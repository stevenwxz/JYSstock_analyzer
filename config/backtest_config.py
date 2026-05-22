"""回测配置 - 与实盘筛选逻辑完全一致"""

from config.config import STOCK_FILTER_CONFIG

# 回测使用与实盘完全相同的筛选参数
BACKTEST_FILTER_CONFIG = STOCK_FILTER_CONFIG.copy()

# 回测参数
BACKTEST_PARAMS = {
    'start_date': '2025-05-01',
    'end_date': '2026-05-01',
    'hold_days': 5,
    'cost_buy': 0.001,       # 买入成本 0.1%
    'cost_sell': 0.0015,     # 卖出成本 0.15%（含印花税）
    'cache_expire_days': 7,
}
