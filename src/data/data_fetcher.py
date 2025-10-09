import akshare as ak
import pandas as pd
import numpy as np
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.a_share_stocks = None
        self.hk_connect_stocks = None

    def get_a_share_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            # 获取A股股票基本信息
            stock_info = ak.stock_info_a_code_name()
            logger.info(f"获取到 {len(stock_info)} 只A股股票")
            return stock_info
        except Exception as e:
            logger.error(f"获取A股列表失败: {e}")
            return pd.DataFrame()

    def get_hk_connect_list(self) -> pd.DataFrame:
        """获取港股通股票列表"""
        try:
            # 获取沪港通和深港通股票列表
            sh_hk_connect = ak.tool_trade_date_hist_sina()  # 替换为实际的港股通接口
            # 这里需要根据实际的akshare接口调整
            hk_connect = ak.stock_hk_ggt_top10()  # 港股通十大成交股
            logger.info(f"获取到港股通相关数据")
            return hk_connect
        except Exception as e:
            logger.error(f"获取港股通列表失败: {e}")
            return pd.DataFrame()

    def get_stock_realtime_data(self, stock_code: str) -> Dict:
        """获取股票实时数据"""
        try:
            # 首先尝试获取实时数据
            try:
                data = ak.stock_zh_a_spot_em()
                stock_data = data[data['代码'] == stock_code]

                if not stock_data.empty:
                    return {
                        'code': stock_code,
                        'name': stock_data.iloc[0]['名称'],
                        'price': stock_data.iloc[0]['最新价'],
                        'change_pct': stock_data.iloc[0]['涨跌幅'],
                        'pe_ratio': stock_data.iloc[0].get('市盈率-动态', 0),
                        'volume': stock_data.iloc[0]['成交量'],
                        'turnover': stock_data.iloc[0]['成交额']
                    }
            except Exception as real_time_error:
                logger.warning(f"实时数据获取失败，尝试使用历史数据: {real_time_error}")

            # 如果实时数据失败，使用最新历史数据
            hist_data = self.get_stock_historical_data(stock_code, 10)
            if not hist_data.empty:
                latest = hist_data.iloc[-1]
                prev = hist_data.iloc[-2] if len(hist_data) > 1 else hist_data.iloc[-1]

                change_pct = ((latest['close'] - prev['close']) / prev['close'] * 100) if len(hist_data) > 1 else 0

                return {
                    'code': stock_code,
                    'name': f'股票{stock_code}',  # 临时名称
                    'price': latest['close'],
                    'change_pct': change_pct,
                    'pe_ratio': 0,  # 历史数据中无PE信息
                    'volume': latest['volume'],
                    'turnover': latest['turnover'],
                    'date': latest['date'].strftime('%Y-%m-%d') if pd.notna(latest['date']) else '未知'
                }

            return {}

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 数据失败: {e}")
            return {}

    def get_stock_historical_data(self, stock_code: str, days: int = 30) -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            # 获取历史K线数据
            data = ak.stock_zh_a_hist(symbol=stock_code, period="daily",
                                    start_date=start_date, end_date=end_date)

            if data.empty:
                return pd.DataFrame()

            # 检查列数并重命名
            if len(data.columns) >= 6:
                # 至少保证基本的OHLCV数据
                if len(data.columns) == 11:
                    data.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'turnover', 'amplitude', 'change_pct', 'change_amount', 'turnover_rate']
                elif len(data.columns) >= 6:
                    # 使用原始列名，只重命名前6列
                    new_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
                    for i in range(6, len(data.columns)):
                        new_columns.append(f'col_{i}')
                    data.columns = new_columns

                data['date'] = pd.to_datetime(data['date'])
            else:
                logger.error(f"历史数据列数不足: {len(data.columns)}")
                return pd.DataFrame()

            return data
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
            return pd.DataFrame()

    def calculate_momentum(self, price_data: pd.DataFrame, days: int = 20) -> float:
        """计算股票动量指标"""
        if len(price_data) < days:
            return 0

        try:
            recent_prices = price_data['close'].tail(days)
            # 计算价格动量 (最新价格 / days天前价格 - 1) * 100
            momentum = (recent_prices.iloc[-1] / recent_prices.iloc[0] - 1) * 100
            return momentum
        except Exception as e:
            logger.error(f"计算动量指标失败: {e}")
            return 0

    def get_market_overview(self) -> Dict:
        """获取市场概况"""
        try:
            # 首先尝试获取实时市场数据
            try:
                market_data = ak.stock_zh_a_spot_em()

                if not market_data.empty:
                    total_stocks = len(market_data)
                    rising_stocks = len(market_data[market_data['涨跌幅'] > 0])
                    falling_stocks = len(market_data[market_data['涨跌幅'] < 0])

                    overview = {
                        'total_stocks': total_stocks,
                        'rising_stocks': rising_stocks,
                        'falling_stocks': falling_stocks,
                        'rising_ratio': rising_stocks / total_stocks * 100,
                        'avg_change_pct': market_data['涨跌幅'].mean(),
                        'update_time': datetime.now(),
                        'data_source': '实时数据'
                    }

                    return overview

            except Exception as real_time_error:
                logger.warning(f"实时市场数据获取失败，使用模拟数据: {real_time_error}")

            # 如果实时数据失败，返回基于历史的模拟概况
            stock_list = self.get_a_share_list()
            if not stock_list.empty:
                total_stocks = len(stock_list)

                # 由于获取不到实时数据，使用模拟的市场统计
                overview = {
                    'total_stocks': total_stocks,
                    'rising_stocks': int(total_stocks * 0.45),  # 模拟45%上涨
                    'falling_stocks': int(total_stocks * 0.35), # 模拟35%下跌
                    'rising_ratio': 45.0,
                    'avg_change_pct': 0.2,  # 模拟平均涨跌幅
                    'update_time': datetime.now(),
                    'data_source': '模拟数据(节假日或网络问题)',
                    'note': '由于股市休市或网络问题，显示模拟市场数据'
                }

                return overview

            # 最后的兜底数据
            return {
                'total_stocks': 5000,
                'rising_stocks': 2250,
                'falling_stocks': 1750,
                'rising_ratio': 45.0,
                'avg_change_pct': 0.2,
                'update_time': datetime.now(),
                'data_source': '兜底数据',
                'note': '无法获取实际市场数据'
            }

        except Exception as e:
            logger.error(f"获取市场概况失败: {e}")
            return {
                'total_stocks': 5000,
                'rising_stocks': 2250,
                'falling_stocks': 1750,
                'rising_ratio': 45.0,
                'avg_change_pct': 0.2,
                'update_time': datetime.now(),
                'data_source': '错误兜底',
                'error': str(e)
            }

    def batch_get_stock_data(self, stock_codes: List[str]) -> List[Dict]:
        """批量获取股票数据"""
        results = []
        for code in stock_codes:
            try:
                # 获取实时数据
                realtime_data = self.get_stock_realtime_data(code)
                if not realtime_data:
                    continue

                # 获取历史数据用于计算动量
                historical_data = self.get_stock_historical_data(code, 30)
                if not historical_data.empty:
                    momentum = self.calculate_momentum(historical_data, 20)
                    realtime_data['momentum_20d'] = momentum

                results.append(realtime_data)

                # 避免请求过于频繁
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"批量获取股票 {code} 数据失败: {e}")
                continue

        return results