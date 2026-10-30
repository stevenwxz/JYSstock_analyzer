# -*- coding: utf-8 -*-
"""纯指标计算函数，供同步/异步数据获取器共用，避免逻辑重复。

这些函数不依赖网络和实例状态，可独立单元测试。
"""
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_momentum(price_data: pd.DataFrame, days: int = 20) -> float:
    """计算价格动量指标 (最新价 / days天前价 - 1) * 100

    Args:
        price_data: 含 close 列的 DataFrame，按日期升序排列
        days: 回看天数

    Returns:
        动量百分比，数据不足或异常时返回 0
    """
    if price_data is None or len(price_data) < days:
        return 0

    try:
        recent_prices = price_data['close'].tail(days)
        if len(recent_prices) < days:
            return 0
        momentum = (recent_prices.iloc[-1] / recent_prices.iloc[0] - 1) * 100
        return float(momentum)
    except Exception as e:
        logger.debug(f"计算动量指标失败: {e}")
        return 0


def calculate_financial_health(pb: Optional[float],
                               div_yield: Optional[float],
                               pe: Optional[float],
                               turnover: Optional[float]) -> int:
    """基于有限数据计算财务健康度评分 (0-100)

    纯函数，结果只取决于输入参数，与数据来源无关。
    """
    score = 50  # 基础分50分

    try:
        # PB评分 (±20分)
        if pb:
            if pb < 1:  # 破净
                score += 20
            elif pb < 2:  # 低估
                score += 10
            elif pb > 10:  # 极度高估
                score -= 20
            elif pb > 5:  # 高估
                score -= 10

        # 股息率评分 (±15分)
        if div_yield:
            if div_yield > 5:
                score += 15
            elif div_yield > 3:
                score += 10
            elif div_yield > 2:
                score += 5
            elif div_yield < 1:
                score -= 5

        # PE评分 (±10分)
        if pe:
            if 10 < pe < 20:  # 合理区间
                score += 10
            elif 20 <= pe < 30:
                score += 5
            elif pe >= 50:  # 过高
                score -= 10

        # 换手率评分 (±5分)
        if turnover:
            if 1 < turnover < 5:  # 适中
                score += 5
            elif turnover > 20:  # 过度投机
                score -= 5

    except Exception as e:
        logger.debug(f"计算财务健康度失败: {e}")

    return max(0, min(100, score))  # 限制在0-100之间
