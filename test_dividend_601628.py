#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试中国人寿(601628)的股息率数据
"""

import requests

def test_china_life_dividend():
    """测试中国人寿的股息率"""
    stock_code = "601628"
    symbol = f"sh{stock_code}"

    url = f"https://qt.gtimg.cn/q={symbol}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://gu.qq.com/'
    }

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 200 and 'v_' in response.text:
        content = response.text
        print("原始响应数据:")
        print(content)
        print("\n" + "="*80 + "\n")

        data_str = content.split('"')[1]
        data_parts = data_str.split('~')

        print(f"数据字段总数: {len(data_parts)}\n")

        # 打印关键字段
        print("关键字段:")
        print(f"[1] 股票名称: {data_parts[1]}")
        print(f"[3] 当前价格: {data_parts[3]}")
        print(f"[32] 涨跌幅: {data_parts[32]}%")
        print(f"[39] PE市盈率: {data_parts[39]}")
        print(f"[46] PB市净率: {data_parts[46]}")

        if len(data_parts) > 52:
            print(f"[52] 股息率: {data_parts[52]}%")
            try:
                dividend_yield = float(data_parts[52])
                print(f"\n解析后的股息率: {dividend_yield}%")

                # 按照评分逻辑判断
                if dividend_yield > 5:
                    score = 5
                elif dividend_yield > 3:
                    score = 4
                elif dividend_yield > 2:
                    score = 2
                elif dividend_yield > 0:
                    score = 1
                else:
                    score = 0

                print(f"按照当前评分逻辑，应得: {score}分")

            except Exception as e:
                print(f"解析失败: {e}")

        if len(data_parts) > 53:
            print(f"[53] 股息: {data_parts[53]}")

        if len(data_parts) > 56:
            print(f"[56] 换手率: {data_parts[56]}%")

        # 打印更多字段以便分析
        print("\n" + "="*80)
        print("所有字段 (前60个):")
        for i in range(min(60, len(data_parts))):
            if data_parts[i]:
                print(f"[{i}]: {data_parts[i]}")

if __name__ == '__main__':
    test_china_life_dividend()
