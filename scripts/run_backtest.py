#!/usr/bin/env python3
"""
沪深300策略回测 - 使用真实历史数据
与实盘评分逻辑完全一致，含基准对比和交易成本
"""

import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import akshare as ak
import pandas as pd
import numpy as np
import pickle
import time
import logging
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.backtest_config import BACKTEST_PARAMS
from src.analysis.stock_filter import StockFilter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_stock_filter = StockFilter()

CACHE_DIR = './cache/backtest'
os.makedirs(CACHE_DIR, exist_ok=True)


# === PLACEHOLDER_DATA_LOADING ===


def load_or_fetch(cache_key, fetch_fn, expire_days=7):
    """通用缓存加载"""
    cache_file = os.path.join(CACHE_DIR, f'{cache_key}.pkl')
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < expire_days * 86400:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    data = fetch_fn()
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)
    return data


def get_report_date(trade_date: str) -> str:
    """根据交易日期确定当时已公布的最新财报期"""
    dt = datetime.strptime(trade_date, '%Y-%m-%d')
    y = dt.year
    m = dt.month
    if m <= 4:
        return f'{y-1}0930'
    elif m <= 8:
        return f'{y}0331'
    elif m <= 10:
        return f'{y}0630'
    else:
        return f'{y}0930'


# === PLACEHOLDER_FETCH_FUNCTIONS ===


def fetch_all_daily_data(stock_codes, start_date, end_date):
    """批量获取所有股票日线数据（使用腾讯API，快速无限流）"""
    cache_file = os.path.join(CACHE_DIR, 'daily_data.pkl')
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < 1 * 86400:
            with open(cache_file, 'rb') as f:
                cached = pickle.load(f)
            if len(cached) >= len(stock_codes) * 0.9:
                sample = next(iter(cached.values()))
                if sample.index[-1] >= pd.Timestamp(end_date) - pd.Timedelta(days=3):
                    logger.info(f"使用缓存日线数据: {len(cached)}只")
                    return cached

    all_data = {}
    total = len(stock_codes)
    failed_codes = []

    for i, code in enumerate(stock_codes):
        try:
            prefix = 'sz' if code.startswith(('0', '3')) else 'sh'
            url = (f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
                   f'?param={prefix}{code},day,{start_date},{end_date},800,qfq')
            r = requests.get(url, timeout=10)
            data = r.json()
            key = f'{prefix}{code}'
            klines = data['data'][key].get('qfqday', data['data'][key].get('day', []))
            if klines:
                rows = [row[:6] for row in klines]
                df = pd.DataFrame(rows, columns=['日期', '开盘', '收盘', '最高', '最低', '成交量'])
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
                for col in ['开盘', '收盘', '最高', '最低', '成交量']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df['涨跌幅'] = df['收盘'].pct_change() * 100
                df['换手率'] = 2.0
                all_data[code] = df
        except Exception:
            failed_codes.append(code)

        if (i + 1) % 50 == 0:
            logger.info(f"  日线数据: {i+1}/{total} (成功{len(all_data)})")
            time.sleep(1)

    if failed_codes:
        logger.warning(f"日线获取失败: {len(failed_codes)}只")
    logger.info(f"日线数据获取完成: {len(all_data)}/{total}")

    with open(cache_file, 'wb') as f:
        pickle.dump(all_data, f)
    return all_data


def fetch_financial_data(report_dates):
    """获取多个报告期的财报数据"""
    def _fetch():
        fin_data = {}
        for rd in report_dates:
            try:
                logger.info(f"  获取财报: {rd}")
                df = ak.stock_yjbb_em(date=rd)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        code = str(row['股票代码']).zfill(6)
                        fin_data.setdefault(code, {})
                        fin_data[code][rd] = {
                            'roe': float(row['净资产收益率']) if pd.notna(row['净资产收益率']) else None,
                            'profit_growth': float(row['净利润-同比增长']) if pd.notna(row['净利润-同比增长']) else None,
                            'eps': float(row['每股收益']) if pd.notna(row['每股收益']) else None,
                            'bvps': float(row['每股净资产']) if pd.notna(row['每股净资产']) else None,
                        }
                time.sleep(2)
            except Exception as e:
                logger.warning(f"  财报{rd}获取失败: {e}")
        return fin_data
    return load_or_fetch('financial_data', _fetch)


# === PLACEHOLDER_BENCHMARK ===


def fetch_benchmark():
    """获取沪深300指数日线"""
    def _fetch():
        df = ak.stock_zh_index_daily(symbol='sh000300')
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df
    return load_or_fetch('benchmark_300', _fetch)


