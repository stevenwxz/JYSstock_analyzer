#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的异常股息率股票
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter

def test_fixed_high_dividend_stocks():
    """测试修复后的异常股息率股票"""
    print("=" * 80)
    print("测试修复后的异常股息率股票")
    print("=" * 80)

    fetcher = StockDataFetcher()
    filter = StockFilter()

    # 异常股息率的股票列表
    high_dividend_stocks = ['002600', '601298', '302132', '001391', '301236']
    
    for stock_code in high_dividend_stocks:
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
            
            # 检查股息率是否在合理范围内
            if dividend_yield and dividend_yield <= 20:
                print(f"  [SUCCESS] 股息率在合理范围内")
            else:
                print(f"  [WARNING] 股息率仍然过高: {dividend_yield}%")
            
            # 合并数据
            realtime_data.update(fundamental_data)
            
            # 计算评分
            score_result = filter.calculate_strength_score(realtime_data)
            dividend_score = score_result['breakdown']['dividend']
            
            print(f"  股息得分: {dividend_score}分")
            print(f"  总分: {score_result['total']:.1f}分")
            print(f"  评级: {score_result['grade']}级")
        else:
            print(f"  [ERROR] 无法获取基本面数据")

if __name__ == '__main__':
    test_fixed_high_dividend_stocks()
