#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查新华保险股息率评分
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter

def check_new_china_life_dividend():
    """检查新华保险股息率评分"""
    print("=" * 60)
    print("检查新华保险(601336)股息率评分")
    print("=" * 60)

    fetcher = StockDataFetcher()
    filter = StockFilter()

    # 获取股票数据
    realtime_data = fetcher.get_stock_realtime_data('601336')
    if realtime_data:
        print(f"股票名称: {realtime_data['name']}")
        print(f"当前价格: {realtime_data['price']}")
        
        # 获取基本面数据
        fundamental_data = fetcher.get_stock_fundamental_data('601336')
        if fundamental_data:
            # 合并数据
            realtime_data.update(fundamental_data)
            
            # 获取股息率
            dividend_yield = fundamental_data.get('dividend_yield')
            print(f"股息率: {dividend_yield}%")
            
            # 计算评分
            score_result = filter.calculate_strength_score(realtime_data)
            dividend_score = score_result['breakdown']['dividend']
            print(f"股息得分: {dividend_score}分")
            
            # 显示评分规则
            print("\n评分规则:")
            if dividend_yield and dividend_yield > 5:
                print("  股息率 > 5% → 5分")
                expected = 5
            elif dividend_yield and dividend_yield > 3:
                print("  股息率 > 3% → 4分")
                expected = 4
            elif dividend_yield and dividend_yield > 2:
                print("  股息率 > 2% → 2分")
                expected = 2
            elif dividend_yield and dividend_yield > 0:
                print("  股息率 > 0% → 1分")
                expected = 1
            else:
                expected = 0
            
            print(f"\n预期得分: {expected}分")
            if dividend_score == expected:
                print("[SUCCESS] 评分正确!")
            else:
                print(f"[ERROR] 评分错误! 期望: {expected}分, 实际: {dividend_score}分")
        else:
            print("[ERROR] 无法获取基本面数据")
    else:
        print("[ERROR] 无法获取实时数据")

if __name__ == '__main__':
    check_new_china_life_dividend()