def build_stock_data(code, daily_df, trade_date, fin_data):
    """为某只股票在某个交易日构建完整的stock_data字典"""
    if code not in daily_df:
        return None
    df = daily_df[code]
    if trade_date not in df.index:
        return None

    row = df.loc[trade_date]
    price = float(row['收盘'])
    loc = df.index.get_loc(trade_date)

    # 20日动量
    momentum_20d = 0
    if loc >= 20:
        price_20d_ago = float(df.iloc[loc - 20]['收盘'])
        momentum_20d = (price / price_20d_ago - 1) * 100

    # 5日动量
    momentum_5d = 0
    if loc >= 5:
        price_5d_ago = float(df.iloc[loc - 5]['收盘'])
        momentum_5d = (price / price_5d_ago - 1) * 100

    # 量比（当日成交量 / 20日平均成交量）
    volume_ratio = 1.0
    if loc >= 20:
        avg_vol = df.iloc[loc - 20:loc]['成交量'].mean()
        if avg_vol > 0:
            volume_ratio = float(row['成交量']) / avg_vol

    # 20日波动率（日收益率标准差）
    volatility_20d = 0
    if loc >= 20:
        returns = df.iloc[loc - 20:loc]['涨跌幅']
        volatility_20d = float(returns.std()) if len(returns) > 0 else 0

    # 20日最大回撤
    max_drawdown_20d = 0
    if loc >= 20:
        prices_20d = df.iloc[loc - 20:loc + 1]['收盘']
        cummax = prices_20d.cummax()
        drawdowns = (prices_20d - cummax) / cummax * 100
        max_drawdown_20d = float(drawdowns.min())

    # 换手率（硬编码，仅用于兼容旧逻辑）
    turnover_rate = float(row['换手率']) if '换手率' in row and pd.notna(row['换手率']) else 2.0

    # 财报数据
    report_date = get_report_date(trade_date.strftime('%Y-%m-%d'))
    fin = {}
    if code in fin_data and report_date in fin_data[code]:
        fin = fin_data[code][report_date]

    eps = fin.get('eps')
    bvps = fin.get('bvps')
    pe_ratio = price / eps if eps and eps > 0 else None
    pb_ratio = price / bvps if bvps and bvps > 0 else None

    return {
        'code': code,
        'name': code,
        'price': price,
        'change_pct': float(row['涨跌幅']),
        'turnover_rate': turnover_rate,
        'momentum_20d': momentum_20d,
        'momentum_5d': momentum_5d,
        'volume_ratio': volume_ratio,
        'volatility_20d': volatility_20d,
        'max_drawdown_20d': max_drawdown_20d,
        'pe_ratio': pe_ratio,
        'pb_ratio': pb_ratio,
        'roe': fin.get('roe'),
        'profit_growth': fin.get('profit_growth'),
        'dividend_yield': None,
    }


def score_stock_optimized(s):
    """优化后的评分体系（满分100）- 平衡型"""
    score = 0
    momentum = s.get('momentum_20d', 0)
    momentum_5d = s.get('momentum_5d', 0)
    volume_ratio = s.get('volume_ratio', 1.0)
    pe = s.get('pe_ratio')
    pb = s.get('pb_ratio')
    roe = s.get('roe')
    growth = s.get('profit_growth')
    volatility = s.get('volatility_20d', 0)
    max_dd = s.get('max_drawdown_20d', 0)
    dividend = s.get('dividend_yield')

    # === 技术面（25分）===

    # 动量评分（15分）— 回归原始逻辑
    if 5 < momentum <= 10:
        m_score = 15
    elif 10 < momentum <= 15:
        m_score = 13
    elif 3 < momentum <= 5:
        m_score = 10
    elif 15 < momentum <= 25:
        m_score = 8
    elif 0 < momentum <= 3:
        m_score = 6
    elif momentum > 25:
        m_score = 3
    elif -3 < momentum <= 0:
        m_score = 2
    else:
        m_score = 0

    # 5日动量防追高：短期加速过猛时减半
    if momentum > 10 and momentum_5d > momentum * 0.6:
        m_score = m_score // 2

    score += m_score

    # 量比评分（10分）
    if 0.8 <= volume_ratio < 1.5:
        score += 10
    elif 1.5 <= volume_ratio < 2.5:
        score += 7
    elif 0.5 <= volume_ratio < 0.8:
        score += 5
    elif 2.5 <= volume_ratio < 4.0:
        score += 3

    # === 估值（25分）===

    # PE评分（10分）
    if pe and 0 < pe < 10:
        score += 10
    elif pe and 10 <= pe < 20:
        score += 7
    elif pe and 20 <= pe < 30:
        score += 4

    # PB评分（5分）
    if pb and 0 < pb < 2:
        score += 5
    elif pb and 2 <= pb < 4:
        score += 4
    elif pb and 4 <= pb < 7:
        score += 2

    # PR市赚率评分（10分）
    if pe and roe and roe > 0:
        pr = pe / (100 * roe / 100)
        if 0 < pr < 0.8:
            score += 10
        elif 0.8 <= pr < 1.0:
            score += 7
        elif 1.0 <= pr < 1.2:
            score += 3

    # === 盈利质量（25分）===

    # ROE（12分）
    if roe and roe > 20:
        score += 12
    elif roe and roe > 15:
        score += 10
    elif roe and roe > 10:
        score += 7
    elif roe and roe > 5:
        score += 3

    # 利润增长（13分）
    if growth and growth > 30:
        score += 13
    elif growth and growth > 20:
        score += 10
    elif growth and growth > 10:
        score += 7
    elif growth and growth > 0:
        score += 3

    # === 安全性（20分）===

    # PB安全边际（5分）
    if pb and 0 < pb < 1.0:
        score += 5
    elif pb and 1.0 <= pb < 1.5:
        score += 4
    elif pb and 1.5 <= pb < 2.5:
        score += 2

    # 20日波动率（8分）
    if volatility < 1.5:
        score += 8
    elif volatility < 2.5:
        score += 6
    elif volatility < 3.5:
        score += 3

    # 20日最大回撤（7分）
    if max_dd > -5:
        score += 7
    elif max_dd > -8:
        score += 4
    elif max_dd > -12:
        score += 2

    # === 分红（5分）===
    if dividend and dividend > 5:
        score += 5
    elif dividend and dividend > 3:
        score += 4
    elif dividend and dividend > 2:
        score += 3
    elif dividend and dividend > 1:
        score += 2

    return score


SECTOR_MAP = {
    '银行': {'601077','601825','601916','601658','601838','600919','600926','601229',
             '601818','601288','002142','601009','601169','601328','601998','601166',
             '601398','601988','600015','600016','600036','601939'},
    '电力': {'600027','600023','600025','600011','601985','600886','600930'},
    '证券': {'601136','601059','600918','601236','601878','002736','600958','601788',
             '600999','601688','601377','000776','601901','600030'},
    '保险': {'601336','601601','601628','601319','601318'},
}

