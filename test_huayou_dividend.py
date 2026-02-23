#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试华友钴业股息率数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock_analyzer'))

from stock_analyzer.src.data.data_fetcher import StockDataFetcher

def test_huayou_dividend():
    """测试华友钴业股息率数据"""
    fetcher = StockDataFetcher()
    
    print("正在获取华友钴业(603799)数据...")
    fundamental_data = fetcher.get_stock_fundamental_data('603799')
    
    print(f"华友钴业基本面数据: {fundamental_data}")
    
    # 也获取实时数据
    realtime_data = fetcher.get_stock_realtime_data('603799')
    print(f"华友钴业实时数据: {realtime_data}")
    
    # 计算理论股息率
    if fundamental_data.get('dividend_yield') is not None:
        print(f"API获取的股息率: {fundamental_data['dividend_yield']:.2f}%")
    
    if realtime_data.get('price') is not None:
        price = realtime_data['price']
        print(f"当前股价: {price}元")
        
        # 根据2024年每10股派现10元的信息计算理论股息率
        dividend_per_share = 1.0  # 每10股派现10元，即每股1.0元
        theoretical_yield = (dividend_per_share / price) * 100
        print(f"基于每10股派现10元的理论股息率: {theoretical_yield:.2f}%")

if __name__ == "__main__":
    test_huayou_dividend()