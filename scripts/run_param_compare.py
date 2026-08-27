#!/usr/bin/env python3
"""参数对比：周度/月度调仓 × 不同止损线"""
import sys, os, json, logging
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)

import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.backtest_config import BACKTEST_PARAMS
from scripts.run_backtest import (
    fetch_all_daily_data, fetch_financial_data, fetch_benchmark,
    build_stock_data, select_stocks_offensive, select_stocks_ultra_defensive
)

logging.basicConfig(level=logging.WARNING)


def run_single(daily_data, fin_data, benchmark, stock_codes, trading_days,
               rebal_mode='monthly', stop_loss=-0.05):
    """单次回测，返回 (累计收益, 最大回撤, 胜率)"""
    cost = 0.001 + 0.0015
    nav_base = 1.0
    holdings = []
    stopped = {}
    last_rebal_month = None
    last_rebal_week = None
    bull_mode = False
    daily_navs = []
    wins = 0
    trades = 0

    for i, today in enumerate(trading_days):
        # 判断是否调仓日
        if rebal_mode == 'monthly':
            is_rebal = (today.year, today.month) != last_rebal_month
        else:
            week_key = (today.year, today.isocalendar()[1])
            is_rebal = week_key != last_rebal_week

        if is_rebal:
            if holdings or stopped:
                port_return = 0
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        port_return += weight * ret
                        if ret > 0:
                            wins += 1
                        trades += 1
                cash_return = sum(stopped.values())
                active_weight = sum(w for _, _, w in holdings)
                rebal_cost = cost * active_weight if active_weight > 0 else 0
                nav_base = nav_base * (1 + port_return + cash_return) * (1 - rebal_cost)

            # MA60 ±2% 缓冲带
            if today in benchmark.index:
                loc = benchmark.index.get_loc(today)
                if loc >= 60:
                    ma60 = benchmark.iloc[loc-60:loc]['close'].mean()
                    cur = float(benchmark.loc[today]['close'])
                    if cur > ma60 * 1.02:
                        bull_mode = True
                    elif cur < ma60 * 0.98:
                        bull_mode = False

            all_stocks = []
            for code in stock_codes:
                sd = build_stock_data(code, daily_data, today, fin_data)
                if sd:
                    all_stocks.append(sd)

            if bull_mode:
                selected = select_stocks_offensive(all_stocks)
            else:
                selected = select_stocks_ultra_defensive(all_stocks)

            holdings = []
            stopped = {}
            if selected:
                w = 1.0 / len(selected)
                for s in selected:
                    holdings.append((s['code'], s['price'], w))

            last_rebal_month = (today.year, today.month)
            last_rebal_week = (today.year, today.isocalendar()[1])
            daily_navs.append(nav_base)
        else:
            if not holdings:
                daily_navs.append(nav_base)
            else:
                port_return = 0
                new_holdings = []
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        if stop_loss is not None and ret < stop_loss:
                            stopped[code] = weight * ret
                        else:
                            port_return += weight * ret
                            new_holdings.append((code, buy_price, weight))
                    else:
                        new_holdings.append((code, buy_price, weight))
                holdings = new_holdings
                cash_return = sum(stopped.values())
                daily_navs.append(nav_base * (1 + port_return + cash_return))

    # 计算最大回撤
    max_dd = 0
    peak = daily_navs[0] if daily_navs else 1
    for v in daily_navs:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak)

    cum_ret = (daily_navs[-1] - 1) * 100 if daily_navs else 0
    win_rate = wins / trades * 100 if trades else 0

    # 年化夏普比（无风险利率按2%）
    if len(daily_navs) > 1:
        daily_rets = [daily_navs[i]/daily_navs[i-1]-1 for i in range(1, len(daily_navs))]
        avg = np.mean(daily_rets)
        std = np.std(daily_rets)
        sharpe = (avg - 0.02/252) / std * np.sqrt(252) if std > 0 else 0
    else:
        sharpe = 0

    return cum_ret, max_dd * 100, win_rate, sharpe


if __name__ == '__main__':
    params = BACKTEST_PARAMS
    start = params['start_date']
    end = params['end_date']

    print("加载数据...")
    with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
        stock_codes = [s['code'] for s in json.load(f)['stocks']]

    fetch_start = (datetime.strptime(start, '%Y-%m-%d') - timedelta(days=50)).strftime('%Y-%m-%d')
    daily_data = fetch_all_daily_data(stock_codes, fetch_start, end)
    report_dates = ['20230630', '20230930', '20231231', '20240331', '20240630',
                    '20240930', '20241231', '20250331', '20250630', '20250930',
                    '20251231', '20260331', '20260630']
    fin_data = fetch_financial_data(report_dates)
    benchmark = fetch_benchmark()

    sample_code = next(iter(daily_data))
    all_days = daily_data[sample_code].index
    trading_days = all_days[(all_days >= start) & (all_days <= end)].tolist()

    # 参数组合
    rebal_modes = [('周度', 'weekly'), ('月度', 'monthly')]
    stop_losses = [
        ('无止损', None),
        ('-3%', -0.03),
        ('-5%', -0.05),
        ('-7%', -0.07),
        ('-10%', -0.10),
    ]

    print(f"\n回测区间: {start} ~ {end}")
    print(f"{'调仓':<6} {'止损':<8} {'累计收益':>10} {'最大回撤':>10} {'胜率':>8} {'夏普比':>8}")
    print('-' * 60)

    for rebal_name, rebal_mode in rebal_modes:
        for sl_name, sl_val in stop_losses:
            cum, dd, wr, sharpe = run_single(
                daily_data, fin_data, benchmark, stock_codes,
                trading_days, rebal_mode=rebal_mode, stop_loss=sl_val)
            print(f"{rebal_name:<6} {sl_name:<8} {cum:>+9.2f}% {dd:>9.2f}% {wr:>7.1f}% {sharpe:>7.2f}")

