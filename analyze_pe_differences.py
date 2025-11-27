import sys
import os
import requests

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.data_fetcher import StockDataFetcher

def analyze_pe_differences(stock_code, stock_name):
    """分析不同PE指标的差异"""
    fetcher = StockDataFetcher()
    
    # 确定市场代码
    if stock_code.startswith('6'):
        symbol = f"sh{stock_code}"
    else:
        symbol = f"sz{stock_code}"

    url = f"https://qt.gtimg.cn/q={symbol}"
    headers = {
        'User-Agent': fetcher._get_random_user_agent(),
        'Referer': 'https://gu.qq.com/'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            content = response.text
            if 'v_' in content:
                data_str = content.split('"')[1]
                data_parts = data_str.split('~')
                
                print(f"\n=== {stock_name} ({stock_code}) PE指标分析 ===")
                print(f"数据段数量: {len(data_parts)}")
                
                if len(data_parts) > 56:
                    price = float(data_parts[3]) if data_parts[3] and data_parts[3] != '' else 0
                    print(f"当前股价: {price}")
                    
                    # 不同PE指标
                    pe_dynamic = data_parts[14] if len(data_parts) > 14 and data_parts[14] != '' else 'N/A'
                    pe_static = data_parts[15] if len(data_parts) > 15 and data_parts[15] != '' else 'N/A'
                    pe_ttm = data_parts[22] if len(data_parts) > 22 and data_parts[22] != '' else 'N/A'
                    pe_fundamental = data_parts[39] if len(data_parts) > 39 and data_parts[39] != '' else 'N/A'
                    
                    print(f"[14] 动态PE: {pe_dynamic}")
                    print(f"[15] 静态PE: {pe_static}")
                    print(f"[22] TTM PE: {pe_ttm}")
                    print(f"[39] 基本面PE: {pe_fundamental}")
                    
                    # 尝试解析数值并计算
                    pe_values = {}
                    for i, (name, pe_str) in enumerate([
                        ("动态PE", pe_dynamic), 
                        ("静态PE", pe_static), 
                        ("TTM PE", pe_ttm), 
                        ("基本面PE", pe_fundamental)
                    ]):
                        if pe_str != 'N/A' and pe_str != '':
                            try:
                                pe_val = float(pe_str)
                                pe_values[name] = pe_val
                                print(f"  {name}: {pe_val:.2f}")
                            except ValueError:
                                print(f"  {name}: 无法解析 ({pe_str})")
                    
                    # 分析合理性
                    print("\n合理性分析:")
                    for name, value in pe_values.items():
                        if value <= 0:
                            print(f"  {name} ({value:.2f}): 异常 - 负值或零")
                        elif value > 100:
                            print(f"  {name} ({value:.2f}): 可能偏高")
                        elif value < 5:
                            print(f"  {name} ({value:.2f}): 偏低 - 可能是成长股或特殊情况")
                        else:
                            print(f"  {name} ({value:.2f}): 合理范围")
                    
                    # 如果股价和PE都有效，计算市值相关的估值
                    if price > 0 and '基本面PE' in pe_values:
                        pe_val = pe_values['基本面PE']
                        if 0 < pe_val < 100:
                            implied_eps = price / pe_val
                            print(f"\n基于基本面PE的隐含EPS: {implied_eps:.2f}")
                            
    except Exception as e:
        print(f"分析失败: {e}")

# 分析有问题的股票
analyze_pe_differences('300308', '中际旭创')
analyze_pe_differences('300274', '阳光电源')

# 再分析一个正常的股票作为对比
analyze_pe_differences('000001', '平安银行')