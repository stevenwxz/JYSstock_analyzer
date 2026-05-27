"""回测配置"""

# 回测参数
BACKTEST_PARAMS = {
    'start_date': '2024-01-01',
    'end_date': '2026-05-25',
    'hold_days': 7,
    'cost_buy': 0.001,       # 买入成本 0.1%
    'cost_sell': 0.0015,     # 卖出成本 0.15%（含印花税）
    'cache_expire_days': 7,
}