CODE_TO_SECTOR = {}
for sector, codes in SECTOR_MAP.items():
    for code in codes:
        CODE_TO_SECTOR[code] = sector


def select_stocks_optimized(all_stocks, max_stocks=6):
    """优化后的选股逻辑"""
    # 去重
    seen = set()
    unique_stocks = []
    for s in all_stocks:
        if s['code'] not in seen:
            seen.add(s['code'])
            unique_stocks.append(s)

    # PE筛选
    filtered = [s for s in unique_stocks if s.get('pe_ratio') and 0 < s['pe_ratio'] <= 30]

    # 排除停牌和跌停
    filtered = [s for s in filtered if not (
        s.get('change_pct', 0) == 0 and s.get('turnover_rate', 0) < 0.1
    )]
    filtered = [s for s in filtered if s.get('change_pct', 0) > -9.8]

    # 评分并排序
    for s in filtered:
        s['opt_score'] = score_stock_optimized(s)

    # 最低分数35
    filtered = [s for s in filtered if s['opt_score'] >= 35]

    # 排序取前N
    filtered.sort(key=lambda x: x['opt_score'], reverse=True)
    return filtered[:max_stocks]


def select_stocks_offensive(all_stocks, max_stocks=6):
    """进攻模式选股 - 调用stock_filter统一逻辑"""
    return _stock_filter.select_top_stocks_offensive(all_stocks)


def select_stocks_ultra_defensive(all_stocks, max_stocks=6):
    """超防守选股 - 调用stock_filter统一逻辑"""
    return _stock_filter.select_top_stocks_ultra_defensive(all_stocks)


