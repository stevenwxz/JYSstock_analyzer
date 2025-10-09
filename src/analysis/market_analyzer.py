import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter
from config.config import STOCK_FILTER_CONFIG, DATA_CONFIG

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        self.stock_filter = StockFilter()
        self.analysis_results = {}

    def run_daily_analysis(self) -> Dict:
        """执行每日盘后分析"""
        logger.info("开始执行盘后分析...")

        try:
            # 1. 获取沪深300成分股列表（优质股票）
            import akshare as ak
            csi300_stocks = ak.index_stock_cons(symbol="000300")
            if csi300_stocks.empty:
                logger.error("无法获取沪深300成分股列表")
                return {}

            # 提取股票代码
            a_share_list = pd.DataFrame({
                'code': csi300_stocks['品种代码'].tolist(),
                'name': csi300_stocks['品种名称'].tolist()
            })

            logger.info(f"开始分析沪深300成分股，共 {len(a_share_list)} 只")

            # 3. 批量获取股票数据（分批处理以避免请求过多）
            batch_size = 100
            all_stock_data = []

            for i in range(0, len(a_share_list), batch_size):
                batch = a_share_list.iloc[i:i+batch_size]['code'].tolist()
                logger.info(f"处理第 {i//batch_size + 1} 批股票，共 {len(batch)} 只")

                batch_data = self.data_fetcher.batch_get_stock_data(batch)
                all_stock_data.extend(batch_data)

            logger.info(f"成功获取 {len(all_stock_data)} 只股票的数据")

            # 4. 筛选股票
            selected_stocks = self.stock_filter.select_top_stocks(all_stock_data)

            # 5. 获取市场概况
            market_overview = self.data_fetcher.get_market_overview()

            # 6. 生成分析结果
            analysis_result = {
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'analysis_time': datetime.now().strftime('%H:%M:%S'),
                'market_overview': market_overview,
                'selected_stocks': selected_stocks,
                'total_analyzed': len(all_stock_data),
                'selection_criteria': STOCK_FILTER_CONFIG,
                'summary': self._generate_analysis_summary(selected_stocks, market_overview)
            }

            # 7. 保存分析结果
            self._save_analysis_result(analysis_result)

            logger.info("盘后分析完成")
            return analysis_result

        except Exception as e:
            logger.error(f"盘后分析失败: {e}")
            return {}

    def _generate_analysis_summary(self, selected_stocks: List[Dict], market_overview: Dict) -> Dict:
        """生成分析摘要"""
        try:
            summary = {
                'market_sentiment': self._analyze_market_sentiment(market_overview),
                'stock_recommendations': [],
                'risk_warnings': [],
                'key_metrics': {}
            }

            # 分析选中的股票
            for stock in selected_stocks:
                recommendation = {
                    'rank': stock.get('rank', 0),
                    'code': stock.get('code', ''),
                    'name': stock.get('name', ''),
                    'current_price': stock.get('price', 0),
                    'change_pct': stock.get('change_pct', 0),
                    'pe_ratio': stock.get('pe_ratio', 0),
                    'momentum_20d': stock.get('momentum_20d', 0),
                    'strength_score': stock.get('strength_score', 0),
                    'reason': stock.get('selection_reason', '')
                }
                summary['stock_recommendations'].append(recommendation)

            # 关键指标
            if selected_stocks:
                prices = [s.get('price', 0) for s in selected_stocks]
                pe_ratios = [s.get('pe_ratio', 0) for s in selected_stocks if s.get('pe_ratio', 0) > 0]
                momentums = [s.get('momentum_20d', 0) for s in selected_stocks]

                summary['key_metrics'] = {
                    'avg_price': np.mean(prices),
                    'avg_pe_ratio': np.mean(pe_ratios) if pe_ratios else 0,
                    'avg_momentum': np.mean(momentums),
                    'price_range': f"{min(prices):.2f} - {max(prices):.2f}",
                    'pe_range': f"{min(pe_ratios):.2f} - {max(pe_ratios):.2f}" if pe_ratios else "N/A"
                }

            # 风险提示
            if market_overview.get('rising_ratio', 0) < 30:
                summary['risk_warnings'].append("市场整体表现较弱，注意控制仓位")

            if any(s.get('pe_ratio', 0) > 25 for s in selected_stocks):
                summary['risk_warnings'].append("部分推荐股票PE较高，注意估值风险")

            return summary

        except Exception as e:
            logger.error(f"生成分析摘要失败: {e}")
            return {}

    def _analyze_market_sentiment(self, market_overview: Dict) -> str:
        """分析市场情绪"""
        try:
            rising_ratio = market_overview.get('rising_ratio', 0)
            avg_change = market_overview.get('avg_change_pct', 0)

            if rising_ratio > 70 and avg_change > 1:
                return "强势上涨"
            elif rising_ratio > 60 and avg_change > 0.5:
                return "偏强震荡"
            elif rising_ratio > 40:
                return "震荡整理"
            elif rising_ratio > 30:
                return "偏弱调整"
            else:
                return "弱势下跌"

        except Exception as e:
            logger.error(f"分析市场情绪失败: {e}")
            return "未知"

    def _save_analysis_result(self, result: Dict) -> bool:
        """保存分析结果"""
        try:
            # 确保目录存在
            os.makedirs('./logs', exist_ok=True)

            # 保存到文件
            filename = f"./logs/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"分析结果已保存到: {filename}")
            return True

        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return False

    def get_latest_analysis(self) -> Optional[Dict]:
        """获取最新的分析结果"""
        try:
            log_dir = './logs'
            if not os.path.exists(log_dir):
                return None

            # 查找最新的分析文件
            analysis_files = [f for f in os.listdir(log_dir) if f.startswith('analysis_') and f.endswith('.json')]
            if not analysis_files:
                return None

            latest_file = max(analysis_files)
            filepath = os.path.join(log_dir, latest_file)

            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)

            return result

        except Exception as e:
            logger.error(f"获取最新分析结果失败: {e}")
            return None

    def generate_performance_report(self, days: int = 7) -> Dict:
        """生成表现报告"""
        try:
            # 这里可以实现回测功能，分析过去推荐股票的表现
            # 简化实现，返回基本统计
            latest_analysis = self.get_latest_analysis()
            if not latest_analysis:
                return {}

            selected_stocks = latest_analysis.get('selected_stocks', [])
            current_data = []

            # 获取当前价格
            for stock in selected_stocks:
                current_stock_data = self.data_fetcher.get_stock_realtime_data(stock['code'])
                if current_stock_data:
                    current_data.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'original_price': stock['price'],
                        'current_price': current_stock_data['price'],
                        'performance': (current_stock_data['price'] / stock['price'] - 1) * 100
                    })

            report = {
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'analysis_date': latest_analysis.get('analysis_date'),
                'stock_performance': current_data,
                'summary': {
                    'total_stocks': len(current_data),
                    'avg_performance': np.mean([s['performance'] for s in current_data]) if current_data else 0,
                    'best_performer': max(current_data, key=lambda x: x['performance']) if current_data else None,
                    'worst_performer': min(current_data, key=lambda x: x['performance']) if current_data else None
                }
            }

            return report

        except Exception as e:
            logger.error(f"生成表现报告失败: {e}")
            return {}