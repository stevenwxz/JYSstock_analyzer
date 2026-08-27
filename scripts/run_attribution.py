#!/usr/bin/env python3
"""逐月涨跌归因分析"""
import sys, os, json, pickle
import pandas as pd
import numpy as np
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ['NO_PROXY'] = '*'
for k in ['HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy']:
    os.environ.pop(k, None)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))
from run_backtest import (
    fetch_benchmark, build_stock_data,
    select_stocks_offensive, select_stocks_ultra_defensive
)

with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
    stock_codes = [s['code'] for s in json.load(f)['stocks']]

with open('./cache/backtest/daily_data.pkl', 'rb') as f:
    daily_data = pickle.load(f)
with open('./cache/backtest/financial_data.pkl', 'rb') as f:
    fin_data = pickle.load(f)

benchmark = fetch_benchmark()

sample_code = next(iter(daily_data))
all_days = daily_data[sample_code].index
mask = (all_days >= '2024-01-01') & (all_days <= '2026-05-25')
trading_days = all_days[mask].tolist()

stop_loss_pct = -0.07
cost = 0.0025
nav = 1.0
holdings = []
stopped = {}
last_month = None
rebal_idx = 0
bull_mode = False
was_bull = False

header = f"{'月份':<10} {'模式':<6} {'策略':>7} {'基准':>7} {'超额':>7} | 持仓归因"
print(header)
print('-' * 105)

for i, today in enumerate(trading_days):
    is_rebal = (today.year, today.month) != last_month

    if is_rebal:
        if last_month is not None and (holdings or stopped):
            contribs = []
            for code, bp, w in holdings:
                if code in daily_data and today in daily_data[code].index:
                    cp = float(daily_data[code].loc[today]['收盘'])
                    contribs.append((code, (cp/bp - 1)*w*100))
                else:
                    contribs.append((code, 0))
            for code, locked in stopped.items():
                contribs.append((code + '*', locked * 100))

            period_ret = sum(c[1] for c in contribs) / 100
            nav = nav * (1 + period_ret) * (1 - cost)
            strat_pct = ((1 + period_ret) * (1 - cost) - 1) * 100

            bd = trading_days[rebal_idx]
            bench_pct = 0
            if bd in benchmark.index and today in benchmark.index:
                bench_pct = (benchmark.loc[today]['close'] / benchmark.loc[bd]['close'] - 1) * 100

            mode_str = '进攻' if was_bull else '防守'
            month_str = f'{last_month[0]}-{last_month[1]:02d}'
            contribs.sort(key=lambda x: x[1], reverse=True)
            contrib_str = ' '.join(f'{c[0]}({c[1]:+.1f}%)' for c in contribs)
            print(f'{month_str:<10} {mode_str:<6} {strat_pct:>+6.2f}% {bench_pct:>+6.2f}% {strat_pct:>+6.2f}% | {contrib_str}'.replace(f'{strat_pct:>+6.2f}% |', f'{strat_pct - bench_pct:>+6.2f}% |'))

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

        all_stocks = [build_stock_data(c, daily_data, today, fin_data) for c in stock_codes]
        all_stocks = [s for s in all_stocks if s]
        selected = select_stocks_offensive(all_stocks) if bull_mode else select_stocks_ultra_defensive(all_stocks)
        holdings = [(s['code'], s['price'], 1.0/len(selected)) for s in selected] if selected else []
        stopped = {}
        was_bull = bull_mode
        last_month = (today.year, today.month)
        rebal_idx = i
    else:
        new_h = []
        for code, bp, w in holdings:
            if code in daily_data and today in daily_data[code].index:
                cp = float(daily_data[code].loc[today]['收盘'])
                if cp/bp - 1 < stop_loss_pct:
                    stopped[code] = w * (cp/bp - 1 - cost)
                else:
                    new_h.append((code, bp, w))
            else:
                new_h.append((code, bp, w))
        holdings = new_h

print(f'\n最终净值: {nav:.4f} | 累计收益: {(nav-1)*100:+.2f}%')
