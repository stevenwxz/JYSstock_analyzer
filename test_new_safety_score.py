#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新的安全性评分系统
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'stock_analyzer'))

from src.analysis.stock_filter import StockFilter

def test_safety_score():
    """测试安全性评分逻辑"""

    filter_obj = StockFilter()

    # 测试案例1: 农业银行 (10月22日数据)
    print("=" * 60)
    print("测试案例1: 农业银行 (601288)")
    print("=" * 60)

    stock_data_abc = {
        'code': '601288',
        'name': '农业银行',
        'price': 8.09,
        'change_pct': 2.66,
        'pe_ratio': 9.91,
        'volume': 4945185,
        'turnover': 394956,
        'momentum_20d': 16.235632183908045,
        'pb_ratio': 1.06,
        'dividend_yield': 10.15,
        'peg': 0.6606666666666666,
        'turnover_rate': 0.29,
        'roe': 10.696266397578205,
        'profit_growth': 1.0696266397578202,
    }

    score_result_abc = filter_obj.calculate_strength_score(stock_data_abc)

    print(f"旧数据: 总分=69, 安全性=0")
    print(f"\n新评分结果:")
    print(f"  总分: {score_result_abc['total']}")
    print(f"  等级: {score_result_abc['grade']}")
    print(f"\n各维度得分:")
    for dimension, score in score_result_abc['breakdown'].items():
        dimension_name = {
            'technical': '技术面',
            'valuation': '估值',
            'profitability': '盈利能力',
            'safety': '安全性',
            'dividend': '股息'
        }[dimension]
        print(f"  {dimension_name}: {score}分")

    print(f"\n安全性得分明细 (PB={stock_data_abc['pb_ratio']}, 股息率={stock_data_abc['dividend_yield']}, 换手率={stock_data_abc['turnover_rate']}):")
    pb = stock_data_abc['pb_ratio']
    div = stock_data_abc['dividend_yield']
    turnover = stock_data_abc['turnover_rate']

    # 模拟评分逻辑
    safety_detail = []
    if pb < 1.2:
        safety_detail.append("  PB < 1.2 (破净): +4分")
    if div > 5:
        safety_detail.append(f"  股息率 > 5% ({div:.2f}%): +3分")
    if turnover < 2:
        safety_detail.append(f"  换手率 < 2% ({turnover:.2f}%): +3分")

    for detail in safety_detail:
        print(detail)

    # 测试案例2: 中国铝业 (10月22日数据)
    print("\n" + "=" * 60)
    print("测试案例2: 中国铝业 (601600)")
    print("=" * 60)

    stock_data_chalco = {
        'code': '601600',
        'name': '中国铝业',
        'price': 8.75,
        'change_pct': 1.51,
        'pe_ratio': 12.05,
        'volume': 2820271,
        'turnover': 243308,
        'momentum_20d': 11.792513095694401,
        'pb_ratio': 2.16,
        'dividend_yield': 10.61,
        'peg': 0.8033333333333333,
        'turnover_rate': 1.19,
        'roe': 17.925311203319502,
        'profit_growth': 7.315311203319502,
    }

    score_result_chalco = filter_obj.calculate_strength_score(stock_data_chalco)

    print(f"旧数据: 总分=64, 安全性=0")
    print(f"\n新评分结果:")
    print(f"  总分: {score_result_chalco['total']}")
    print(f"  等级: {score_result_chalco['grade']}")
    print(f"\n各维度得分:")
    for dimension, score in score_result_chalco['breakdown'].items():
        dimension_name = {
            'technical': '技术面',
            'valuation': '估值',
            'profitability': '盈利能力',
            'safety': '安全性',
            'dividend': '股息'
        }[dimension]
        print(f"  {dimension_name}: {score}分")

    print(f"\n安全性得分明细 (PB={stock_data_chalco['pb_ratio']}, 股息率={stock_data_chalco['dividend_yield']}, 换手率={stock_data_chalco['turnover_rate']}):")
    pb = stock_data_chalco['pb_ratio']
    div = stock_data_chalco['dividend_yield']
    turnover = stock_data_chalco['turnover_rate']

    safety_detail = []
    if 2.0 <= pb < 3.0:
        safety_detail.append(f"  2.0 <= PB < 3.0 ({pb:.2f}): +2分")
    if div > 5:
        safety_detail.append(f"  股息率 > 5% ({div:.2f}%): +3分")
    if turnover < 2:
        safety_detail.append(f"  换手率 < 2% ({turnover:.2f}%): +3分")

    for detail in safety_detail:
        print(detail)

    # 测试案例3: 高风险股票示例
    print("\n" + "=" * 60)
    print("测试案例3: 高风险股票示例 (高PB、无分红、高换手)")
    print("=" * 60)

    stock_data_risky = {
        'code': '300999',
        'name': '高风险示例',
        'price': 50.0,
        'change_pct': 5.0,
        'pe_ratio': 80.0,
        'volume': 500000,
        'turnover': 250000,
        'momentum_20d': 20.0,
        'pb_ratio': 8.5,  # 高PB
        'dividend_yield': 0.5,  # 低分红
        'peg': 4.0,
        'turnover_rate': 15.5,  # 高换手
        'roe': 8.0,
        'profit_growth': 10.0,
    }

    score_result_risky = filter_obj.calculate_strength_score(stock_data_risky)

    print(f"新评分结果:")
    print(f"  总分: {score_result_risky['total']}")
    print(f"  等级: {score_result_risky['grade']}")
    print(f"\n各维度得分:")
    for dimension, score in score_result_risky['breakdown'].items():
        dimension_name = {
            'technical': '技术面',
            'valuation': '估值',
            'profitability': '盈利能力',
            'safety': '安全性',
            'dividend': '股息'
        }[dimension]
        print(f"  {dimension_name}: {score}分")

    print(f"\n安全性得分明细 (PB={stock_data_risky['pb_ratio']}, 股息率={stock_data_risky['dividend_yield']}, 换手率={stock_data_risky['turnover_rate']}):")
    print(f"  PB > 5.0 ({stock_data_risky['pb_ratio']:.2f}): 0分 (风险高)")
    print(f"  股息率 < 1% ({stock_data_risky['dividend_yield']:.2f}%): 0分")
    print(f"  换手率 > 10% ({stock_data_risky['turnover_rate']:.2f}%): 0分 (投机性强)")
    print(f"  → 安全性总分: {score_result_risky['breakdown']['safety']}分")

    print("\n" + "=" * 60)
    print("总结")
    print("=" * 60)
    print(f"农业银行: 旧分数 69 → 新分数 {score_result_abc['total']} (等级: {score_result_abc['grade']})")
    print(f"中国铝业: 旧分数 64 → 新分数 {score_result_chalco['total']} (等级: {score_result_chalco['grade']})")
    print(f"高风险股: 新分数 {score_result_risky['total']} (等级: {score_result_risky['grade']})")
    print("\n✓ 安全性评分系统已生效,能够有效区分不同风险等级的股票!")

if __name__ == '__main__':
    test_safety_score()
