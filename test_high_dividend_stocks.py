#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异常股息率股票的数据
"""

import requests

def test_high_dividend_stocks():
    """测试异常股息率股票的数据"""
    print("=" * 80)
    print("测试异常股息率股票的数据")
    print("=" * 80)

    # 异常股息率的股票列表
    high_dividend_stocks = ['002600', '601298', '302132', '001391', '301236']
    
    for stock_code in high_dividend_stocks:
        try:
            # 构造腾讯财经API请求
            if stock_code.startswith('6'):
                symbol = f"sh{stock_code}"
            else:
                symbol = f"sz{stock_code}"

            url = f"https://qt.gtimg.cn/q={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://gu.qq.com/'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200 and 'v_' in response.text:
                content = response.text
                data_str = content.split('"')[1]
                data_parts = data_str.split('~')

                print(f"\n股票: {stock_code}")
                if len(data_parts) > 3:
                    print(f"  [3] 当前价格: {data_parts[3]}")
                if len(data_parts) > 52:
                    print(f"  [52] API股息率: {data_parts[52]}%")
                if len(data_parts) > 53:
                    print(f"  [53] 每股股息: {data_parts[53]}")
                if len(data_parts) > 56:
                    print(f"  [56] 换手率: {data_parts[56]}%")
                
                # 尝试解析数据
                current_price = float(data_parts[3]) if data_parts[3] and data_parts[3] != '' else None
                dividend_per_share = float(data_parts[53]) if len(data_parts) > 53 and data_parts[53] and data_parts[53] != '' else None
                api_dividend = float(data_parts[52]) if len(data_parts) > 52 and data_parts[52] and data_parts[52] != '' else None
                
                print(f"  解析后价格: {current_price}")
                print(f"  解析后每股股息: {dividend_per_share}")
                print(f"  解析后API股息率: {api_dividend}%")
                
                if current_price and dividend_per_share and current_price > 0:
                    calculated_yield = (dividend_per_share / current_price) * 100
                    print(f"  计算股息率: {calculated_yield:.2f}%")
                    
                    # 检查是否可能是因为小数点错误
                    if calculated_yield > 20:  # 异常高
                        # 尝试将股息除以100
                        adjusted_yield = (dividend_per_share / 100 / current_price) * 100
                        print(f"  调整后股息率(股息/100): {adjusted_yield:.2f}%")
                        
                        # 尝试将股息除以10
                        adjusted_yield2 = (dividend_per_share / 10 / current_price) * 100
                        print(f"  调整后股息率(股息/10): {adjusted_yield2:.2f}%")
        except Exception as e:
            print(f"  [ERROR] 获取 {stock_code} 数据失败: {e}")

if __name__ == '__main__':
    test_high_dividend_stocks()