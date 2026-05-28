#!/usr/bin/env python3
"""逐日净值曲线对比图"""
import sys, os, json, numpy as np, logging
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(key, None)
logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator
from datetime import datetime, timedelta
from run_backtest_optimized import (
    build_stock_data, fetch_all_daily_data,
    fetch_financial_data, fetch_benchmark,
    select_stocks_optimized,
    select_stocks_offensive, select_stocks_ultra_defensive
)

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
    csi300 = json.load(f)
stock_codes = [s['code'] for s in csi300['stocks']]

start = '2024-01-01'
end = '2026-05-25'
fetch_start = (datetime.strptime(start, '%Y-%m-%d') - timedelta(days=50)).strftime('%Y-%m-%d')
daily_data = fetch_all_daily_data(stock_codes, fetch_start, end)
fin_data = fetch_financial_data(['20230630','20230930','20231231','20240331','20240630','20240930','20241231','20250331','20250630','20250930','20251231'])
benchmark = fetch_benchmark()

sample_code = next(iter(daily_data))
all_days = daily_data[sample_code].index
trading_days = all_days[(all_days >= start) & (all_days <= end)].tolist()

hold_days = 7
cost = 0.001 + 0.0015
stop_loss_pct = -0.07

def simulate_daily(daily_data, fin_data, stock_codes, trading_days,
                   hold_days, use_stop_loss=True, use_overheat=True):
    """逐日模拟净值曲线"""
    nav_list = []
    nav_base = 1.0
    holdings = []  # [(code, buy_price, weight)]
    stopped = {}  # code -> 止损时的固定亏损
    cost = 0.001 + 0.0015

    i = 0
    while i < len(trading_days):
        today = trading_days[i]

        if i % hold_days == 0:
            if i > 0 and holdings:
                # 先计算旧持仓在今天的最终收益
                port_return = 0
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        if use_stop_loss and ret < stop_loss_pct:
                            port_return += weight * stop_loss_pct
                        else:
                            port_return += weight * ret
                    # 数据缺失的持仓不贡献收益
                cash_return = sum(stopped.values())
                nav_base = nav_base * (1 + port_return + cash_return)
                nav_base *= (1 - cost)

            # 选新股
            all_stocks = []
            for code in stock_codes:
                sd = build_stock_data(code, daily_data, today, fin_data)
                if sd:
                    all_stocks.append(sd)

            if use_overheat:
                selected = select_stocks_optimized(all_stocks)
            else:
                selected = select_stocks_optimized(all_stocks)

            holdings = []
            stopped = {}
            for s in selected:
                holdings.append((s['code'], s['price'], 1.0 / len(selected)))

            nav_list.append(nav_base)
        else:
            port_return = 0
            new_holdings = []
            for code, buy_price, weight in holdings:
                if code in daily_data and today in daily_data[code].index:
                    cur_price = float(daily_data[code].loc[today]['收盘'])
                    ret = cur_price / buy_price - 1
                    if use_stop_loss and ret < stop_loss_pct:
                        stopped[code] = weight * (stop_loss_pct - cost)
                    else:
                        port_return += weight * ret
                        new_holdings.append((code, buy_price, weight))
                else:
                    new_holdings.append((code, buy_price, weight))

            if use_stop_loss:
                holdings = new_holdings
            cash_return = sum(stopped.values())
            nav_list.append(nav_base * (1 + port_return + cash_return))

        i += 1

    return nav_list


def _score_offensive(s):
    """进攻模式评分：PE<30内选高动量+高增长，取消过热惩罚"""
    from run_backtest_optimized import score_stock_optimized
    # 取消过热惩罚
    orig_m5d = s.get('momentum_5d', 0)
    s['momentum_5d'] = 0
    base_score = score_stock_optimized(s)
    s['momentum_5d'] = orig_m5d

    # 高动量加分（取消惩罚后额外奖励）
    momentum = s.get('momentum_20d', 0)
    bonus = 0
    if momentum > 15:
        bonus += 12
    elif momentum > 10:
        bonus += 8
    elif momentum > 5:
        bonus += 4

    # 高增长加分
    growth = s.get('profit_growth')
    if growth and growth > 30:
        bonus += 5

    return base_score + bonus


def _select_offensive(all_stocks):
    """进攻模式选股：仍然PE<30，但优选高动量"""
    seen = set()
    unique = [s for s in all_stocks if s['code'] not in seen and not seen.add(s['code'])]
    filtered = [s for s in unique if s.get('pe_ratio') and 0 < s['pe_ratio'] <= 30]
    filtered = [s for s in filtered if s.get('change_pct', 0) > -9.8]
    for s in filtered:
        s['opt_score'] = _score_offensive(s)
    filtered = [s for s in filtered if s['opt_score'] >= 35]
    filtered.sort(key=lambda x: x['opt_score'], reverse=True)
    return filtered[:6]


