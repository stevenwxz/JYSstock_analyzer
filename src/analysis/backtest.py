import akshare as ak
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter

logger = logging.getLogger(__name__)

class BacktestAnalyzer:
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        self.stock_filter = StockFilter()

    def get_historical_data_for_date(self, stock_code: str, target_date: str) -> Dict:
        """获取特定日期的股票数据"""
        try:
            # 获取目标日期前后的数据
            end_date = (datetime.strptime(target_date, '%Y-%m-%d') + timedelta(days=5)).strftime('%Y%m%d')
            start_date = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y%m%d')

            hist_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily",
                                         start_date=start_date, end_date=end_date)

            if hist_data.empty:
                return {}

            # 查找目标日期的数据
            target_date_formatted = datetime.strptime(target_date, '%Y-%m-%d').strftime('%Y-%m-%d')

            # 将日期列转换为字符串格式进行比较
            hist_data['日期'] = pd.to_datetime(hist_data['日期']).dt.strftime('%Y-%m-%d')
            target_data = hist_data[hist_data['日期'] == target_date_formatted]

            if target_data.empty:
                # 如果没有找到确切日期，使用最接近的前一个交易日
                hist_data['日期'] = pd.to_datetime(hist_data['日期'])
                valid_data = hist_data[hist_data['日期'] <= datetime.strptime(target_date, '%Y-%m-%d')]
                if not valid_data.empty:
                    target_data = valid_data.tail(1)
                else:
                    return {}

            if not target_data.empty:
                row = target_data.iloc[0]

                # 计算动量（过去20天）
                momentum = 0
                if len(hist_data) >= 21:
                    current_price = row['收盘'] if '收盘' in target_data.columns else row.iloc[4]
                    past_price = hist_data.iloc[-21]['收盘'] if '收盘' in hist_data.columns else hist_data.iloc[-21].iloc[4]
                    momentum = (current_price / past_price - 1) * 100

                return {
                    'code': stock_code,
                    'name': f'股票{stock_code}',
                    'date': target_date,
                    'price': row['收盘'] if '收盘' in target_data.columns else row.iloc[4],
                    'volume': row['成交量'] if '成交量' in target_data.columns else row.iloc[5],
                    'change_pct': row['涨跌幅'] if '涨跌幅' in target_data.columns else 0,
                    'momentum_20d': momentum,
                    'pe_ratio': 15.0,  # 使用估算值
                    'turnover': row['成交额'] if '成交额' in target_data.columns else row.iloc[6] if len(row) > 6 else 0
                }

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 在 {target_date} 的数据失败: {e}")

        return {}

    def simulate_analysis_for_date(self, analysis_date: str, stock_list: List[str] = None) -> Dict:
        """模拟特定日期的分析"""
        try:
            logger.info(f"模拟 {analysis_date} 的分析...")

            # 如果没有提供股票列表，使用一些常见股票
            if stock_list is None:
                stock_list = [
                    '000001', '000002', '000858', '000725', '002714',
                    '600036', '600519', '600887', '600276', '600009',
                    '300059', '002415', '002507', '000596', '002241',
                    '600031', '000063', '600048', '002304', '600104'
                ]

            # 获取所有股票的数据
            stock_data = []
            for code in stock_list:
                data = self.get_historical_data_for_date(code, analysis_date)
                if data:
                    # 计算基本面数据（模拟）
                    # 注意：在真实回测中，这些数据需要从历史数据中获取
                    data['roe'] = 12.0 + np.random.uniform(-3, 3)  # 随机ROE
                    data['profit_growth'] = 15.0 + np.random.uniform(-5, 5)  # 随机利润增长率
                    data['dividend_yield'] = 2.0 + np.random.uniform(-1, 2)  # 随机股息率
                    data['turnover_rate'] = 1.5 + np.random.uniform(-1, 2)  # 随机换手率
                    data['pb_ratio'] = 1.5 + np.random.uniform(-0.5, 1.0)  # 随机PB
                    data['peg'] = 0.8 + np.random.uniform(-0.3, 0.5)  # 随机PEG
                    
                    stock_data.append(data)
                    logger.info(f"获取到 {code} 的数据: ¥{data['price']:.2f}")

            logger.info(f"成功获取 {len(stock_data)} 只股票的 {analysis_date} 数据")

            if not stock_data:
                return {}

            # 应用筛选算法
            selected_stocks = self.stock_filter.select_top_stocks(stock_data)

            # 构建分析结果
            analysis_result = {
                'analysis_date': analysis_date,
                'total_analyzed': len(stock_data),
                'selected_stocks': selected_stocks,
                'market_overview': {
                    'total_stocks': len(stock_data),
                    'avg_change_pct': np.mean([s['change_pct'] for s in stock_data]),
                    'data_source': f'历史回测数据-{analysis_date}'
                }
            }

            return analysis_result

        except Exception as e:
            logger.error(f"模拟 {analysis_date} 分析失败: {e}")
            return {}

    def calculate_performance(self, recommendations: List[Dict], next_date: str) -> Dict:
        """计算推荐股票在下一交易日的表现"""
        try:
            logger.info(f"计算推荐股票在 {next_date} 的表现...")

            performance_results = []
            total_return = 0

            for stock in recommendations:
                code = stock['code']
                original_price = stock['price']

                # 获取下一日的数据
                next_data = self.get_historical_data_for_date(code, next_date)

                if next_data:
                    next_price = next_data['price']
                    return_pct = (next_price / original_price - 1) * 100

                    performance_results.append({
                        'rank': stock['rank'],
                        'code': code,
                        'name': stock['name'],
                        'original_price': original_price,
                        'next_price': next_price,
                        'return_pct': return_pct,
                        'original_reason': stock.get('selection_reason', ''),
                        'strength_score': stock.get('strength_score', 0)
                    })

                    total_return += return_pct

                    logger.info(f"{code}: ¥{original_price:.2f} -> ¥{next_price:.2f} ({return_pct:+.2f}%)")

            # 计算统计数据
            if performance_results:
                returns = [r['return_pct'] for r in performance_results]
                avg_return = np.mean(returns)
                max_return = max(returns)
                min_return = min(returns)
                positive_count = len([r for r in returns if r > 0])

                summary = {
                    'total_stocks': len(performance_results),
                    'avg_return': avg_return,
                    'total_return': total_return,
                    'max_return': max_return,
                    'min_return': min_return,
                    'positive_count': positive_count,
                    'success_rate': positive_count / len(performance_results) * 100,
                    'best_performer': max(performance_results, key=lambda x: x['return_pct']),
                    'worst_performer': min(performance_results, key=lambda x: x['return_pct'])
                }
            else:
                summary = {}

            return {
                'performance_date': next_date,
                'stock_performance': performance_results,
                'summary': summary
            }

        except Exception as e:
            logger.error(f"计算表现失败: {e}")
            return {}

    def run_backtest(self, analysis_date: str, next_date: str) -> Dict:
        """运行完整的回测"""
        try:
            logger.info(f"开始回测: {analysis_date} -> {next_date}")

            # 1. 模拟分析日的选股
            analysis_result = self.simulate_analysis_for_date(analysis_date)

            if not analysis_result or not analysis_result.get('selected_stocks'):
                logger.error("模拟分析失败或无推荐股票")
                return {}

            # 2. 计算次日表现
            performance_result = self.calculate_performance(
                analysis_result['selected_stocks'],
                next_date
            )

            # 3. 生成完整报告
            backtest_report = {
                'backtest_info': {
                    'analysis_date': analysis_date,
                    'performance_date': next_date,
                    'backtest_run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'original_analysis': analysis_result,
                'performance_analysis': performance_result,
                'conclusion': self._generate_conclusion(analysis_result, performance_result)
            }

            return backtest_report

        except Exception as e:
            logger.error(f"回测失败: {e}")
            return {}

    def _generate_conclusion(self, analysis: Dict, performance: Dict) -> Dict:
        """生成回测结论"""
        try:
            if not performance.get('summary'):
                return {'status': 'failed', 'message': '无法获取表现数据'}

            summary = performance['summary']

            conclusion = {
                'overall_performance': '优秀' if summary['avg_return'] > 2 else '良好' if summary['avg_return'] > 0 else '需改进',
                'success_rate': f"{summary['success_rate']:.1f}%",
                'average_return': f"{summary['avg_return']:+.2f}%",
                'best_pick': f"{summary['best_performer']['name']} ({summary['best_performer']['return_pct']:+.2f}%)",
                'strategy_effectiveness': '有效' if summary['avg_return'] > 0 and summary['success_rate'] > 50 else '需优化',
                'key_insights': [
                    f"推荐的{summary['total_stocks']}只股票中，{summary['positive_count']}只上涨",
                    f"平均收益率为{summary['avg_return']:+.2f}%",
                    f"最佳推荐股票收益率达{summary['max_return']:+.2f}%",
                    f"策略成功率为{summary['success_rate']:.1f}%"
                ]
            }

            return conclusion

        except Exception as e:
            logger.error(f"生成结论失败: {e}")
            return {'status': 'error', 'message': str(e)}