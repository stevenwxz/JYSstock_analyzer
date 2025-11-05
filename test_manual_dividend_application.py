#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试手动配置的股息率是否被正确应用
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_fetcher import StockDataFetcher

def test_manual_dividend_application():
    """测试手动配置的股息率是否被正确应用"""
    print("=" * 80)
    print("测试手动配置的股息率是否被正确应用")
    print("=" * 80)

    fetcher = StockDataFetcher()

    # 测试几个股票
    test_stocks = ['601319', '601601', '601600']
    
    for stock_code in test_stocks:
        print(f"\n测试股票: {stock_code}")
        
        # 获取基本面数据
        fundamental_data = fetcher.get_stock_fundamental_data(stock_code)
        
        if fundamental_data:
            dividend_yield = fundamental_data.get('dividend_yield')
            print(f"  实际获取的股息率: {dividend_yield}%")
            
            # 手动检查配置值
            from config.dividend_override import get_manual_dividend_yield
            manual_value = get_manual_dividend_yield(stock_code)
            print(f"  手动配置的股息率: {manual_value}%")
            
            if dividend_yield == manual_value:
                print(f"  [SUCCESS] 手动配置值被正确应用")
            else:
                print(f"  [ERROR] 手动配置值未被应用! 期望: {manual_value}%, 实际: {dividend_yield}%")
        else:
            print(f"  [ERROR] 无法获取基本面数据")

if __name__ == '__main__':
    test_manual_dividend_application()
