#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动配置的股息率数据

当API返回的股息率数据不准确时，可以在这里手动配置正确的股息率
数据来源：各公司财报、公告、东方财富等

格式：
{
    '股票代码': {
        'dividend_yield': 股息率(%),
        'dividend_per_share': 每股股息(元),
        'year': 年份,
        'note': '备注'
    }
}
"""

# 手动配置的股息率数据
DIVIDEND_OVERRIDE = {
    # 中国人寿 (601628)
    # 2024年全年派息0.65元/股（含税）
    # 当前股价约44元，实际股息率约1.48%
    '601628': {
        'dividend_yield': 1.48,  # 实际股息率 1.48%
        'dividend_per_share': 0.65,  # 2024年全年派息
        'year': 2024,
        'note': '2024年派息：中期+末期共0.65元/股，股价44元计算'
    },

    # 新华保险 (601336)
    # 可以根据实际情况补充其他股票
    # '601336': {
    #     'dividend_yield': 2.0,
    #     'dividend_per_share': 1.35,
    #     'year': 2024,
    #     'note': '待确认'
    # },

    # 更多股票可以在这里添加...
}


def get_manual_dividend_yield(stock_code: str) -> float:
    """
    获取手动配置的股息率

    Args:
        stock_code: 股票代码

    Returns:
        股息率(%)，如果没有配置则返回None
    """
    if stock_code in DIVIDEND_OVERRIDE:
        return DIVIDEND_OVERRIDE[stock_code]['dividend_yield']
    return None


def get_dividend_info(stock_code: str) -> dict:
    """
    获取完整的股息信息

    Args:
        stock_code: 股票代码

    Returns:
        股息信息字典，如果没有配置则返回None
    """
    return DIVIDEND_OVERRIDE.get(stock_code, None)


def has_manual_override(stock_code: str) -> bool:
    """
    检查是否有手动配置的股息率

    Args:
        stock_code: 股票代码

    Returns:
        True如果有手动配置，否则False
    """
    return stock_code in DIVIDEND_OVERRIDE
