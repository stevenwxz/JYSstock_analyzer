#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定股票的股息率获取
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter

def test_stock_dividend():
    """测试股票股息率获取"""
    print("=" * 80)
    print("测试股票股息率获取")
    print("=" * 80)

    fetcher = StockDataFetcher()
    filter = StockFilter()

    # 测试股票列表
    test_stocks = ['601628', '601319', '601601', '601600']
    
    for stock_code in test_stocks:
        print(f"\n测试股票: {stock_code}")
        
        # 获取实时数据
        realtime_data = fetcher.get_stock_realtime_data(stock_code)
        if not realtime_data:
            print(f"  [ERROR] 无法获取实时数据")
            continue
            
        print(f"  股票名称: {realtime_data['name']}")
        print(f"  当前价格: {realtime_data['price']}")
        print(f"  涨跌幅: {realtime_data['change_pct']}")
        
        # 获取基本面数据
        fundamental_data = fetcher.get_stock_fundamental_data(stock_code)
        if fundamental_data:
            dividend_yield = fundamental_data.get('dividend_yield')
            print(f"  股息率: {dividend_yield}%")
            
            # 合并数据
            realtime_data.update(fundamental_data)
            
            # 计算评分
            score_result = filter.calculate_strength_score(realtime_data)
            dividend_score = score_result['breakdown']['dividend']
            
            print(f"  股息得分: {dividend_score}分")
            print(f"  总分: {score_result['total']:.1f}分")
            print(f"  评级: {score_result['grade']}级")
            
            # 显示评分逻辑
            if dividend_yield is not None:
                if dividend_yield > 5:
                    expected_score = 5
                elif dividend_yield > 3:
                    expected_score = 4
                elif dividend_yield > 2:
                    expected_score = 2
                elif dividend_yield > 0:
                    expected_score = 1
                else:
                    expected_score = 0
                    
                print(f"  预期得分: {expected_score}分")
                
                if dividend_score == expected_score:
                    print(f"  [SUCCESS] 评分正确")
                else:
                    print(f"  [ERROR] 评分错误! 期望: {expected_score}分, 实际: {dividend_score}分")
        else:
            print(f"  [ERROR] 无法获取基本面数据")

if __name__ == '__main__':
    test_stock_dividend()