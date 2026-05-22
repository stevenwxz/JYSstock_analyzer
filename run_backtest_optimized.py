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
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from src.analysis.stock_filter import StockFilter
from config.config import STOCK_FILTER_CONFIG
from config.backtest_config import BACKTEST_PARAMS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    """批量获取所有股票日线数据"""
    def _fetch():
        all_data = {}
        total = len(stock_codes)
        failed_codes = []
        for i, code in enumerate(stock_codes):
            success = False
            for attempt in range(3):
                try:
                    df = ak.stock_zh_a_hist(
                        symbol=code, period='daily',
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust='qfq'
                    )
                    if not df.empty:
                        df['日期'] = pd.to_datetime(df['日期'])
                        df = df.set_index('日期')
                        all_data[code] = df
                        success = True
                        break
                except Exception:
                    time.sleep(2 * (attempt + 1))
            if not success:
                failed_codes.append(code)
            if (i + 1) % 50 == 0:
                logger.info(f"  日线数据: {i+1}/{total} (成功{len(all_data)})")
                time.sleep(5)
            else:
                time.sleep(1)
        if failed_codes:
            logger.warning(f"日线获取失败: {len(failed_codes)}只")
        logger.info(f"日线数据获取完成: {len(all_data)}/{total}")
        return all_data
    return load_or_fetch('daily_data', _fetch)


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

    # 20日动量
    loc = df.index.get_loc(trade_date)
    momentum_20d = 0
    if loc >= 20:
        price_20d_ago = float(df.iloc[loc - 20]['收盘'])
        momentum_20d = (price / price_20d_ago - 1) * 100

    # 换手率
    turnover_rate = float(row['换手率']) if '换手率' in row and pd.notna(row['换手率']) else 0

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
        'pe_ratio': pe_ratio,
        'pb_ratio': pb_ratio,
        'roe': fin.get('roe'),
        'profit_growth': fin.get('profit_growth'),
        'dividend_yield': None,
    }


# === PLACEHOLDER_BACKTEST_LOOP ===


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
    # 多取35天用于计算动量
    fetch_start = (datetime.strptime(start, '%Y-%m-%d') - timedelta(days=50)).strftime('%Y-%m-%d')
    daily_data = fetch_all_daily_data(stock_codes, fetch_start, end)

    logger.info("获取财报数据...")
    report_dates = ['20240930', '20241231', '20250331', '20250630', '20250930', '20251231']
    fin_data = fetch_financial_data(report_dates)

    logger.info("获取沪深300基准...")
    benchmark = fetch_benchmark()

    # 3. 生成交易日序列
    sample_code = next(iter(daily_data))
    all_trading_days = daily_data[sample_code].index
    mask = (all_trading_days >= start) & (all_trading_days <= end)
    trading_days = all_trading_days[mask].tolist()
    logger.info(f"交易日数: {len(trading_days)}")

    # 4. 回测循环
    stock_filter = StockFilter(config=STOCK_FILTER_CONFIG)
    results = []
    i = 0

    while i + hold_days < len(trading_days):
        buy_date = trading_days[i]
        sell_date = trading_days[i + hold_days]

        # 构建所有股票数据
        all_stocks = []
        for code in stock_codes:
            sd = build_stock_data(code, daily_data, buy_date, fin_data)
            if sd:
                all_stocks.append(sd)

        # 选股
        selected = stock_filter.select_top_stocks(all_stocks)

        # 计算收益
        period_returns = []
        for stock in selected:
            code = stock['code']
            if code in daily_data and sell_date in daily_data[code].index:
                sell_price = float(daily_data[code].loc[sell_date]['收盘'])
                buy_price = stock['price']
                raw_return = (sell_price / buy_price - 1)
                net_return = raw_return - cost_buy - cost_sell
                period_returns.append(net_return * 100)

        # 基准收益
        bench_ret = 0
        if buy_date in benchmark.index and sell_date in benchmark.index:
            bench_ret = (benchmark.loc[sell_date]['close'] / benchmark.loc[buy_date]['close'] - 1) * 100

        avg_ret = np.mean(period_returns) if period_returns else 0
        results.append({
            'buy_date': buy_date.strftime('%Y-%m-%d'),
            'sell_date': sell_date.strftime('%Y-%m-%d'),
            'strategy_return': avg_ret,
            'benchmark_return': bench_ret,
            'excess_return': avg_ret - bench_ret,
            'num_stocks': len(period_returns),
            'win_count': sum(1 for r in period_returns if r > 0),
        })

        i += hold_days

    # 5. 输出结果
    print_results(results)


# === PLACEHOLDER_PRINT ===


def print_results(results):
    """打印回测结果"""
    if not results:
        print("无回测结果")
        return

    strat_returns = [r['strategy_return'] for r in results]
    bench_returns = [r['benchmark_return'] for r in results]
    excess_returns = [r['excess_return'] for r in results]

    # 累计收益（复利）
    cum_strat = 1.0
    cum_bench = 1.0
    max_cum = 1.0
    max_drawdown = 0
    for r in results:
        cum_strat *= (1 + r['strategy_return'] / 100)
        cum_bench *= (1 + r['benchmark_return'] / 100)
        max_cum = max(max_cum, cum_strat)
        dd = (max_cum - cum_strat) / max_cum
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


if __name__ == '__main__':
    run_backtest()