def _score_ultra_defensive(s):
    """超防守评分：极低波动+低PB+高ROE"""
    score = 0
    volatility = s.get('volatility_20d', 0)
    pb = s.get('pb_ratio')
    roe = s.get('roe')
    max_dd = s.get('max_drawdown_20d', 0)
    momentum = s.get('momentum_20d', 0)

    # 低波动（30分）
    if volatility < 1.0:
        score += 30
    elif volatility < 1.5:
        score += 25
    elif volatility < 2.0:
        score += 18
    elif volatility < 2.5:
        score += 10

    # 低PB安全边际（25分）
    if pb and 0 < pb < 0.8:
        score += 25
    elif pb and 0.8 <= pb < 1.2:
        score += 20
    elif pb and 1.2 <= pb < 2.0:
        score += 12
    elif pb and 2.0 <= pb < 3.0:
        score += 5

    # 盈利质量（25分）
    if roe and roe > 15:
        score += 25
    elif roe and roe > 10:
        score += 18
    elif roe and roe > 7:
        score += 10

    # 小回撤（20分）
    if max_dd > -3:
        score += 20
    elif max_dd > -5:
        score += 14
    elif max_dd > -8:
        score += 7

    # 温和正动量加分（不要负动量的）
    if 0 < momentum <= 5:
        score += 5

    return score


def _select_ultra_defensive(all_stocks):
    """超防守选股：低波动低PB高ROE"""
    seen = set()
    unique = [s for s in all_stocks if s['code'] not in seen and not seen.add(s['code'])]
    filtered = [s for s in unique if s.get('pe_ratio') and 0 < s['pe_ratio'] <= 30]
    filtered = [s for s in filtered if s.get('change_pct', 0) > -9.8]
    for s in filtered:
        s['opt_score'] = _score_ultra_defensive(s)
    filtered = [s for s in filtered if s['opt_score'] >= 40]
    filtered.sort(key=lambda x: x['opt_score'], reverse=True)
    return filtered[:6]
    """进攻模式选股：仍然PE<30，但优选高动量"""
    seen = set()
    unique = [s for s in all_stocks if s['code'] not in seen and not seen.add(s['code'])]
    filtered = [s for s in unique if s.get('pe_ratio') and 0 < s['pe_ratio'] <= 30]
    filtered = [s for s in filtered if s.get('change_pct', 0) > -9.8]
    for s in filtered:
        s['opt_score'] = _score_offensive(s)
    filtered = [s for s in filtered if s['opt_score'] >= 35]
    filtered.sort(key=lambda x: x['opt_score'], reverse=True)
    return filtered[:6]


def simulate_low_drawdown(daily_data, fin_data, stock_codes, trading_days,
                          hold_days, benchmark, max_stocks=6, stop_loss=-0.05):
    """低回撤策略v3：牛市进攻满仓 + 熊市超防守满仓（不降仓位，靠选股抗跌）"""
    nav_list = []
    nav_base = 1.0
    holdings = []
    stopped = {}
    cost = 0.001 + 0.0015
    cur_stop = stop_loss

    i = 0
    while i < len(trading_days):
        today = trading_days[i]

        if i % hold_days == 0:
            if i > 0 and holdings:
                port_return = 0
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        if ret < cur_stop:
                            port_return += weight * cur_stop
                        else:
                            port_return += weight * ret
                cash_return = sum(stopped.values())
                nav_base = nav_base * (1 + port_return + cash_return)
                nav_base *= (1 - cost)

            # 趋势判断
            bull_mode = False
            if today in benchmark.index:
                loc = benchmark.index.get_loc(today)
                if loc >= 60:
                    ma60 = benchmark.iloc[loc-60:loc]['close'].mean()
                    cur = float(benchmark.loc[today]['close'])
                    bull_mode = cur > ma60

            all_stocks = []
            for code in stock_codes:
                sd = build_stock_data(code, daily_data, today, fin_data)
                if sd:
                    all_stocks.append(sd)

            if bull_mode:
                selected = select_stocks_offensive(all_stocks)[:max_stocks]
            else:
                selected = select_stocks_ultra_defensive(all_stocks)[:max_stocks]

            holdings = []
            stopped = {}
            if selected:
                for s in selected:
                    holdings.append((s['code'], s['price'], 1.0/len(selected)))
            nav_list.append(nav_base)
        else:
            if not holdings:
                nav_list.append(nav_base)
            else:
                port_return = 0
                new_holdings = []
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        if ret < cur_stop:
                            stopped[code] = weight * (cur_stop - cost)
                        else:
                            port_return += weight * ret
                            new_holdings.append((code, buy_price, weight))
                    else:
                        new_holdings.append((code, buy_price, weight))
                holdings = new_holdings
                cash_return = sum(stopped.values())
                nav_list.append(nav_base * (1 + port_return + cash_return))

        i += 1

    return nav_list


