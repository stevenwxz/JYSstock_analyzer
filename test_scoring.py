#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的评分系统
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.analysis.stock_filter import StockFilter

def test_scoring_system():
    """测试评分系统"""
    print("=" * 80)
    print("测试方案I - 新的评分系统")
    print("=" * 80)

    filter = StockFilter()

    # 测试案例1: 低估值价值股
    print("\n【案例1】低估值价值股")
    print("-" * 80)
    stock1 = {
        'code': '600000',
        'name': '浦发银行',
        'price': 8.5,
        'change_pct': 1.2,
        'pe_ratio': 5.5,      # PE < 10
        'pb_ratio': 0.6,      # PB < 1 (破净)
        'peg': 0.8,
        'turnover': 50000,
        'momentum_20d': 3.5,
        'roe': 10.9,          # ROE = PB/PE = 0.6/5.5*100
        'profit_growth': 8.5,
        'dividend_yield': 5.2,  # 高分红
        'turnover_rate': 1.5,   # 低换手
    }

    score1 = filter.calculate_strength_score(stock1)
    print_score_detail(stock1, score1)

    # 测试案例2: 成长股
    print("\n【案例2】成长股")
    print("-" * 80)
    stock2 = {
        'code': '300750',
        'name': '宁德时代',
        'price': 180,
        'change_pct': 2.5,
        'pe_ratio': 25,       # PE 20-30
        'pb_ratio': 6.0,      # PB 4-7
        'peg': 1.2,
        'turnover': 200000,
        'momentum_20d': 15.2,
        'roe': 24.0,          # 高ROE
        'profit_growth': 35.0, # 高成长
        'dividend_yield': 0.5, # 低分红
        'turnover_rate': 8.5,  # 换手偏高
    }

    score2 = filter.calculate_strength_score(stock2)
    print_score_detail(stock2, score2)

    # 测试案例3: 平衡型股票
    print("\n【案例3】平衡型股票")
    print("-" * 80)
    stock3 = {
        'code': '601318',
        'name': '中国平安',
        'price': 45,
        'change_pct': 0.8,
        'pe_ratio': 12,       # PE 10-20
        'pb_ratio': 1.5,      # PB < 2
        'peg': 1.0,
        'turnover': 100000,
        'momentum_20d': 5.5,
        'roe': 12.5,
        'profit_growth': 12.0,
        'dividend_yield': 3.5,
        'turnover_rate': 2.8,
    }

    score3 = filter.calculate_strength_score(stock3)
    print_score_detail(stock3, score3)

    # 测试案例4: 高估值股票
    print("\n【案例4】高估值股票")
    print("-" * 80)
    stock4 = {
        'code': '688981',
        'name': '中芯国际',
        'price': 50,
        'change_pct': -1.2,
        'pe_ratio': 35,       # PE >= 30 (超出配置)
        'pb_ratio': 12.0,     # PB >= 10
        'peg': 2.5,
        'turnover': 80000,
        'momentum_20d': -5.0,
        'roe': 34.3,
        'profit_growth': 5.0,
        'dividend_yield': 0.2,
        'turnover_rate': 12.5,  # 高换手
    }

    score4 = filter.calculate_strength_score(stock4)
    print_score_detail(stock4, score4)

    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)

    # 总结
    print("\n【评分总结】")
    print(f"案例1 (低估值价值股): {score1['total']:.1f}分 ({score1['grade']}级)")
    print(f"案例2 (成长股):       {score2['total']:.1f}分 ({score2['grade']}级)")
    print(f"案例3 (平衡型股票):   {score3['total']:.1f}分 ({score3['grade']}级)")
    print(f"案例4 (高估值股票):   {score4['total']:.1f}分 ({score4['grade']}级)")

def print_score_detail(stock, score_result):
    """打印详细评分"""
    print(f"股票: {stock['name']} ({stock['code']})")
    print(f"价格: {stock['price']}元  涨跌: {stock['change_pct']:+.2f}%")
    print(f"\n【估值指标】")
    print(f"  PE: {stock.get('pe_ratio', 0):.2f}  PB: {stock.get('pb_ratio', 0):.2f}  PEG: {stock.get('peg', 0):.2f}")
    print(f"\n【基本面指标】")
    print(f"  ROE: {stock.get('roe', 0):.1f}%  利润增长: {stock.get('profit_growth', 0):.1f}%")
    print(f"  股息率: {stock.get('dividend_yield', 0):.1f}%  换手率: {stock.get('turnover_rate', 0):.1f}%")
    print(f"\n【技术指标】")
    print(f"  20日动量: {stock.get('momentum_20d', 0):.1f}%  成交额: {stock.get('turnover', 0)/10000:.1f}亿")

    breakdown = score_result['breakdown']
    print(f"\n【评分明细】")
    print(f"  技术面:   {breakdown['technical']:>2}分 / 30分")
    print(f"  估值:     {breakdown['valuation']:>2}分 / 25分")
    print(f"  盈利质量: {breakdown['profitability']:>2}分 / 30分")
    print(f"  安全性:   {breakdown['safety']:>2}分 / 10分")
    print(f"  分红:     {breakdown['dividend']:>2}分 /  5分")
    print(f"  " + "-" * 30)
    print(f"  总分:     {score_result['total']:>2.1f}分 / 100分")
    print(f"  评级:     {score_result['grade']}级")

if __name__ == '__main__':
    test_scoring_system()
