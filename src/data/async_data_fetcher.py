import asyncio
import aiohttp
import pandas as pd
import numpy as np
import time
import logging
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
import os
import json

# 添加config路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.dividend_override import get_manual_dividend_yield, has_manual_override

logger = logging.getLogger(__name__)

class AsyncStockDataFetcher:
    """异步股票数据获取器 - 大幅提升性能"""

    def __init__(self, max_concurrent: int = 20):
        """
        初始化异步数据获取器

        Args:
            max_concurrent: 最大并发请求数 (默认20,可以根据网络情况调整)
        """
        self.max_concurrent = max_concurrent
        self.semaphore = None  # 将在异步上下文中初始化
        self.failed_stocks = []
        self._hist_cache = {}  # 历史数据缓存

        # User-Agent池
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]

    def _get_random_user_agent(self) -> str:
        """随机获取User-Agent"""
        return random.choice(self.user_agents)

    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str,
                                max_retries: int = 3, timeout: int = 10) -> Optional[str]:
        """
        带重试的异步HTTP请求

        Args:
            session: aiohttp会话
            url: 请求URL
            max_retries: 最大重试次数
            timeout: 超时时间(秒)

        Returns:
            响应文本或None
        """
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://gu.qq.com/'
        }

        for attempt in range(max_retries):
            try:
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()

                    # 如果状态码不是200,等待后重试
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (2 ** attempt))

            except asyncio.TimeoutError:
                logger.debug(f"请求超时 (尝试 {attempt + 1}/{max_retries}): {url[:80]}...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))
            except Exception as e:
                logger.debug(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        return None

    async def get_stock_realtime_data(self, session: aiohttp.ClientSession,
                                     stock_code: str) -> Dict:
        """异步获取股票实时数据"""
        # 使用信号量控制并发
        async with self.semaphore:
            try:
                # 构造腾讯财经API请求
                if stock_code.startswith('6'):
                    symbol = f"sh{stock_code}"
                else:
                    symbol = f"sz{stock_code}"

                url = f"https://qt.gtimg.cn/q={symbol}"

                content = await self._fetch_with_retry(session, url, max_retries=3, timeout=10)

                if content and 'v_' in content:
                    data_str = content.split('"')[1]
                    data_parts = data_str.split('~')

                    if len(data_parts) > 35:
                        name = data_parts[1]
                        price = float(data_parts[3]) if data_parts[3] and data_parts[3] != '' else 0
                        prev_close = float(data_parts[4]) if data_parts[4] and data_parts[4] != '' else 0
                        change_pct = float(data_parts[32]) if data_parts[32] and data_parts[32] != '' else 0
                        volume = int(float(data_parts[6])) if data_parts[6] and data_parts[6] != '' else 0
                        turnover = int(float(data_parts[7])) if data_parts[7] and data_parts[7] != '' else 0

                        # 获取总市值和总股本
                        market_cap = None
                        total_shares = None

                        if len(data_parts) > 23 and data_parts[23]:
                            try:
                                market_cap = float(data_parts[23])
                            except ValueError:
                                pass

                        if len(data_parts) > 25 and data_parts[25]:
                            try:
                                total_shares = float(data_parts[25])
                            except ValueError:
                                pass

                        # 获取换手率
                        turnover_rate = None
                        if len(data_parts) > 27 and data_parts[27]:
                            try:
                                turnover_rate = float(data_parts[27])
                            except ValueError:
                                pass

                        # 获取PE值 - 按优先级
                        pe_ratio = None
                        pe_fields = [
                            data_parts[39] if len(data_parts) > 39 else None,  # 基本面PE
                            data_parts[22] if len(data_parts) > 22 else None,  # TTM PE
                            data_parts[15] if len(data_parts) > 15 else None,  # 静态PE
                            data_parts[14] if len(data_parts) > 14 else None   # 动态PE
                        ]

                        for pe_str in pe_fields:
                            if pe_str and pe_str != '':
                                try:
                                    pe_value = float(pe_str)
                                    if 0 < pe_value < 1000:
                                        pe_ratio = pe_value
                                        break
                                except ValueError:
                                    continue

                        # 获取PB值
                        pb_ratio = None
                        if len(data_parts) > 16 and data_parts[16]:
                            try:
                                pb_value = float(data_parts[16])
                                if 0 < pb_value < 100:
                                    pb_ratio = pb_value
                            except ValueError:
                                pass

                        return {
                            'code': stock_code,
                            'name': name,
                            'price': price,
                            'prev_close': prev_close,
                            'change_pct': change_pct,
                            'pe_ratio': pe_ratio,
                            'pb_ratio': pb_ratio,
                            'market_cap': market_cap,
                            'total_shares': total_shares,
                            'volume': volume,
                            'turnover': turnover,
                            'turnover_rate': turnover_rate
                        }

            except Exception as e:
                logger.debug(f"获取股票 {stock_code} 实时数据失败: {e}")

            return {}

    async def get_stock_fundamental_data(self, session: aiohttp.ClientSession,
                                        stock_code: str) -> Dict:
        """异步获取股票基本面数据"""
        async with self.semaphore:
            try:
                # 确定市场代码
                if stock_code.startswith('6') or stock_code.startswith('688'):
                    market = 'sh'
                else:
                    market = 'sz'

                symbol = f"{market}{stock_code}"
                url = f"https://qt.gtimg.cn/q={symbol}"

                content = await self._fetch_with_retry(session, url, max_retries=2, timeout=10)

                if content and 'v_' in content and len(content.split('~')) > 52:
                    data_str = content.split('"')[1]
                    data_parts = data_str.split('~')

                    # 解析PB市净率
                    pb_ratio = None
                    if len(data_parts) > 46 and data_parts[46]:
                        try:
                            pb_ratio = float(data_parts[46])
                            if pb_ratio <= 0:
                                pb_ratio = None
                        except ValueError:
                            pass

                    # 解析股息率
                    dividend_yield = None
                    manual_dividend = get_manual_dividend_yield(stock_code)
                    if manual_dividend is not None:
                        dividend_yield = manual_dividend
                    else:
                        current_price = float(data_parts[3]) if data_parts[3] else None
                        dividend_data = None

                        if len(data_parts) > 53 and data_parts[53]:
                            try:
                                dividend_data = float(data_parts[53])
                                if dividend_data < 0:
                                    dividend_data = None
                            except ValueError:
                                pass

                        if current_price and current_price > 0 and dividend_data and dividend_data > 0:
                            per_share_dividend = dividend_data / 10
                            dividend_yield = (per_share_dividend / current_price) * 100

                            if not (0 < dividend_yield <= 20):
                                dividend_yield = None

                    # 解析换手率
                    turnover_rate = None
                    if len(data_parts) > 56 and data_parts[56]:
                        try:
                            turnover_rate = float(data_parts[56])
                        except ValueError:
                            pass

                    # 获取PE和计算PEG
                    pe_ratio = None
                    peg = None
                    if len(data_parts) > 39 and data_parts[39]:
                        try:
                            pe_value = float(data_parts[39])
                            if 0 < pe_value < 200:
                                pe_ratio = pe_value

                                if pb_ratio:
                                    if pb_ratio < 1:
                                        assumed_growth = 20
                                    elif pb_ratio > 5:
                                        assumed_growth = 10
                                    else:
                                        assumed_growth = 15
                                else:
                                    assumed_growth = 15

                                peg = pe_ratio / assumed_growth
                        except ValueError:
                            pass

                    # 计算ROE
                    roe = None
                    if pb_ratio and pe_ratio and pe_ratio > 0:
                        try:
                            roe = (pb_ratio / pe_ratio) * 100
                            if roe < -50 or roe > 50:
                                roe = None
                        except:
                            roe = None

                    # 估算利润增长率
                    profit_growth = None
                    if roe and dividend_yield:
                        try:
                            payout_ratio = min(dividend_yield / roe, 0.9) if roe > 0 else 0.5
                            profit_growth = roe * (1 - payout_ratio)
                        except:
                            profit_growth = None

                    # 计算财务健康度评分
                    financial_health_score = self._calculate_financial_health(
                        pb_ratio, dividend_yield, pe_ratio, turnover_rate
                    )

                    return {
                        'pb_ratio': pb_ratio,
                        'dividend_yield': dividend_yield,
                        'peg': peg,
                        'turnover_rate': turnover_rate,
                        'financial_health_score': financial_health_score,
                        'roe': roe,
                        'profit_growth': profit_growth,
                        'debt_ratio': None,
                        'current_ratio': None,
                        'gross_margin': None,
                        'market_cap': None,
                        'total_shares': None
                    }

            except Exception as e:
                logger.debug(f"获取股票 {stock_code} 基本面数据失败: {e}")

            return {
                'pb_ratio': None,
                'dividend_yield': None,
                'peg': None,
                'turnover_rate': None,
                'financial_health_score': 0,
                'roe': None,
                'profit_growth': None,
                'debt_ratio': None,
                'current_ratio': None,
                'gross_margin': None,
                'market_cap': None,
                'total_shares': None
            }

    def _calculate_financial_health(self, pb: Optional[float], div_yield: Optional[float],
                                   pe: Optional[float], turnover: Optional[float]) -> int:
        """计算财务健康度评分"""
        score = 50

        try:
            if pb:
                if pb < 1:
                    score += 20
                elif pb < 2:
                    score += 10
                elif pb > 10:
                    score -= 20
                elif pb > 5:
                    score -= 10

            if div_yield:
                if div_yield > 5:
                    score += 15
                elif div_yield > 3:
                    score += 10
                elif div_yield > 2:
                    score += 5
                elif div_yield < 1:
                    score -= 5

            if pe:
                if 10 < pe < 20:
                    score += 10
                elif 20 <= pe < 30:
                    score += 5
                elif pe >= 50:
                    score -= 10

            if turnover:
                if 1 < turnover < 5:
                    score += 5
                elif turnover > 20:
                    score -= 5
        except:
            pass

        return max(0, min(100, score))

    async def get_stock_historical_data(self, session: aiohttp.ClientSession,
                                       stock_code: str, days: int = 30) -> pd.DataFrame:
        """异步获取股票历史数据"""
        async with self.semaphore:
            try:
                # 检查缓存
                cache_key = f"{stock_code}_{days}"
                if cache_key in self._hist_cache:
                    cached_data, cached_time = self._hist_cache[cache_key]
                    if time.time() - cached_time < 3600:  # 1小时缓存
                        return cached_data

                # 确定市场代码
                if stock_code.startswith('6') or stock_code.startswith('688'):
                    market = 'sh'
                else:
                    market = 'sz'

                symbol = f"{market}{stock_code}"
                actual_days = int(days * 2)

                url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{actual_days},qfq&_var=kline_dayqfq"

                content = await self._fetch_with_retry(session, url, max_retries=3, timeout=15)

                if content and 'kline_dayqfq=' in content:
                    json_str = content.replace('kline_dayqfq=', '')
                    data_json = json.loads(json_str)

                    if 'data' in data_json and symbol in data_json['data']:
                        kline_data = data_json['data'][symbol]

                        if 'qfqday' in kline_data and kline_data['qfqday']:
                            klines = kline_data['qfqday']

                            if klines:
                                df_data = []
                                for kline in klines:
                                    df_data.append({
                                        'date': kline[0],
                                        'open': float(kline[1]),
                                        'close': float(kline[2]),
                                        'high': float(kline[3]),
                                        'low': float(kline[4]),
                                        'volume': float(kline[5]) if len(kline) > 5 else 0
                                    })

                                data = pd.DataFrame(df_data)
                                data['date'] = pd.to_datetime(data['date'])

                                if len(data) > days:
                                    data = data.tail(days)

                                # 存入缓存
                                self._hist_cache[cache_key] = (data, time.time())

                                return data

            except Exception as e:
                logger.debug(f"获取股票 {stock_code} 历史数据失败: {e}")

            return pd.DataFrame()

    def calculate_momentum(self, price_data: pd.DataFrame, days: int = 20) -> float:
        """计算动量指标"""
        if len(price_data) < days:
            return 0

        try:
            recent_prices = price_data['close'].tail(days)
            momentum = (recent_prices.iloc[-1] / recent_prices.iloc[0] - 1) * 100
            return momentum
        except Exception as e:
            logger.debug(f"计算动量失败: {e}")
            return 0

    async def get_stock_industry_info(self, session: aiohttp.ClientSession,
                                     stock_code: str) -> str:
        """异步获取股票行业信息 - 简化版,直接返回未知"""
        # 为了提升性能,暂时跳过行业信息获取
        # 后续可以通过本地缓存文件来批量获取
        return "未知行业"

    async def batch_get_stock_data(self, stock_codes: List[str],
                                  calculate_momentum: bool = True,
                                  include_fundamental: bool = True) -> List[Dict]:
        """
        批量异步获取股票数据 - 核心优化方法

        Args:
            stock_codes: 股票代码列表
            calculate_momentum: 是否计算动量
            include_fundamental: 是否包含基本面数据

        Returns:
            股票数据列表
        """
        # 初始化信号量
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

        # 去重
        stock_codes = list(set(stock_codes))
        logger.info(f"开始批量获取 {len(stock_codes)} 只股票数据 (最大并发: {self.max_concurrent})")

        start_time = time.time()

        # 创建TCP连接器,增加连接数和超时设置
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,  # 总连接数
            limit_per_host=self.max_concurrent,  # 每个主机的连接数
            ttl_dns_cache=300,  # DNS缓存5分钟
        )

        timeout = aiohttp.ClientTimeout(
            total=60,  # 总超时60秒
            connect=10,  # 连接超时10秒
            sock_read=15  # 读取超时15秒
        )

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 第一步: 批量获取实时数据
            logger.info("步骤1: 批量获取实时数据...")
            realtime_tasks = [
                self.get_stock_realtime_data(session, code)
                for code in stock_codes
            ]
            realtime_results = await asyncio.gather(*realtime_tasks)

            # 过滤掉空结果
            valid_stocks = [data for data in realtime_results if data and data.get('code')]
            logger.info(f"成功获取 {len(valid_stocks)}/{len(stock_codes)} 只股票实时数据")

            if not valid_stocks:
                return []

            # 第二步: 批量获取基本面数据
            if include_fundamental:
                logger.info("步骤2: 批量获取基本面数据...")
                fundamental_tasks = [
                    self.get_stock_fundamental_data(session, stock['code'])
                    for stock in valid_stocks
                ]
                fundamental_results = await asyncio.gather(*fundamental_tasks)

                # 合并基本面数据
                for stock, fundamental in zip(valid_stocks, fundamental_results):
                    stock.update(fundamental)

            # 第三步: 批量获取历史数据并计算动量
            if calculate_momentum:
                logger.info("步骤3: 批量获取历史数据并计算动量...")
                historical_tasks = [
                    self.get_stock_historical_data(session, stock['code'], days=30)
                    for stock in valid_stocks
                ]
                historical_results = await asyncio.gather(*historical_tasks)

                # 计算动量
                momentum_success = 0
                for stock, hist_data in zip(valid_stocks, historical_results):
                    if not hist_data.empty and len(hist_data) >= 20:
                        momentum = self.calculate_momentum(hist_data, days=20)
                        stock['momentum_20d'] = momentum
                        momentum_success += 1
                    else:
                        stock['momentum_20d'] = 0

                logger.info(f"动量计算成功: {momentum_success}/{len(valid_stocks)}")
            else:
                for stock in valid_stocks:
                    stock['momentum_20d'] = 0

            # 第四步: 批量获取行业信息 (简化版)
            for stock in valid_stocks:
                stock['industry'] = "未知行业"

        elapsed = time.time() - start_time
        logger.info(f"批量获取完成! 用时: {elapsed:.2f}秒, 平均速度: {len(valid_stocks)/elapsed:.1f}只/秒")

        return valid_stocks

    async def get_market_overview_async(self) -> Dict:
        """异步获取市场概况 - 使用缓存优化"""
        try:
            # 检查缓存文件
            cache_file = './cache/market_overview.json'
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    cache_time = datetime.fromisoformat(cached_data.get('cache_time', '2000-01-01'))

                    # 如果缓存在5分钟内,直接使用
                    if (datetime.now() - cache_time).seconds < 300:
                        logger.info("使用缓存的市场概况数据")
                        return cached_data['data']

            logger.info("正在获取市场概况数据...")

            # 创建会话
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 获取主要指数数据
                url = "https://qt.gtimg.cn/q=sh000001,sz399001,sz399006"
                headers = {
                    'User-Agent': self._get_random_user_agent(),
                    'Referer': 'https://gu.qq.com/'
                }

                index_data = []
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            if 'v_' in content:
                                lines = content.strip().split(';')

                                for line in lines:
                                    if 'v_' in line and '~' in line:
                                        data_str = line.split('"')[1]
                                        parts = data_str.split('~')
                                        if len(parts) > 32:
                                            index_data.append({
                                                'name': parts[1],
                                                'change_pct': float(parts[32]) if parts[32] else 0,
                                                'price': float(parts[3]) if parts[3] else 0
                                            })
                except Exception as e:
                    logger.warning(f"获取指数数据失败: {e}")

                avg_change = sum(d['change_pct'] for d in index_data[:3]) / 3 if index_data else 0

                # 使用简化的市场统计 - 只统计沪深300的涨跌情况
                # 加载沪深300列表
                csi300_file = './data/csi300_stocks.json'
                if os.path.exists(csi300_file):
                    with open(csi300_file, 'r', encoding='utf-8') as f:
                        csi300_data = json.load(f)
                        stock_codes = [s['code'] for s in csi300_data['stocks']]

                    # 批量查询沪深300股票涨跌
                    rising = 0
                    falling = 0
                    flat = 0

                    # 分批查询
                    batch_size = 100
                    for i in range(0, len(stock_codes), batch_size):
                        batch = stock_codes[i:i+batch_size]
                        symbols = []
                        for code in batch:
                            if code.startswith('6'):
                                symbols.append(f"sh{code}")
                            else:
                                symbols.append(f"sz{code}")

                        batch_url = f"https://qt.gtimg.cn/q={','.join(symbols)}"

                        try:
                            async with session.get(batch_url, headers=headers, timeout=15) as response:
                                if response.status == 200:
                                    content = await response.text()
                                    lines = content.strip().split(';')

                                    for line in lines:
                                        if 'v_' in line and '~' in line:
                                            try:
                                                data_str = line.split('"')[1]
                                                parts = data_str.split('~')

                                                if len(parts) > 32:
                                                    change_pct = float(parts[32]) if parts[32] else 0

                                                    if change_pct > 0:
                                                        rising += 1
                                                    elif change_pct < 0:
                                                        falling += 1
                                                    else:
                                                        flat += 1
                                            except:
                                                continue
                        except Exception as e:
                            logger.debug(f"批次查询失败: {e}")
                            continue

                        # 小延迟避免限流
                        await asyncio.sleep(0.3)

                    total = rising + falling + flat
                    rising_ratio = (rising / total * 100) if total > 0 else 50.0

                    overview = {
                        'total_stocks': 300,  # 沪深300
                        'rising_stocks': rising,
                        'falling_stocks': falling,
                        'flat_stocks': flat,
                        'rising_ratio': rising_ratio,
                        'avg_change_pct': avg_change,
                        'update_time': datetime.now(),
                        'data_source': '腾讯财经实时数据(沪深300)',
                        'indices': index_data,
                        'note': f'统计沪深300成分股涨跌数据',
                        'success_count': total
                    }

                    # 保存缓存
                    os.makedirs('./cache', exist_ok=True)
                    cache_data = {
                        'cache_time': datetime.now().isoformat(),
                        'data': overview
                    }
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, default=str)

                    logger.info(f"市场概况获取成功: 上涨{rising}, 下跌{falling}, 上涨比例{rising_ratio:.2f}%")
                    return overview

            # 如果失败,返回兜底数据
            return {
                'total_stocks': 300,
                'rising_stocks': 135,
                'falling_stocks': 105,
                'flat_stocks': 60,
                'rising_ratio': 45.0,
                'avg_change_pct': 0.2,
                'update_time': datetime.now(),
                'data_source': '兜底数据',
                'note': '无法获取实际市场数据'
            }

        except Exception as e:
            logger.error(f"获取市场概况失败: {e}")
            return {
                'total_stocks': 300,
                'rising_stocks': 135,
                'falling_stocks': 105,
                'flat_stocks': 60,
                'rising_ratio': 45.0,
                'avg_change_pct': 0.2,
                'update_time': datetime.now(),
                'data_source': '错误兜底',
                'error': str(e)
            }


# 同步包装函数,方便在非异步代码中使用
def batch_get_stock_data_sync(stock_codes: List[str], calculate_momentum: bool = True,
                              include_fundamental: bool = True, max_concurrent: int = 20) -> List[Dict]:
    """
    同步版本的批量获取股票数据

    Args:
        stock_codes: 股票代码列表
        calculate_momentum: 是否计算动量
        include_fundamental: 是否包含基本面数据
        max_concurrent: 最大并发数

    Returns:
        股票数据列表
    """
    fetcher = AsyncStockDataFetcher(max_concurrent=max_concurrent)
    return asyncio.run(
        fetcher.batch_get_stock_data(stock_codes, calculate_momentum, include_fundamental)
    )


def get_market_overview_sync() -> Dict:
    """同步版本的获取市场概况"""
    fetcher = AsyncStockDataFetcher()
    return asyncio.run(fetcher.get_market_overview_async())
