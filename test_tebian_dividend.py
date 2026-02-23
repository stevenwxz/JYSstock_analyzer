#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特变电工股息率数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock_analyzer'))

from stock_analyzer.src.data.data_fetcher import StockDataFetcher

def test_tebian_dividend():
    """测试特变电工股息率数据"""
    fetcher = StockDataFetcher()
    
    print("正在获取特变电工(600089)数据...")
    fundamental_data = fetcher.get_stock_fundamental_data('600089')
    
    print(f"特变电工基本面数据: {fundamental_data}")
    
    # 也获取实时数据
    realtime_data = fetcher.get_stock_realtime_data('600089')
    print(f"特变电工实时数据: {realtime_data}")
    
    # 计算理论股息率
    if fundamental_data.get('dividend_yield') is not None:
        print(f"API获取的股息率: {fundamental_data['dividend_yield']:.2f}%")
    
    if realtime_data.get('price') is not None:
        price = realtime_data['price']
        print(f"当前股价: {price}元")

if __name__ == "__main__":
    test_tebian_dividend()