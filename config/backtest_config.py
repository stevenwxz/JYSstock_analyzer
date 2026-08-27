"""回测配置"""
from datetime import date

# 动态计算上月最后一天
_today = date.today()
_last_month_end = _today.replace(day=1)  # 本月1号
from datetime import timedelta
_last_month_end = (_last_month_end - timedelta(days=1)).strftime('%Y-%m-%d')

# 回测参数
BACKTEST_PARAMS = {
    'start_date': '2024-01-01',
    'end_date': _last_month_end,
    'hold_days': 7,
    'cost_buy': 0.001,       # 买入成本 0.1%
    'cost_sell': 0.0015,     # 卖出成本 0.15%（含印花税）
    'cache_expire_days': 7,
}
