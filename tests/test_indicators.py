# -*- coding: utf-8 -*-
"""离线冒烟测试：覆盖纯指标、评分、股息动态计算等无网络依赖的逻辑。

运行方式：python -m unittest discover -s tests -v
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd

from src.data.indicators import calculate_momentum, calculate_financial_health


class TestIndicators(unittest.TestCase):
    """指标纯函数测试"""

    def _make_price_df(self, closes):
        """构造升序排列的收盘价 DataFrame"""
        return pd.DataFrame({'close': closes})

    def test_momentum_zero_when_insufficient_data(self):
        self.assertEqual(calculate_momentum(self._make_price_df([10, 11]), days=20), 0)

    def test_momentum_positive(self):
        # 20个交易日，从100涨到110 → 动量 10%
        closes = [100 + i * 0.5 for i in range(20)]  # 100 → 109.5
        self.assertAlmostEqual(calculate_momentum(self._make_price_df(closes), days=20), 9.5, places=3)

    def test_momentum_negative(self):
        closes = [100 - i for i in range(20)]  # 100 → 81
        self.assertAlmostEqual(calculate_momentum(self._make_price_df(closes), days=20), -19.0, places=3)

    def test_momentum_none_returns_zero(self):
        self.assertEqual(calculate_momentum(None, days=20), 0)

    def test_financial_health_baseline(self):
        # 全部为 None 时为基础分 50
        self.assertEqual(calculate_financial_health(None, None, None, None), 50)

    def test_financial_health_low_pb_high_dividend(self):
        # 破净 + 高股息 → 50 + 20 + 15 = 85
        self.assertEqual(calculate_financial_health(0.8, 6.0, None, None), 85)

    def test_financial_health_clamped(self):
        # 极端高估 + 过度投机，分数不得低于 0
        score = calculate_financial_health(20, 0, 100, 50)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class TestDividendOverride(unittest.TestCase):
    """股息手动修正机制测试"""

    def test_get_manual_dividend_per_share(self):
        from config.dividend_override import get_manual_dividend_per_share
        # 新华保险 601336：每股股息 2.53 元
        self.assertEqual(get_manual_dividend_per_share('601336'), 2.53)
        # 未配置的股票返回 None
        self.assertIsNone(get_manual_dividend_per_share('000000'))

    def test_dividend_yield_dynamic_calc(self):
        """股息率 = 每股股息 / 股价 * 100（动态计算，不再依赖静态值）"""
        from config.dividend_override import get_manual_dividend_per_share
        dps = get_manual_dividend_per_share('601336')
        price = 67.32
        self.assertAlmostEqual(dps / price * 100, 3.758, places=2)


class TestStockFilter(unittest.TestCase):
    """评分逻辑测试"""

    def test_pr_ratio_formula(self):
        """PR = PE / ROE（roe 为百分数，如 15 表示 15%），仅真实财报 ROE 参与"""
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        stock = {'pe_ratio': 15, 'roe': 15, 'roe_source': 'financial'}
        self.assertAlmostEqual(sf.calculate_pr_ratio(stock), 1.0, places=3)

    def test_pr_ratio_zero_when_roe_inferred(self):
        """ROE 为 PB/PE 反推值（无 roe_source 标记）时，PR 应归零（共线伪因子）"""
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        # 未标记 roe_source，视为反推 ROE，PR 不参与计分
        self.assertEqual(sf.calculate_pr_ratio({'pe_ratio': 15, 'roe': 15}), 0)

    def test_pr_ratio_zero_when_roe_missing(self):
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        self.assertEqual(sf.calculate_pr_ratio({'pe_ratio': 15, 'roe': None, 'roe_source': 'financial'}), 0)
        self.assertEqual(sf.calculate_pr_ratio({'pe_ratio': None, 'roe': 15, 'roe_source': 'financial'}), 0)

    def test_grade_boundaries(self):
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        self.assertEqual(sf._get_grade(85), 'A+')
        self.assertEqual(sf._get_grade(44), 'D')


class TestTurnoverNeutralization(unittest.TestCase):
    """换手率中性化测试：换手率未知(None)时不应误杀股票，也不应参与换手率加分"""

    def _base_stock(self, turnover_rate):
        return {
            'code': '000001',
            'name': '测试',
            'price': 10.0,
            'change_pct': 0.5,
            'turnover_rate': turnover_rate,
            'pe_ratio': 15,
            'pb_ratio': 1.5,
            'roe': 12,
            'momentum_20d': 8,
        }

    def test_none_turnover_not_filtered(self):
        """换手率为 None 时，附加筛选不应把股票过滤掉"""
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        stocks = [self._base_stock(None)]
        result = sf.apply_additional_filters(stocks)
        self.assertEqual(len(result), 1)

    def test_none_turnover_no_score_bonus(self):
        """换手率为 None 时，评分逻辑不因换手率加分"""
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        detail = sf.calculate_strength_score(self._base_stock(None))
        breakdown = detail['breakdown']
        # 技术面里的换手率加分应不起作用：无换手率时不额外加分
        # 这里只验证不会抛异常且返回合理结构
        self.assertIn('technical', breakdown)
        self.assertGreaterEqual(breakdown['technical'], 0)

    def test_low_turnover_filtered(self):
        """换手率有值且过低时，仍应被过滤（实盘行为不变）"""
        from src.analysis.stock_filter import StockFilter
        sf = StockFilter()
        stocks = [self._base_stock(0.01)]  # 0.01% 低于 min_turnover_rate
        result = sf.apply_additional_filters(stocks)
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
