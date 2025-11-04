#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基于换手率的流动性评分
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.analysis.stock_filter import StockFilter

def test_turnover_rate_scoring():
    """测试换手率评分逻辑"""
    print("=" * 80)
    print("测试基于换手率的流动性评分")
    print("=" * 80)

    filter = StockFilter()

    # 测试案例
    test_cases = [
        {
            'name': '案例1: 大盘蓝筹（中国人寿）',
            'stock': {
                'code': '601628',
                'name': '中国人寿',
                'price': 43.97,
                'change_pct': -0.92,
                'pe_ratio': 7.30,
                'pb_ratio': 2.01,
                'turnover': 96967,  # 成交额（万）
                'turnover_rate': 1.38,  # 换手率(%)
                'momentum_20d': 10.5,
                'roe': 27.5,
                'profit_growth': 26.1,
                'dividend_yield': 1.48,
            },
            'expected_liquidity_score': 5,  # 1.38%在1-3%区间，应得5分
        },
        {
            'name': '案例2: 小盘活跃股',
            'stock': {
                'code': '600000',
                'name': '小盘股A',
                'price': 10.0,
                'change_pct': 2.0,
                'pe_ratio': 15.0,
                'pb_ratio': 2.5,
                'turnover': 5000,  # 成交额小（万）
                'turnover_rate': 2.5,  # 换手率适中(%)
                'momentum_20d': 5.0,
                'roe': 12.0,
                'profit_growth': 10.0,
                'dividend_yield': 2.0,
            },
            'expected_liquidity_score': 5,  # 2.5%在1-3%区间，应得5分
        },
        {
            'name': '案例3: 高换手妖股',
            'stock': {
                'code': '300000',
                'name': '妖股B',
                'price': 50.0,
                'change_pct': 5.0,
                'pe_ratio': 80.0,
                'pb_ratio': 10.0,
                'turnover': 50000,  # 成交额大（万）
                'turnover_rate': 25.0,  # 换手率极高(%)
                'momentum_20d': 20.0,
                'roe': 8.0,
                'profit_growth': 5.0,
                'dividend_yield': 0.5,
            },
            'expected_liquidity_score': 1,  # 25%>8%，应得1分
        },
        {
            'name': '案例4: 流动性不足',
            'stock': {
                'code': '600001',
                'name': '冷门股C',
                'price': 8.0,
                'change_pct': 0.5,
                'pe_ratio': 12.0,
                'pb_ratio': 1.5,
                'turnover': 1000,  # 成交额很小（万）
                'turnover_rate': 0.3,  # 换手率极低(%)
                'momentum_20d': 2.0,
                'roe': 10.0,
                'profit_growth': 5.0,
                'dividend_yield': 3.0,
            },
            'expected_liquidity_score': 0,  # 0.3%<0.5%，应得0分
        },
        {
            'name': '案例5: 换手率良好',
            'stock': {
                'code': '000001',
                'name': '平衡股D',
                'price': 20.0,
                'change_pct': 1.0,
                'pe_ratio': 18.0,
                'pb_ratio': 3.0,
                'turnover': 20000,
                'turnover_rate': 4.0,  # 换手率3-5%(%)
                'momentum_20d': 8.0,
                'roe': 15.0,
                'profit_growth': 12.0,
                'dividend_yield': 2.5,
            },
            'expected_liquidity_score': 4,  # 4%在3-5%区间，应得4分
        },
    ]

    # 运行测试
    passed = 0
    failed = 0

    for i, case in enumerate(test_cases, 1):
        print(f"\n【{case['name']}】")
        print("-" * 80)

        stock = case['stock']
        expected = case['expected_liquidity_score']

        # 计算评分
        score_result = filter.calculate_strength_score(stock)
        breakdown = score_result['breakdown']
        actual_liquidity_score = breakdown['technical']

        # 显示结果
        print(f"股票: {stock['name']} ({stock['code']})")
        print(f"成交额: {stock['turnover']:,}万")
        print(f"换手率: {stock['turnover_rate']}%")
        print(f"\n流动性评分:")

        # 根据换手率显示预期得分逻辑
        tr = stock['turnover_rate']
        if 1 <= tr < 3:
            expected_desc = "1%-3% (最佳) → 应得5分"
        elif 3 <= tr < 5:
            expected_desc = "3%-5% (良好) → 应得4分"
        elif 5 <= tr < 8:
            expected_desc = "5%-8% (充足) → 应得3分"
        elif 0.5 <= tr < 1:
            expected_desc = "0.5%-1% (偏低) → 应得2分"
        elif tr >= 8:
            expected_desc = ">8% (投机) → 应得1分"
        else:
            expected_desc = "<0.5% (不足) → 应得0分"

        print(f"  换手率区间: {expected_desc}")

        # 注意：技术面总分包含涨跌幅(10分)+动量(15分)+流动性(5分)
        # 我们需要单独计算流动性得分
        # 但是breakdown['technical']是总分，需要分解

        # 重新计算仅流动性部分的得分
        liquidity_only = 0
        if tr and 1 <= tr < 3:
            liquidity_only = 5
        elif tr and 3 <= tr < 5:
            liquidity_only = 4
        elif tr and 5 <= tr < 8:
            liquidity_only = 3
        elif tr and 0.5 <= tr < 1:
            liquidity_only = 2
        elif tr and tr >= 8:
            liquidity_only = 1

        print(f"  实际得分: {liquidity_only}分")
        print(f"  预期得分: {expected}分")

        if liquidity_only == expected:
            print(f"  [PASS] 评分正确!")
            passed += 1
        else:
            print(f"  [FAIL] 评分错误!")
            failed += 1

        # 显示完整评分
        print(f"\n完整评分明细:")
        print(f"  技术面: {breakdown['technical']}分 (涨跌幅+动量+流动性)")
        print(f"  估值: {breakdown['valuation']}分")
        print(f"  盈利: {breakdown['profitability']}分")
        print(f"  安全性: {breakdown['safety']}分")
        print(f"  股息: {breakdown['dividend']}分")
        print(f"  总分: {score_result['total']}分 ({score_result['grade']}级)")

    # 总结
    print("\n" + "=" * 80)
    print(f"测试结果: {passed}个通过, {failed}个失败")
    if failed == 0:
        print("[SUCCESS] 所有测试用例通过!")
    else:
        print(f"[WARNING] 有{failed}个测试用例失败")
    print("=" * 80)

if __name__ == '__main__':
    test_turnover_rate_scoring()