def run_backtest():
    """执行回测"""
    params = BACKTEST_PARAMS
    start = params['start_date']
    end = params['end_date']
    hold_days = params['hold_days']
    cost_buy = params['cost_buy']
    cost_sell = params['cost_sell']

    logger.info(f"回测参数: {start} ~ {end}, 持仓{hold_days}天")
    logger.info(f"交易成本: 买入{cost_buy*100}% + 卖出{cost_sell*100}%")

    # 1. 加载成分股
    import json
    with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
        csi300 = json.load(f)
    stock_codes = [s['code'] for s in csi300['stocks']]
    logger.info(f"股票池: {len(stock_codes)}只")

    # 2. 获取数据（带缓存）
    logger.info("获取日线数据...")
    # 多取35天用于计算动量；fetch到昨天以追踪本月建议表现
    fetch_start = (datetime.strptime(start, '%Y-%m-%d') - timedelta(days=50)).strftime('%Y-%m-%d')
    from datetime import date
    yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    fetch_end = max(end, yesterday)
    daily_data = fetch_all_daily_data(stock_codes, fetch_start, fetch_end)

    logger.info("获取财报数据...")
    report_dates = ['20230630', '20230930', '20231231', '20240331', '20240630',
                        '20240930', '20241231', '20250331', '20250630', '20250930', '20251231',
                        '20260331', '20260630']
    fin_data = fetch_financial_data(report_dates)

    logger.info("获取沪深300基准...")
    benchmark = fetch_benchmark()

    # 3. 生成交易日序列
    sample_code = next(iter(daily_data))
    all_trading_days = daily_data[sample_code].index
    mask = (all_trading_days >= start) & (all_trading_days <= end)
    trading_days = all_trading_days[mask].tolist()
    logger.info(f"交易日数: {len(trading_days)}")

    # 4. 回测循环（逐日模拟：月度调仓+MA60±2%缓冲带+-7%止损）
    stop_loss_pct = -0.07
    cost = cost_buy + cost_sell
    results = []
    daily_navs = []

    nav_base = 1.0
    holdings = []  # [(code, buy_price, weight)]
    stopped = {}
    last_rebal_month = None
    rebal_start_idx = 0
    bull_mode = False  # 缓冲带内维持上一次模式
    was_bull = False

    i = 0
    while i < len(trading_days):
        today = trading_days[i]
        is_rebal_day = (today.year, today.month) != last_rebal_month

        if is_rebal_day:
            # 调仓日：先结算旧持仓
            if last_rebal_month is not None and (holdings or stopped):
                port_return = 0
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        port_return += weight * ret
                cash_return = sum(stopped.values())
                period_ret = port_return + cash_return
                # 只对存活持仓收调仓成本，止损仓位已卖出不再收费
                active_weight = sum(w for _, _, w in holdings)
                rebal_cost = cost * active_weight if active_weight > 0 else 0
                nav_base = nav_base * (1 + period_ret) * (1 - rebal_cost)

                buy_date_str = trading_days[rebal_start_idx].strftime('%Y-%m-%d')
                sell_date_str = today.strftime('%Y-%m-%d')
                bench_ret = 0
                bd = trading_days[rebal_start_idx]
                if bd in benchmark.index and today in benchmark.index:
                    bench_ret = (benchmark.loc[today]['close'] / benchmark.loc[bd]['close'] - 1) * 100
                strat_ret_pct = ((1 + period_ret) * (1 - rebal_cost) - 1) * 100
                # 逐只归因
                contribs = []
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cp = float(daily_data[code].loc[today]['收盘'])
                        contribs.append({'code': code, 'pnl': (cp/buy_price-1)*weight*100})
                for code, locked in stopped.items():
                    contribs.append({'code': code+'*', 'pnl': locked*100})
                contribs.sort(key=lambda x: x['pnl'], reverse=True)

                results.append({
                    'buy_date': buy_date_str,
                    'sell_date': sell_date_str,
                    'strategy_return': strat_ret_pct,
                    'benchmark_return': bench_ret,
                    'excess_return': strat_ret_pct - bench_ret,
                    'num_stocks': len(holdings) + len(stopped),
                    'win_count': sum(1 for c, bp, w in holdings
                                     if c in daily_data and today in daily_data[c].index
                                     and float(daily_data[c].loc[today]['收盘']) / bp - 1 > 0),
                    'mode': '进攻' if was_bull else '防守',
                    'contribs': contribs,
                })

            # MA60 ±2%缓冲带趋势判断（与实盘market_analyzer一致）
            if today in benchmark.index:
                loc = benchmark.index.get_loc(today)
                if loc >= 60:
                    ma60 = benchmark.iloc[loc-60:loc]['close'].mean()
                    cur = float(benchmark.loc[today]['close'])
                    if cur > ma60 * 1.02:
                        bull_mode = True
                    elif cur < ma60 * 0.98:
                        bull_mode = False
                    # 缓冲带内 bull_mode 保持上一次

            all_stocks = []
            for code in stock_codes:
                sd = build_stock_data(code, daily_data, today, fin_data)
                if sd:
                    all_stocks.append(sd)

            if bull_mode:
                selected = select_stocks_offensive(all_stocks)
            else:
                selected = select_stocks_ultra_defensive(all_stocks)

            was_bull = bull_mode
            holdings = []
            stopped = {}
            if selected:
                w = 1.0 / len(selected)
                for s in selected:
                    holdings.append((s['code'], s['price'], w))

            last_rebal_month = (today.year, today.month)
            rebal_start_idx = i
            daily_navs.append(nav_base)
        else:
            # 非调仓日：逐日盯盘止损，剩余仓位继续
            if not holdings:
                daily_navs.append(nav_base)
            else:
                port_return = 0
                new_holdings = []
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        if ret < stop_loss_pct:
                            stopped[code] = weight * ret
                        else:
                            port_return += weight * ret
                            new_holdings.append((code, buy_price, weight))
                    else:
                        new_holdings.append((code, buy_price, weight))
                holdings = new_holdings
                cash_return = sum(stopped.values())
                daily_navs.append(nav_base * (1 + port_return + cash_return))

        i += 1

    # 结算最后一期未了结的持仓
    if holdings or stopped:
        last_day = trading_days[-1]
        port_return = 0
        for code, buy_price, weight in holdings:
            if code in daily_data and last_day in daily_data[code].index:
                cur_price = float(daily_data[code].loc[last_day]['收盘'])
                port_return += weight * (cur_price / buy_price - 1)
        cash_return = sum(stopped.values())
        period_ret = port_return + cash_return
        active_weight = sum(w for _, _, w in holdings)
        rebal_cost = cost * active_weight if active_weight > 0 else 0
        nav_base = nav_base * (1 + period_ret) * (1 - rebal_cost)

        buy_date_str = trading_days[rebal_start_idx].strftime('%Y-%m-%d')
        sell_date_str = last_day.strftime('%Y-%m-%d')
        bench_ret = 0
        bd = trading_days[rebal_start_idx]
        if bd in benchmark.index and last_day in benchmark.index:
            bench_ret = (benchmark.loc[last_day]['close'] / benchmark.loc[bd]['close'] - 1) * 100
        strat_ret_pct = ((1 + period_ret) * (1 - rebal_cost) - 1) * 100
        contribs = []
        for code, buy_price, weight in holdings:
            if code in daily_data and last_day in daily_data[code].index:
                cp = float(daily_data[code].loc[last_day]['收盘'])
                contribs.append({'code': code, 'pnl': (cp/buy_price-1)*weight*100})
        for code, locked in stopped.items():
            contribs.append({'code': code+'*', 'pnl': locked*100})
        contribs.sort(key=lambda x: x['pnl'], reverse=True)
        results.append({
            'buy_date': buy_date_str,
            'sell_date': sell_date_str,
            'strategy_return': strat_ret_pct,
            'benchmark_return': bench_ret,
            'excess_return': strat_ret_pct - bench_ret,
            'num_stocks': len(holdings) + len(stopped),
            'win_count': sum(1 for c, bp, w in holdings
                             if c in daily_data and last_day in daily_data[c].index
                             and float(daily_data[c].loc[last_day]['收盘']) / bp - 1 > 0),
            'mode': '进攻' if was_bull else '防守',
            'contribs': contribs,
        })
        daily_navs[-1] = nav_base

    # 5. 输出结果
    print_results(results, daily_navs, benchmark)
    plot_backtest_results(results, daily_navs, trading_days, benchmark)

    # 6. 本月持仓建议（用回测最后一天数据选股）
    recommendation = get_recommendation(daily_data, fin_data, benchmark,
                                        stock_codes, trading_days[-1])
    recommendation = track_recommendation_performance(recommendation, daily_data, benchmark)
    generate_html_report(results, daily_navs, trading_days, benchmark,
                         recommendation)
    print_recommendation(recommendation)


# === PLACEHOLDER_PRINT ===


