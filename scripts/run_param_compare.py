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
    """单次回测，返回 (累计收益, 最大回撤, 胜率, 夏普比)

    净值模型与主回测 run_backtest.py 一致：现金 + 持仓份额，逐日累积净值，
    止损按触发价卖出变现，调仓日结算剩余持仓并统计胜率。
    """
    cost_buy = 0.001
    cost_sell = 0.0015
    cash = 1.0
    holdings = []   # [(code, buy_price, shares)]
    stopped = []    # 本周期止损记录 [(code, buy_price, sell_price)]
    last_prices = {}
    last_rebal_month = None
    last_rebal_week = None
    bull_mode = False
    daily_navs = []
    wins = 0
    trades = 0

    def _nav():
        return cash + sum(shares * last_prices.get(code, buy_price)
                          for code, buy_price, shares in holdings)

    for today in trading_days:
        if rebal_mode == 'monthly':
            is_rebal = (today.year, today.month) != last_rebal_month
        else:
            week_key = (today.year, today.isocalendar()[1])
            is_rebal = week_key != last_rebal_week

        # 每日止损检查（调仓日也先检查止损）
        new_holdings = []
        for code, buy_price, shares in holdings:
            if code in daily_data and today in daily_data[code].index:
                cur_price = float(daily_data[code].loc[today]['收盘'])
                last_prices[code] = cur_price
                if stop_loss is not None and (cur_price / buy_price - 1) < stop_loss:
                    cash += shares * cur_price * (1 - cost_sell)
                    stopped.append((code, buy_price, cur_price))
                else:
                    new_holdings.append((code, buy_price, shares))
            else:
                new_holdings.append((code, buy_price, shares))
        holdings = new_holdings

        if is_rebal:
            # 结算上一周期：统计胜率 + 卖出剩余持仓
            if last_rebal_month is not None or last_rebal_week is not None:
                for code, buy_price, shares in holdings:
                    cur_price = last_prices.get(code, buy_price)
                    cash += shares * cur_price * (1 - cost_sell)
                    trades += 1
                    if cur_price / buy_price - 1 > 0:
                        wins += 1
                # 止损股：已止损变现，止损时 ret 必为负，仅计入 trades 不计 wins
                for code, buy_price, sell_price in stopped:
                    trades += 1
                    if sell_price / buy_price - 1 > 0:
                        wins += 1
                holdings = []
                stopped = []

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

            if selected:
                allocation = cash * (1 - cost_buy) / len(selected)
                cash -= allocation * len(selected) / (1 - cost_buy)
                for s in selected:
                    holdings.append((s['code'], s['price'], allocation / s['price']))
                    last_prices[s['code']] = s['price']
                cash = 0.0

            last_rebal_month = (today.year, today.month)
            last_rebal_week = (today.year, today.isocalendar()[1])
            daily_navs.append(_nav())
        else:
            daily_navs.append(_nav())

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

    # 支持 --pool-compare 模式：对比 CSI300 vs CSI800
    pool_compare = '--pool-compare' in sys.argv

    if pool_compare:
        pools = []
        if os.path.exists('./data/csi300_stocks.json'):
            with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
                pools.append(('CSI300', [s['code'] for s in json.load(f)['stocks']]))
        if os.path.exists('./data/csi800_stocks.json'):
            with open('./data/csi800_stocks.json', 'r', encoding='utf-8') as f:
                pools.append(('CSI800', [s['code'] for s in json.load(f)['stocks']]))

        if len(pools) < 2:
            print("需要同时存在 csi300_stocks.json 和 csi800_stocks.json")
            sys.exit(1)

        print(f"回测区间: {start} ~ {end}")
        print(f"参数: 月度调仓, -7%止损")
        print(f"\n{'股票池':<10} {'只数':>6} {'累计收益':>10} {'最大回撤':>10} {'胜率':>8} {'夏普比':>8}")
        print('-' * 62)

        fetch_start = (datetime.strptime(start, '%Y-%m-%d') - timedelta(days=50)).strftime('%Y-%m-%d')
        report_dates = ['20230630', '20230930', '20231231', '20240331', '20240630',
                        '20240930', '20241231', '20250331', '20250630', '20250930',
                        '20251231', '20260331', '20260630']
        fin_data = fetch_financial_data(report_dates)

        for pool_name, codes in pools:
            print(f"\n加载 {pool_name} 数据({len(codes)}只)...")
            pool_key = pool_name.replace('CSI', '')
            benchmark = fetch_benchmark(pool_key)
            dd = fetch_all_daily_data(codes, fetch_start, end, pool_tag=pool_key)
            sample_code = next(iter(dd))
            all_days = dd[sample_code].index
            trading_days = all_days[(all_days >= start) & (all_days <= end)].tolist()

            cum, mdd, wr, sharpe = run_single(
                dd, fin_data, benchmark, codes,
                trading_days, rebal_mode='monthly', stop_loss=-0.07)
            print(f"{pool_name:<10} {len(codes):>6} {cum:>+9.2f}% {mdd:>9.2f}% {wr:>7.1f}% {sharpe:>7.2f}")

    else:
        print("加载数据...")
        _stock_file = './data/csi300_stocks.json' if os.path.exists('./data/csi300_stocks.json') else './data/csi800_stocks.json'
        with open(_stock_file, 'r', encoding='utf-8') as f:
            stock_codes = [s['code'] for s in json.load(f)['stocks']]

        fetch_start = (datetime.strptime(start, '%Y-%m-%d') - timedelta(days=50)).strftime('%Y-%m-%d')
        daily_data = fetch_all_daily_data(stock_codes, fetch_start, end, pool_tag='300')
        report_dates = ['20230630', '20230930', '20231231', '20240331', '20240630',
                        '20240930', '20241231', '20250331', '20250630', '20250930',
                        '20251231', '20260331', '20260630']
        fin_data = fetch_financial_data(report_dates)
        benchmark = fetch_benchmark('300')

        sample_code = next(iter(daily_data))
        all_days = daily_data[sample_code].index
        trading_days = all_days[(all_days >= start) & (all_days <= end)].tolist()

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

