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

    def calculate_strength_score(self, stock_data: Dict) -> float:
        """计算股票强势分数"""
        score = 0

        try:
            # 1. 涨跌幅得分 (30%)
            change_pct = stock_data.get('change_pct', 0)
            if change_pct > 5:
                score += 30
            elif change_pct > 2:
                score += 20
            elif change_pct > 0:
                score += 10
            elif change_pct > -2:
                score += 5

            # 2. 动量得分 (40%)
            momentum = stock_data.get('momentum_20d', 0)
            if momentum > 15:
                score += 40
            elif momentum > 10:
                score += 30
            elif momentum > 5:
                score += 20
            elif momentum > 0:
                score += 10

            # 3. 成交额得分 (20%) - 更准确反映流动性
            turnover = stock_data.get('turnover', 0)
            min_turnover = self.config.get('min_turnover', self.config.get('min_volume', 0) * 10)  # 兼容旧配置
            if turnover > min_turnover * 3:
                score += 20
            elif turnover > min_turnover * 2:
                score += 15
            elif turnover > min_turnover:
                score += 10

            # 4. 价格位置得分 (10%)
            price = stock_data.get('price', 0)
            if price > self.config['min_price']:
                score += 10

        except Exception as e:
            logger.error(f"计算强势分数失败: {e}")
            return 0

        return score

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
                stock['strength_score'] = self.calculate_strength_score(stock)

            # 按强势分数排序，选择前N只
            sorted_stocks = sorted(stocks_data,
                                 key=lambda x: x['strength_score'],
                                 reverse=True)

            # 根据配置的最小强势分数筛选
            min_score = self.config.get('min_strength_score', 50)
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
                turnover = stock.get('turnover', 0)
                change_pct = stock.get('change_pct', 0)

                # 排除停牌股票（涨跌幅为0且成交额很小）
                if change_pct == 0 and turnover < 100:  # 100万元（API返回单位为万元）
                    continue

                # 排除价格过低的股票
                if price < self.config['min_price']:
                    continue

                # 排除成交额过小的股票（优先使用成交额）
                min_turnover = self.config.get('min_turnover', self.config.get('min_volume', 0) * 10)
                if turnover < min_turnover:
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
        """选择最终的推荐股票"""
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

            # 4. 选择前N只股票
            final_selection = strength_filtered[:self.config['max_stocks']]

            # 5. 添加选择理由
            for i, stock in enumerate(final_selection):
                stock['rank'] = i + 1
                stock['selection_reason'] = self._generate_selection_reason(stock)

            logger.info(f"最终选择 {len(final_selection)} 只股票")
            return final_selection

        except Exception as e:
            logger.error(f"股票选择失败: {e}")
            return []

    def _generate_selection_reason(self, stock: Dict) -> str:
        """生成选择理由"""
        reasons = []

        pe_ratio = stock.get('pe_ratio', 0)
        change_pct = stock.get('change_pct', 0)
        momentum = stock.get('momentum_20d', 0)
        strength_score = stock.get('strength_score', 0)

        reasons.append(f"PE={pe_ratio:.2f}")

        if change_pct > 3:
            reasons.append("当日强势上涨")
        elif change_pct > 0:
            reasons.append("当日上涨")

        if momentum > 10:
            reasons.append("20日动量强劲")
        elif momentum > 0:
            reasons.append("20日动量向上")

        reasons.append(f"强势分数={strength_score:.1f}")

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