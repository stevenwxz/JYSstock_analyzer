import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from config.config import STOCK_FILTER_CONFIG

logger = logging.getLogger(__name__)

class StockFilter:
    def __init__(self, config: Dict = None):
        self.config = config or STOCK_FILTER_CONFIG

    def calculate_pr_ratio(self, stock_data: Dict) -> float:
        """计算市赚率PR = PE / (100 * ROE)"""
        try:
            pe = stock_data.get('pe_ratio', 0)
            roe = stock_data.get('roe', 0)

            if pe and roe and pe > 0 and roe > 0:
                pr = pe / (100 * roe)
                return round(pr, 3)
            return 0
        except Exception as e:
            logger.error(f"计算市赚率PR失败: {e}")
            return 0

    def calculate_strength_score(self, stock_data: Dict) -> Dict:
        """计算股票强势分数"""
        score_breakdown = {
            'technical': 0,    # 技术面 (30分): 动量25 + 换手率5
            'valuation': 0,    # 估值 (25分): PE10 + PB5 + PR10
            'profitability': 0,  # 盈利质量 (30分): ROE15 + 利润增长15
            'safety': 0,       # 安全性 (10分): PB安全边际5 + 低换手率5
            'dividend': 0      # 分红 (5分): 股息率
        }

        try:
            # ===== 1. 技术面得分 (30分) =====
            # 1.1 20日动量 (25分)
            momentum = stock_data.get('momentum_20d', 0)
            if momentum > 15:
                score_breakdown['technical'] += 25
            elif momentum > 10:
                score_breakdown['technical'] += 20
            elif momentum > 5:
                score_breakdown['technical'] += 14
            elif momentum > 0:
                score_breakdown['technical'] += 8
            elif momentum > -5:
                score_breakdown['technical'] += 3

            # 1.2 流动性-换手率 (5分)
            turnover_rate = stock_data.get('turnover_rate', 0)
            if turnover_rate and 1 <= turnover_rate < 3:
                score_breakdown['technical'] += 5
            elif turnover_rate and 3 <= turnover_rate < 5:
                score_breakdown['technical'] += 4
            elif turnover_rate and 5 <= turnover_rate < 8:
                score_breakdown['technical'] += 3
            elif turnover_rate and 0.5 <= turnover_rate < 1:
                score_breakdown['technical'] += 2

            # ===== 2. 估值得分 (20分) =====
            # 2.1 PE估值 (10分)
            pe = stock_data.get('pe_ratio', 0)
            if pe and 0 < pe < 10:
                score_breakdown['valuation'] += 10
            elif pe and 10 <= pe < 20:
                score_breakdown['valuation'] += 7
            elif pe and 20 <= pe < 30:
                score_breakdown['valuation'] += 4

            # 2.2 PB估值 (5分)
            pb = stock_data.get('pb_ratio', 0)
            if pb and 0 < pb < 2:
                score_breakdown['valuation'] += 5
            elif pb and 2 <= pb < 4:
                score_breakdown['valuation'] += 4
            elif pb and 4 <= pb < 7:
                score_breakdown['valuation'] += 2

            # 2.3 PR市赚率 (10分)
            pr = self.calculate_pr_ratio(stock_data)
            if pr and 0 < pr < 0.8:
                score_breakdown['valuation'] += 10
            elif pr and 0.8 <= pr < 1:
                score_breakdown['valuation'] += 7
            elif pr and 1 <= pr < 1.2:
                score_breakdown['valuation'] += 3

            # ===== 3. 盈利质量得分 (30分) =====
            # 3.1 ROE (15分)
            roe = stock_data.get('roe', 0)
            if roe and roe > 20:
                score_breakdown['profitability'] += 15
            elif roe and roe > 15:
                score_breakdown['profitability'] += 12
            elif roe and roe > 10:
                score_breakdown['profitability'] += 8
            elif roe and roe > 5:
                score_breakdown['profitability'] += 4

            # 3.2 净利润增长率 (15分)
            profit_growth = stock_data.get('profit_growth', 0)
            if profit_growth and profit_growth > 30:
                score_breakdown['profitability'] += 15
            elif profit_growth and profit_growth > 20:
                score_breakdown['profitability'] += 12
            elif profit_growth and profit_growth > 10:
                score_breakdown['profitability'] += 8
            elif profit_growth and profit_growth > 0:
                score_breakdown['profitability'] += 4

            # ===== 4. 安全性得分 (10分) =====
            # 4.1 PB安全边际 (5分)
            pb = stock_data.get('pb_ratio', 0)
            if pb and 0 < pb < 1.0:
                score_breakdown['safety'] += 5
            elif pb and 1.0 <= pb < 1.5:
                score_breakdown['safety'] += 4
            elif pb and 1.5 <= pb < 2.5:
                score_breakdown['safety'] += 2

            # 4.2 低换手率-筹码稳定 (5分)
            turnover_rate = stock_data.get('turnover_rate', 0)
            if turnover_rate and 0 < turnover_rate < 2:
                score_breakdown['safety'] += 5
            elif turnover_rate and 2 <= turnover_rate < 5:
                score_breakdown['safety'] += 3
            elif turnover_rate and 5 <= turnover_rate < 10:
                score_breakdown['safety'] += 1

            # ===== 5. 分红得分 (5分) =====
            dividend_yield = stock_data.get('dividend_yield', 0)
            if dividend_yield and dividend_yield > 5:
                score_breakdown['dividend'] += 5
            elif dividend_yield and dividend_yield > 3:
                score_breakdown['dividend'] += 4
            elif dividend_yield and dividend_yield > 2:
                score_breakdown['dividend'] += 3
            elif dividend_yield and dividend_yield > 1:
                score_breakdown['dividend'] += 2
            elif dividend_yield and dividend_yield > 0.5:
                score_breakdown['dividend'] += 1

        except Exception as e:
            logger.error(f"计算强势分数失败: {e}")
            return {'total': 0, 'breakdown': score_breakdown, 'grade': 'D'}

        total_score = sum(score_breakdown.values())
        grade = self._get_grade(total_score)

        return {
            'total': total_score,
            'breakdown': score_breakdown,
            'grade': grade
        }

    def _get_grade(self, score: float) -> str:
        """根据分数获取评级"""
        if score >= 85:
            return 'A+'
        elif score >= 75:
            return 'A'
        elif score >= 65:
            return 'B+'
        elif score >= 55:
            return 'B'
        elif score >= 45:
            return 'C'
        else:
            return 'D'

    def filter_by_pe_ratio(self, stocks_data: List[Dict]) -> List[Dict]:
        """按市盈率筛选股票"""
        filtered_stocks = []

        for stock in stocks_data:
            try:
                pe_ratio = stock.get('pe_ratio', 0)
                # 修复PE筛选问题：确保PE值是数字类型，如果是None则设为0
                if pe_ratio is None:
                    pe_ratio = 0
                
                # 过滤掉PE为0或负数的股票（可能是亏损股）
                if 0 < pe_ratio <= self.config['max_pe_ratio']:
                    filtered_stocks.append(stock)
            except Exception as e:
                logger.error(f"PE筛选失败 {stock.get('code', 'unknown')}: {e}")
                continue

        logger.info(f"PE筛选后剩余 {len(filtered_stocks)} 只股票")
        return filtered_stocks

    def filter_by_strength(self, stocks_data: List[Dict]) -> List[Dict]:
        """按强势指标筛选股票"""
        try:
            # 计算每只股票的强势分数
            for stock in stocks_data:
                score_result = self.calculate_strength_score(stock)
                stock['strength_score_detail'] = score_result  # 保存详细评分
                stock['strength_score'] = score_result['total']  # 保存总分
                stock['strength_grade'] = score_result['grade']  # 保存评级

            # 按强势分数排序，选择前N只
            sorted_stocks = sorted(stocks_data,
                                 key=lambda x: x['strength_score'],
                                 reverse=True)

            # 根据配置的最小强势分数筛选
            min_score = self.config.get('min_strength_score', 45)  # 降低到45分
            strong_stocks = [stock for stock in sorted_stocks if stock['strength_score'] >= min_score]

            logger.info(f"强势筛选后剩余 {len(strong_stocks)} 只股票")
            return strong_stocks

        except Exception as e:
            logger.error(f"强势筛选失败: {e}")
            return []

    def apply_additional_filters(self, stocks_data: List[Dict]) -> List[Dict]:
        """应用额外的筛选条件"""
        filtered_stocks = []

        for stock in stocks_data:
            try:
                # 过滤条件
                price = stock.get('price', 0)
                turnover_rate = stock.get('turnover_rate', 0)
                change_pct = stock.get('change_pct', 0)

                # 排除停牌股票（涨跌幅为0且换手率很小）
                if change_pct == 0 and (turnover_rate is None or turnover_rate < 0.1):  # 0.1%换手率
                    continue

                # 排除价格过低的股票
                if price < self.config['min_price']:
                    continue

                # 排除换手率过小的股票
                min_turnover_rate = self.config.get('min_turnover_rate', 0.5)  # 默认0.5%
                if turnover_rate is None or turnover_rate < min_turnover_rate:
                    continue

                # 排除跌停股票
                if change_pct <= -9.8:
                    continue

                filtered_stocks.append(stock)

            except Exception as e:
                logger.error(f"附加筛选失败 {stock.get('code', 'unknown')}: {e}")
                continue

        logger.info(f"附加筛选后剩余 {len(filtered_stocks)} 只股票")
        return filtered_stocks

    def select_top_stocks(self, stocks_data: List[Dict]) -> List[Dict]:
        """选择最终的推荐股票 - 直接按分数排序选择，不限制行业"""
        try:
            # 0. 去重（防止输入数据中有重复）
            unique_stocks = {}
            for stock in stocks_data:
                code = stock.get('code')
                if code and code not in unique_stocks:
                    unique_stocks[code] = stock

            stocks_data = list(unique_stocks.values())
            logger.info(f"去重后股票数量: {len(stocks_data)}")

            # 1. 首先按PE筛选
            pe_filtered = self.filter_by_pe_ratio(stocks_data)

            # 2. 应用额外筛选条件
            additional_filtered = self.apply_additional_filters(pe_filtered)

            # 3. 按强势筛选并排序
            strength_filtered = self.filter_by_strength(additional_filtered)

            # 4. 直接按分数排序，不限制行业
            strength_filtered.sort(key=lambda x: x['strength_score'], reverse=True)

            # 5. 选择前N只股票
            final_selection = strength_filtered[:self.config['max_stocks']]

            # 6. 添加选择理由和排名
            for i, stock in enumerate(final_selection):
                stock['rank'] = i + 1
                stock['selection_reason'] = self._generate_selection_reason(stock)

            logger.info(f"最终选择 {len(final_selection)} 只股票 (不限制行业)")
            return final_selection

        except Exception as e:
            logger.error(f"股票选择失败: {e}")
            return []

    def calculate_offensive_score(self, stock_data: Dict) -> Dict:
        """进攻模式评分：取消过热惩罚 + 高动量加分"""
        base_result = self.calculate_strength_score(stock_data)
        base_score = base_result['total']

        momentum = stock_data.get('momentum_20d', 0)
        bonus = 0
        if momentum > 15:
            bonus += 12
        elif momentum > 10:
            bonus += 8
        elif momentum > 5:
            bonus += 4

        growth = stock_data.get('profit_growth')
        if growth and growth > 30:
            bonus += 5

        total = base_score + bonus
        grade = self._get_grade(total)
        return {'total': total, 'breakdown': base_result['breakdown'], 'grade': grade, 'bonus': bonus}

    def calculate_ultra_defensive_score(self, stock_data: Dict) -> Dict:
        """超防守评分：极低波动+低PB+高ROE+小回撤"""
        score = 0
        breakdown = {'low_volatility': 0, 'low_pb': 0, 'high_roe': 0, 'small_drawdown': 0, 'momentum_bonus': 0}

        volatility = stock_data.get('volatility_20d', 0)
        pb = stock_data.get('pb_ratio')
        roe = stock_data.get('roe')
        max_dd = stock_data.get('max_drawdown_20d', 0)
        momentum = stock_data.get('momentum_20d', 0)

        if volatility < 1.0:
            breakdown['low_volatility'] = 30
        elif volatility < 1.5:
            breakdown['low_volatility'] = 25
        elif volatility < 2.0:
            breakdown['low_volatility'] = 18
        elif volatility < 2.5:
            breakdown['low_volatility'] = 10

        if pb and 0 < pb < 0.8:
            breakdown['low_pb'] = 25
        elif pb and 0.8 <= pb < 1.2:
            breakdown['low_pb'] = 20
        elif pb and 1.2 <= pb < 2.0:
            breakdown['low_pb'] = 12
        elif pb and 2.0 <= pb < 3.0:
            breakdown['low_pb'] = 5

        if roe and roe > 15:
            breakdown['high_roe'] = 25
        elif roe and roe > 10:
            breakdown['high_roe'] = 18
        elif roe and roe > 7:
            breakdown['high_roe'] = 10

        if max_dd > -3:
            breakdown['small_drawdown'] = 20
        elif max_dd > -5:
            breakdown['small_drawdown'] = 14
        elif max_dd > -8:
            breakdown['small_drawdown'] = 7

        if 0 < momentum <= 5:
            breakdown['momentum_bonus'] = 5

        score = sum(breakdown.values())
        grade = self._get_grade(score)
        return {'total': score, 'breakdown': breakdown, 'grade': grade}

    def select_top_stocks_offensive(self, stocks_data: List[Dict]) -> List[Dict]:
        """进攻模式选股：PE<30 + 进攻评分 + 取前N"""
        unique_stocks = {}
        for stock in stocks_data:
            code = stock.get('code')
            if code and code not in unique_stocks:
                unique_stocks[code] = stock
        stocks_data = list(unique_stocks.values())

        pe_filtered = self.filter_by_pe_ratio(stocks_data)
        additional_filtered = self.apply_additional_filters(pe_filtered)

        for stock in additional_filtered:
            score_result = self.calculate_offensive_score(stock)
            stock['strength_score_detail'] = score_result
            stock['strength_score'] = score_result['total']
            stock['strength_grade'] = score_result['grade']

        sorted_stocks = sorted(additional_filtered, key=lambda x: x['strength_score'], reverse=True)
        final = sorted_stocks[:self.config['max_stocks']]
        for i, stock in enumerate(final):
            stock['rank'] = i + 1
            stock['selection_reason'] = self._generate_selection_reason(stock)
        logger.info(f"[进攻模式] 选出 {len(final)} 只股票")
        return final

    def select_top_stocks_ultra_defensive(self, stocks_data: List[Dict]) -> List[Dict]:
        """超防守模式选股：PE<30 + 超防守评分 + 取前N"""
        unique_stocks = {}
        for stock in stocks_data:
            code = stock.get('code')
            if code and code not in unique_stocks:
                unique_stocks[code] = stock
        stocks_data = list(unique_stocks.values())

        pe_filtered = self.filter_by_pe_ratio(stocks_data)
        additional_filtered = self.apply_additional_filters(pe_filtered)

        for stock in additional_filtered:
            score_result = self.calculate_ultra_defensive_score(stock)
            stock['strength_score_detail'] = score_result
            stock['strength_score'] = score_result['total']
            stock['strength_grade'] = score_result['grade']

        sorted_stocks = sorted(additional_filtered, key=lambda x: x['strength_score'], reverse=True)
        final = sorted_stocks[:self.config['max_stocks']]
        for i, stock in enumerate(final):
            stock['rank'] = i + 1
            stock['selection_reason'] = self._generate_selection_reason(stock)
        logger.info(f"[超防守模式] 选出 {len(final)} 只股票")
        return final

    def _generate_selection_reason(self, stock: Dict) -> str:
        """生成选择理由 - 包含基本面指标"""
        reasons = []

        # 基本信息
        pe_ratio = stock.get('pe_ratio', 0)
        pb_ratio = stock.get('pb_ratio', 0)
        change_pct = stock.get('change_pct', 0)
        momentum = stock.get('momentum_20d', 0)
        strength_score = stock.get('strength_score', 0)
        strength_grade = stock.get('strength_grade', '')

        # 基本面指标
        roe = stock.get('roe', 0)
        profit_growth = stock.get('profit_growth', 0)
        dividend_yield = stock.get('dividend_yield', 0)
        turnover_rate = stock.get('turnover_rate', 0)

        # 估值
        if pe_ratio:
            reasons.append(f"PE={pe_ratio:.2f}")
        if pb_ratio:
            reasons.append(f"PB={pb_ratio:.2f}")

        # 技术面
        if momentum > 10:
            reasons.append("20日动量强劲")
        elif momentum > 0:
            reasons.append("20日动量向上")

        # 基本面
        if roe and roe > 15:
            reasons.append(f"ROE优秀({roe:.1f}%)")
        elif roe and roe > 10:
            reasons.append(f"ROE良好({roe:.1f}%)")

        if profit_growth and profit_growth > 20:
            reasons.append(f"高成长({profit_growth:.1f}%)")
        elif profit_growth and profit_growth > 10:
            reasons.append(f"成长性好({profit_growth:.1f}%)")

        # 安全性 - 基于新的评分逻辑
        safety_score = stock.get('strength_score_detail', {}).get('breakdown', {}).get('safety', 0)
        if safety_score >= 8:
            reasons.append("安全性高")
        elif safety_score >= 6:
            reasons.append("安全性良好")

        # 综合评分
        reasons.append(f"综合{strength_grade}级({strength_score:.1f}分)")

        return "；".join(reasons)

    def get_filter_summary(self, original_count: int, final_count: int) -> Dict:
        """获取筛选总结"""
        return {
            'original_count': original_count,
            'final_count': final_count,
            'filter_rate': final_count / original_count * 100 if original_count > 0 else 0,
            'filter_config': self.config,
            'timestamp': datetime.now()
        }