def print_results(results, daily_navs=None, benchmark=None):
    """打印回测结果"""
    if not results:
        print("无回测结果")
        return

    strat_returns = [r['strategy_return'] for r in results]

    # 策略累计收益：优先用逐日净值（最准确）
    if daily_navs and len(daily_navs) > 1:
        cum_strat = daily_navs[-1]
    else:
        cum_strat = 1.0
        for r in results:
            cum_strat *= (1 + r['strategy_return'] / 100)

    # 基准累计收益：直接用起止日收盘价（避免空仓期漏算）
    cum_bench = 1.0
    if benchmark is not None:
        from datetime import datetime
        start_d = results[0]['buy_date']
        end_d = results[-1]['sell_date']
        start_dt = datetime.strptime(start_d, '%Y-%m-%d')
        end_dt = datetime.strptime(end_d, '%Y-%m-%d')
        bm_dates = benchmark.index
        bm_start = bm_dates[bm_dates >= start_dt][0]
        bm_end = bm_dates[bm_dates <= end_dt][-1]
        cum_bench = float(benchmark.loc[bm_end]['close']) / float(benchmark.loc[bm_start]['close'])
    else:
        for r in results:
            cum_bench *= (1 + r['benchmark_return'] / 100)

    # 最大回撤：优先用逐日净值（更精确）
    max_drawdown = 0
    if daily_navs and len(daily_navs) > 1:
        peak = daily_navs[0]
        for v in daily_navs:
            peak = max(peak, v)
            dd = (peak - v) / peak
            max_drawdown = max(max_drawdown, dd)
    else:
        max_cum = 1.0
        cum_tmp = 1.0
        for r in results:
            cum_tmp *= (1 + r['strategy_return'] / 100)
            max_cum = max(max_cum, cum_tmp)
            dd = (max_cum - cum_tmp) / max_cum
            max_drawdown = max(max_drawdown, dd)

    total_wins = sum(r['win_count'] for r in results)
    total_trades = sum(r['num_stocks'] for r in results)
    win_rate = total_wins / total_trades * 100 if total_trades else 0

    print(f"\n{'='*60}")
    print(f"  回测结果: {results[0]['buy_date']} ~ {results[-1]['sell_date']}")
    print(f"{'='*60}")
    print(f"  调仓次数:     {len(results)}")
    print(f"  总交易笔数:   {total_trades}")
    print(f"{'='*60}")
    print(f"  策略累计收益:  {(cum_strat-1)*100:+.2f}%")
    print(f"  基准累计收益:  {(cum_bench-1)*100:+.2f}%")
    print(f"  超额收益:     {(cum_strat-cum_bench)*100:+.2f}%")
    print(f"{'='*60}")
    print(f"  单期平均收益:  {np.mean(strat_returns):+.2f}%")
    print(f"  单期最佳:     {max(strat_returns):+.2f}%")
    print(f"  单期最差:     {min(strat_returns):+.2f}%")
    print(f"  胜率:         {win_rate:.1f}%")
    print(f"  最大回撤:     {max_drawdown*100:.2f}%")
    print(f"{'='*60}")

    # 逐期明细
    print(f"\n{'买入日期':<12} {'卖出日期':<12} {'策略':>7} {'基准':>7} {'超额':>7}")
    print('-' * 55)
    for r in results:
        print(f"{r['buy_date']:<12} {r['sell_date']:<12} "
              f"{r['strategy_return']:>+6.2f}% {r['benchmark_return']:>+6.2f}% "
              f"{r['excess_return']:>+6.2f}%")


def plot_backtest_results(results, daily_navs=None, trading_days=None, benchmark=None):
    """绘制回测净值曲线"""
    if not results:
        return

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter, MonthLocator

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 使用逐日净值数据（更精确）
    if daily_navs and trading_days and benchmark is not None:
        dates = [d.to_pydatetime() if hasattr(d, 'to_pydatetime') else d for d in trading_days]
        strat_curve = [(v - 1) * 100 for v in daily_navs]

        # 基准逐日净值
        base_price = float(benchmark.loc[trading_days[0]]['close']) if trading_days[0] in benchmark.index else 1
        bench_curve = []
        for d in trading_days:
            if d in benchmark.index:
                bench_curve.append((float(benchmark.loc[d]['close']) / base_price - 1) * 100)
            else:
                bench_curve.append(bench_curve[-1] if bench_curve else 0)

        # 最大回撤
        peak = daily_navs[0]
        max_dd = 0
        for v in daily_navs:
            peak = max(peak, v)
            max_dd = max(max_dd, (peak - v) / peak)
    else:
        # 降级：从期间结果计算
        dates = [datetime.strptime(r['sell_date'], '%Y-%m-%d') for r in results]
        cum_s, cum_b, max_s, max_dd = 1.0, 1.0, 1.0, 0
        strat_curve, bench_curve = [], []
        for r in results:
            cum_s *= (1 + r['strategy_return'] / 100)
            cum_b *= (1 + r['benchmark_return'] / 100)
            max_s = max(max_s, cum_s)
            max_dd = max(max_dd, (max_s - cum_s) / max_s)
            strat_curve.append((cum_s - 1) * 100)
            bench_curve.append((cum_b - 1) * 100)

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(dates, strat_curve, color='#E63946', linewidth=2.2,
            label=f'策略 {strat_curve[-1]:+.1f}% (回撤{max_dd*100:.1f}%)')
    ax.plot(dates, bench_curve, color='#6C757D', linewidth=1.8, linestyle='--',
            label=f'沪深300 {bench_curve[-1]:+.1f}%')

    ax.fill_between(dates, bench_curve, strat_curve,
                    where=[s > b for s, b in zip(strat_curve, bench_curve)],
                    alpha=0.15, color='#E63946', interpolate=True)
    ax.fill_between(dates, bench_curve, strat_curve,
                    where=[s <= b for s, b in zip(strat_curve, bench_curve)],
                    alpha=0.15, color='#6C757D', interpolate=True)

    ax.axhline(y=0, color='black', linewidth=0.5, alpha=0.3)
    ax.set_xlabel('日期', fontsize=11)
    ax.set_ylabel('累计收益率 (%)', fontsize=11)
    ax.set_title(f'MA60趋势择时回测（{results[0]["buy_date"]} ~ {results[-1]["sell_date"]}）',
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='-')
    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    fig.autofmt_xdate(rotation=30)

    plt.tight_layout()
    os.makedirs('./charts', exist_ok=True)
    out_path = './charts/backtest_curve.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\n净值曲线已保存: {out_path}")