def simulate_trend_timing(daily_data, fin_data, stock_codes, trading_days,
                          hold_days, benchmark):
    """趋势择时策略：基准站上MA60进攻，跌破MA60防守"""
    nav_list = []
    nav_base = 1.0
    holdings = []
    stopped = {}
    cost = 0.001 + 0.0015
    cur_stop = stop_loss_pct

    i = 0
    while i < len(trading_days):
        today = trading_days[i]

        if i % hold_days == 0:
            if i > 0 and holdings:
                port_return = 0
                for code, buy_price, weight in holdings:
                    if code in daily_data and today in daily_data[code].index:
                        cur_price = float(daily_data[code].loc[today]['收盘'])
                        ret = cur_price / buy_price - 1
                        if ret < cur_stop:
                            port_return += weight * cur_stop
                        else:
                            port_return += weight * ret
                cash_return = sum(stopped.values())
                nav_base = nav_base * (1 + port_return + cash_return)
                nav_base *= (1 - cost)

            bull_mode = False
            if today in benchmark.index:
                loc = benchmark.index.get_loc(today)
                if loc >= 60:
                    ma60 = benchmark.iloc[loc-60:loc]['close'].mean()
                    cur = float(benchmark.loc[today]['close'])
                    bull_mode = cur > ma60

            cur_stop = stop_loss_pct

            all_stocks = []
            for code in stock_codes:
                sd = build_stock_data(code, daily_data, today, fin_data)
                if sd:
                    all_stocks.append(sd)

            if bull_mode:
                selected = _select_offensive(all_stocks)
            else:
                selected = select_stocks_optimized(all_stocks)

            holdings = []
            stopped = {}
            for s in selected:
                holdings.append((s['code'], s['price'], 1.0 / len(selected)))
            nav_list.append(nav_base)
        else:
            port_return = 0
            new_holdings = []
            for code, buy_price, weight in holdings:
                if code in daily_data and today in daily_data[code].index:
                    cur_price = float(daily_data[code].loc[today]['收盘'])
                    ret = cur_price / buy_price - 1
                    if ret < cur_stop:
                        stopped[code] = weight * (cur_stop - cost)
                    else:
                        port_return += weight * ret
                        new_holdings.append((code, buy_price, weight))
                else:
                    new_holdings.append((code, buy_price, weight))
            holdings = new_holdings
            cash_return = sum(stopped.values())
            nav_list.append(nav_base * (1 + port_return + cash_return))

        i += 1

    return nav_list


# === 运行模拟：对比不同止损率 ===
stop_losses = [-0.05, -0.07, -0.10]
nav_results = {}
for sl in stop_losses:
    print(f"模拟: 低回撤平衡 - 止损{sl*100:.0f}%...")
    nav_results[sl] = simulate_low_drawdown(daily_data, fin_data, stock_codes,
                                            trading_days, hold_days, benchmark,
                                            stop_loss=sl)

# 基准逐日净值
bench_nav = []
if trading_days[0] in benchmark.index:
    base_price = float(benchmark.loc[trading_days[0]]['close'])
    for d in trading_days:
        if d in benchmark.index:
            bench_nav.append(float(benchmark.loc[d]['close']) / base_price)
        else:
            bench_nav.append(bench_nav[-1] if bench_nav else 1.0)
else:
    bench_nav = [1.0] * len(trading_days)

# === 绘图：止损率对比 ===
def calc_dd(nav):
    peak = nav[0]
    max_dd = 0
    for v in nav:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak)
    return max_dd * 100

dates = [d.to_pydatetime() if hasattr(d, 'to_pydatetime') else d for d in trading_days]
fig, ax = plt.subplots(figsize=(14, 7))

colors = {-0.05: '#E63946', -0.07: '#2A9D8F', -0.10: '#457B9D'}
for sl in stop_losses:
    nav = nav_results[sl]
    dd = calc_dd(nav)
    ax.plot(dates, [(v-1)*100 for v in nav], color=colors[sl],
            linewidth=2.2,
            label=f'止损{sl*100:.0f}% {(nav[-1]-1)*100:+.1f}% (回撤{dd:.1f}%)')

ax.plot(dates, [(v-1)*100 for v in bench_nav], color='#6C757D',
        linewidth=1.8, linestyle='--',
        label=f'沪深300 {(bench_nav[-1]-1)*100:+.1f}%')

ax.axhline(y=0, color='black', linewidth=0.5, alpha=0.3)
ax.set_xlabel('日期', fontsize=11)
ax.set_ylabel('累计收益率 (%)', fontsize=11)
ax.set_title('止损率对比：-5% vs -7% vs -10%（低回撤平衡策略 2024-2026）',
             fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle='-')
ax.xaxis.set_major_locator(MonthLocator())
ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
out_path = './reports/charts/daily_curve.png'
os.makedirs('./reports/charts', exist_ok=True)
plt.savefig(out_path, dpi=150, bbox_inches='tight')
print(f"\n图表已保存: {out_path}")
print(f"数据点数: {len(trading_days)}个交易日")
print(f"--- 止损率对比 ---")
for sl in stop_losses:
    nav = nav_results[sl]
    dd = calc_dd(nav)
    print(f"止损{sl*100:.0f}%: {(nav[-1]-1)*100:+.2f}% | 最大回撤 {dd:.1f}%")
print(f"沪深300: {(bench_nav[-1]-1)*100:+.2f}%")