def generate_html_report(results, daily_navs, trading_days, benchmark,
                         recommendation=None):
    """生成图文并茂的HTML回测报告"""
    import base64, json as _json
    from io import BytesIO
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter, MonthLocator

    # 股票代码→名称映射
    _name_map = {}
    try:
        with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as _f:
            for s in _json.load(_f)['stocks']:
                _name_map[s['code']] = s['name']
    except Exception:
        pass

    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False

    if not results or not daily_navs:
        return

    # === KPI 计算 ===
    cum_strat = daily_navs[-1]

    start_dt = datetime.strptime(results[0]['buy_date'], '%Y-%m-%d')
    end_dt = datetime.strptime(results[-1]['sell_date'], '%Y-%m-%d')
    bm_dates = benchmark.index
    bm_start = bm_dates[bm_dates >= start_dt][0]
    bm_end = bm_dates[bm_dates <= end_dt][-1]
    cum_bench = float(benchmark.loc[bm_end]['close']) / float(
        benchmark.loc[bm_start]['close'])

    peak = daily_navs[0]
    max_dd = 0
    for v in daily_navs:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak)

    total_wins = sum(r['win_count'] for r in results)
    total_trades = sum(r['num_stocks'] for r in results)
    win_rate = total_wins / total_trades * 100 if total_trades else 0

    years = (end_dt - start_dt).days / 365.25
    ann_ret = (cum_strat ** (1/years) - 1) * 100 if years > 0 else 0

    # === 图1: 净值曲线 ===
    def chart_to_base64(fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=130, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode()

    dates = [d.to_pydatetime() if hasattr(d, 'to_pydatetime')
             else d for d in trading_days]

    base_price = float(benchmark.loc[trading_days[0]]['close']) if trading_days[0] in benchmark.index else 1
    bench_curve = []
    for d in trading_days:
        if d in benchmark.index:
            bench_curve.append((float(benchmark.loc[d]['close']) / base_price - 1) * 100)
        else:
            bench_curve.append(bench_curve[-1] if bench_curve else 0)
    strat_curve = [(v - 1) * 100 for v in daily_navs]

    fig1, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(dates, strat_curve, color='#E63946', linewidth=2,
             label=f'策略 {strat_curve[-1]:+.1f}%')
    ax1.plot(dates, bench_curve, color='#6C757D', linewidth=1.5,
             linestyle='--', label=f'沪深300 {bench_curve[-1]:+.1f}%')
    ax1.axhline(y=0, color='black', linewidth=0.5, alpha=0.3)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.set_ylabel('累计收益率 (%)')
    ax1.set_title('净值曲线')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    fig1.autofmt_xdate(rotation=30)
    fig1.tight_layout()
    img_nav = chart_to_base64(fig1)

    # === 图2: 月度收益柱状图 ===
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    months = [r['buy_date'][:7] for r in results]
    s_rets = [r['strategy_return'] for r in results]
    b_rets = [r['benchmark_return'] for r in results]
    x = np.arange(len(months))
    w = 0.35
    ax2.bar(x - w/2, s_rets, w, label='策略', color='#E63946', alpha=0.8)
    ax2.bar(x + w/2, b_rets, w, label='沪深300', color='#6C757D', alpha=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels(months, rotation=45, ha='right', fontsize=8)
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.legend(fontsize=9)
    ax2.set_ylabel('收益率 (%)')
    ax2.set_title('月度收益对比')
    ax2.grid(True, alpha=0.2, axis='y')
    fig2.tight_layout()
    img_monthly = chart_to_base64(fig2)

    # === 构建月度明细表 HTML ===
    rows_html = ''
    for r in results:
        mode_cls = 'offensive' if r['mode'] == '进攻' else 'defensive'
        ret_cls = 'pos' if r['strategy_return'] > 0 else 'neg'
        exc_cls = 'pos' if r['excess_return'] > 0 else 'neg'
        contrib_strs = []
        for c in r.get('contribs', [])[:6]:
            sign = 'pos' if c['pnl'] > 0 else 'neg'
            raw_code = c['code'].rstrip('*')
            name = _name_map.get(raw_code, raw_code)
            sl = '止损' if c['code'].endswith('*') else ''
            contrib_strs.append(
                f"<span class='{sign}'>{name}{sl}({c['pnl']:+.1f}%)</span>")
        rows_html += f"""<tr>
<td>{r['buy_date']}</td><td>{r['sell_date']}</td>
<td class='{mode_cls}'>{r['mode']}</td>
<td class='{ret_cls}'>{r['strategy_return']:+.2f}%</td>
<td>{r['benchmark_return']:+.2f}%</td>
<td class='{exc_cls}'>{r['excess_return']:+.2f}%</td>
<td>{r['num_stocks']}</td>
<td class='contribs'>{' '.join(contrib_strs)}</td>
</tr>\n"""

    # === HTML模板 ===
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>回测报告 {results[0]['buy_date']} ~ {results[-1]['sell_date']}</title>
<style>
body {{ font-family: -apple-system, 'Microsoft YaHei', sans-serif;
       max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8f9fa; }}
h1 {{ color: #1a1a2e; border-bottom: 2px solid #E63946; padding-bottom: 10px; }}
h2 {{ color: #16213e; margin-top: 30px; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr);
            gap: 15px; margin: 20px 0; }}
.kpi {{ background: white; border-radius: 8px; padding: 20px;
       box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
.kpi .value {{ font-size: 24px; font-weight: bold; margin: 5px 0; }}
.kpi .label {{ font-size: 12px; color: #666; }}
.pos {{ color: #E63946; }} .neg {{ color: #2A9D8F; }}
.offensive {{ color: #E63946; font-weight: bold; }}
.defensive {{ color: #457B9D; font-weight: bold; }}
table {{ width: 100%; border-collapse: collapse; background: white;
        border-radius: 8px; overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
th {{ background: #1a1a2e; color: white; padding: 10px 8px;
     font-size: 13px; }}
td {{ padding: 8px; border-bottom: 1px solid #eee; font-size: 12px;
     text-align: center; }}
tr:hover {{ background: #f5f5f5; }}
.contribs {{ text-align: left; font-size: 11px; }}
img {{ width: 100%; border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 10px 0; }}
.footer {{ text-align: center; color: #999; margin-top: 30px;
          font-size: 12px; }}
</style></head><body>
<h1>MA60趋势择时策略 回测报告</h1>
<p>回测区间: {results[0]['buy_date']} ~ {results[-1]['sell_date']} |
   调仓周期: 月度 | 止损: -7%</p>"""

    html += f"""
<div class="kpi-grid">
<div class="kpi"><div class="label">策略累计收益</div>
  <div class="value pos">{(cum_strat-1)*100:+.1f}%</div></div>
<div class="kpi"><div class="label">年化收益</div>
  <div class="value">{ann_ret:+.1f}%</div></div>
<div class="kpi"><div class="label">最大回撤</div>
  <div class="value neg">{max_dd*100:.1f}%</div></div>
<div class="kpi"><div class="label">胜率</div>
  <div class="value">{win_rate:.0f}%</div></div>
<div class="kpi"><div class="label">基准收益(沪深300)</div>
  <div class="value">{(cum_bench-1)*100:+.1f}%</div></div>
<div class="kpi"><div class="label">超额收益</div>
  <div class="value pos">{(cum_strat-cum_bench)*100:+.1f}%</div></div>
<div class="kpi"><div class="label">调仓次数</div>
  <div class="value">{len(results)}</div></div>
<div class="kpi"><div class="label">总交易笔数</div>
  <div class="value">{total_trades}</div></div>
</div>

<h2>净值曲线</h2>
<img src="data:image/png;base64,{img_nav}">

<h2>月度收益对比</h2>
<img src="data:image/png;base64,{img_monthly}">

<h2>月度持仓明细与归因</h2>
<table>
<tr><th>买入</th><th>卖出</th><th>模式</th><th>策略</th>
<th>基准</th><th>超额</th><th>持仓</th><th>逐只归因</th></tr>
{rows_html}
</table>

"""

    # 本月持仓建议
    if recommendation and recommendation.get('picks'):
        rec = recommendation
        has_perf = any(p.get('return_pct') is not None for p in rec['picks'])
        if has_perf:
            track_date = next((p['track_date'] for p in rec['picks'] if p.get('track_date')), '')
            rec_rows = ''
            total_ret = 0
            cnt = 0
            for s in rec['picks']:
                ret_val = s.get('return_pct')
                if ret_val is not None:
                    ret_cls = 'pos' if ret_val > 0 else 'neg'
                    ret_str = f"<span class='{ret_cls}'>{ret_val:+.2f}%</span>"
                    cur_str = f"{s['current_price']:.2f}"
                    total_ret += ret_val
                    cnt += 1
                else:
                    ret_str = 'N/A'
                    cur_str = 'N/A'
                rec_rows += (f"<tr><td>{s['code']}</td><td>{s['name']}</td>"
                             f"<td>{s['price']:.2f}</td><td>{cur_str}</td>"
                             f"<td>{ret_str}</td></tr>\n")
            avg_ret = total_ret / cnt if cnt else 0
            avg_cls = 'pos' if avg_ret > 0 else 'neg'
            bench_ret = rec.get('bench_return')
            rec_rows += (f"<tr style='font-weight:bold;border-top:2px solid #333'>"
                         f"<td colspan='4'>等权平均</td>"
                         f"<td class='{avg_cls}'>{avg_ret:+.2f}%</td></tr>\n")
            if bench_ret is not None:
                bench_cls = 'pos' if bench_ret > 0 else 'neg'
                excess = avg_ret - bench_ret
                exc_cls = 'pos' if excess > 0 else 'neg'
                rec_rows += (f"<tr style='font-weight:bold'>"
                             f"<td colspan='4'>沪深300同期</td>"
                             f"<td class='{bench_cls}'>{bench_ret:+.2f}%</td></tr>\n")
                rec_rows += (f"<tr style='font-weight:bold'>"
                             f"<td colspan='4'>超额收益</td>"
                             f"<td class='{exc_cls}'>{excess:+.2f}%</td></tr>\n")
            html += f"""
<h2>本月持仓建议（{rec['month']}）— 实际表现</h2>
<p>选股基准日: {rec['date']} | 市场模式: <b>{rec['mode']}</b> | 止损: -7% | 截至: {track_date}</p>
<table>
<tr><th>代码</th><th>名称</th><th>买入价</th><th>现价</th><th>收益</th></tr>
{rec_rows}
</table>
"""
        else:
            rec_rows = ''
            for s in rec['picks']:
                rec_rows += (f"<tr><td>{s['code']}</td><td>{s['name']}</td>"
                             f"<td>{s['price']:.2f}</td><td>{s['score']:.0f}</td></tr>\n")
            html += f"""
<h2>本月持仓建议（{rec['month']}）</h2>
<p>选股基准日: {rec['date']} | 市场模式: <b>{rec['mode']}</b> | 止损: -7%</p>
<table>
<tr><th>代码</th><th>名称</th><th>价格</th><th>评分</th></tr>
{rec_rows}
</table>
"""

    html += f"""
<div class="footer">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</body></html>"""

    os.makedirs('./reports/backtest', exist_ok=True)
    out_path = f'./reports/backtest/backtest_{results[0]["buy_date"]}_{results[-1]["sell_date"]}.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"回测报告已生成: {out_path}")
    return out_path


def get_recommendation(daily_data, fin_data, benchmark, stock_codes, latest_day):
    """生成本月持仓建议数据"""
    import json

    name_map = {}
    with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
        for s in json.load(f)['stocks']:
            name_map[s['code']] = s['name']

    bull_mode = False
    mode_name = '防守'
    if latest_day in benchmark.index:
        loc = benchmark.index.get_loc(latest_day)
        if loc >= 60:
            ma60 = benchmark.iloc[loc-60:loc]['close'].mean()
            cur = float(benchmark.loc[latest_day]['close'])
            if cur > ma60 * 1.02:
                bull_mode = True
                mode_name = '进攻'
            elif cur < ma60 * 0.98:
                mode_name = '防守'
            else:
                mode_name = '缓冲带(维持上期)'

    all_stocks = []
    for code in stock_codes:
        sd = build_stock_data(code, daily_data, latest_day, fin_data)
        if sd:
            all_stocks.append(sd)

    if bull_mode:
        selected = select_stocks_offensive(all_stocks)
    else:
        selected = select_stocks_ultra_defensive(all_stocks)

    next_month = latest_day.month % 12 + 1
    next_year = latest_day.year + (1 if next_month == 1 else 0)
    month_str = f'{next_year}-{next_month:02d}'

    picks = []
    for s in selected:
        picks.append({
            'code': s['code'],
            'name': name_map.get(s['code'], s['code']),
            'price': s['price'],
            'score': s.get('strength_score', 0),
        })

    return {
        'month': month_str,
        'date': latest_day.strftime('%Y-%m-%d'),
        'mode': mode_name,
        'picks': picks,
    }


def track_recommendation_performance(rec, daily_data, benchmark):
    """追踪本月建议持仓从选股日到昨天的实际表现"""
    if not rec or not rec.get('picks'):
        return rec

    rec_date = datetime.strptime(rec['date'], '%Y-%m-%d')
    for pick in rec['picks']:
        code = pick['code']
        buy_price = pick['price']
        pick['current_price'] = None
        pick['return_pct'] = None
        pick['track_date'] = None

        if code not in daily_data:
            continue
        df = daily_data[code]
        future = df.index[df.index > rec_date]
        if len(future) == 0:
            continue
        latest = future[-1]
        cur_price = float(df.loc[latest]['收盘'])
        pick['current_price'] = cur_price
        pick['return_pct'] = (cur_price / buy_price - 1) * 100
        pick['track_date'] = latest.strftime('%Y-%m-%d')

    # 同期沪深300基准收益
    rec['bench_return'] = None
    track_date = next((p['track_date'] for p in rec['picks'] if p.get('track_date')), None)
    if track_date and benchmark is not None:
        td = pd.Timestamp(track_date)
        rd = pd.Timestamp(rec['date'])
        if rd in benchmark.index and td in benchmark.index:
            rec['bench_return'] = (float(benchmark.loc[td]['close']) /
                                   float(benchmark.loc[rd]['close']) - 1) * 100

    return rec


def print_recommendation(rec):
    """打印本月持仓建议"""
    print(f"\n{'='*60}")
    print(f"  本月持仓建议（{rec['month']}）")
    print(f"{'='*60}")
    print(f"  选股基准日: {rec['date']}")
    print(f"  市场模式: {rec['mode']}")
    print(f"  建议持仓数: {len(rec['picks'])}")
    print(f"  止损线: -7%")
    print(f"{'='*60}")
    if rec['picks']:
        has_perf = any(p.get('return_pct') is not None for p in rec['picks'])
        if has_perf:
            track_date = next((p['track_date'] for p in rec['picks'] if p.get('track_date')), '')
            print(f"  实际表现截至: {track_date}")
            print(f"\n{'代码':<10} {'名称':<10} {'买入价':>8} {'现价':>8} {'收益':>8}")
            print('-' * 50)
            total_ret = 0
            cnt = 0
            for s in rec['picks']:
                ret_str = f"{s['return_pct']:+.2f}%" if s.get('return_pct') is not None else 'N/A'
                cur_str = f"{s['current_price']:.2f}" if s.get('current_price') else 'N/A'
                print(f"{s['code']:<10} {s['name']:<10} "
                      f"{s['price']:>8.2f} {cur_str:>8} {ret_str:>8}")
                if s.get('return_pct') is not None:
                    total_ret += s['return_pct']
                    cnt += 1
            if cnt:
                avg_ret = total_ret / cnt
                bench_ret = rec.get('bench_return')
                bench_str = f"{bench_ret:+.2f}%" if bench_ret is not None else 'N/A'
                excess = avg_ret - bench_ret if bench_ret is not None else None
                excess_str = f"{excess:+.2f}%" if excess is not None else ''
                print(f"{'':40} {'等权平均':>8} {avg_ret:+.2f}%")
                print(f"{'':40} {'沪深300':>8} {bench_str:>8}")
                if excess is not None:
                    print(f"{'':40} {'超额收益':>8} {excess_str:>8}")
        else:
            print(f"\n{'代码':<10} {'名称':<10} {'价格':>8} {'评分':>6}")
            print('-' * 40)
            for s in rec['picks']:
                print(f"{s['code']:<10} {s['name']:<10} "
                      f"{s['price']:>8.2f} {s['score']:>6.1f}")
    else:
        print("  未选出符合条件的股票")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    run_backtest()
