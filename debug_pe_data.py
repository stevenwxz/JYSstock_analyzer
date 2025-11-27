import sys
import os
import requests
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.data_fetcher import StockDataFetcher

def test_tencent_api(stock_code):
    """直接测试腾讯API返回的数据"""
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
                
                print(f"股票 {stock_code} 腾讯API返回的完整数据:")
                print(f"数据段数量: {len(data_parts)}")
                
                # 打印关键字段
                if len(data_parts) > 56:
                    print(f"[1] 名称: {data_parts[1] if data_parts[1] else 'N/A'}")
                    print(f"[3] 当前价: {data_parts[3] if data_parts[3] else 'N/A'}")
                    print(f"[32] 涨跌幅: {data_parts[32] if data_parts[32] else 'N/A'}")
                    print(f"[14] 动态PE: {data_parts[14] if data_parts[14] else 'N/A'}")
                    print(f"[15] 静态PE: {data_parts[15] if data_parts[15] else 'N/A'}")
                    print(f"[22] TTM PE: {data_parts[22] if data_parts[22] else 'N/A'}")
                    print(f"[39] 基本面PE: {data_parts[39] if data_parts[39] else 'N/A'}")
                    print(f"[16] PB: {data_parts[16] if data_parts[16] else 'N/A'}")
                    print(f"[27] 换手率: {data_parts[27] if data_parts[27] else 'N/A'}")
                    print()
                    
                return data_parts
    except Exception as e:
        print(f"获取腾讯API数据失败: {e}")
        return None

def test_stock_data(stock_code):
    """测试股票数据获取"""
    print(f"\n=== 测试股票 {stock_code} ===")
    
    # 直接测试腾讯API
    test_tencent_api(stock_code)
    
    fetcher = StockDataFetcher()
    
    print("获取实时数据:")
    realtime_data = fetcher.get_stock_realtime_data(stock_code)
    if realtime_data:
        print(f"  股票名称: {realtime_data.get('name', 'N/A')}")
        print(f"  股价: {realtime_data.get('price', 'N/A')}")
        print(f"  PE比率: {realtime_data.get('pe_ratio', 'N/A')}")
        print(f"  PB比率: {realtime_data.get('pb_ratio', 'N/A')}")
        print(f"  总市值: {realtime_data.get('market_cap', 'N/A')}")
        print(f"  总股本: {realtime_data.get('total_shares', 'N/A')}")
    
    print("\n获取基本面数据:")
    fundamental_data = fetcher.get_stock_fundamental_data(stock_code)
    if fundamental_data:
        print(f"  基本面PE: {fundamental_data.get('pe_ratio', 'N/A')}")
        print(f"  基本面PB: {fundamental_data.get('pb_ratio', 'N/A')}")
        print(f"  股息率: {fundamental_data.get('dividend_yield', 'N/A')}")
        print(f"  ROE: {fundamental_data.get('roe', 'N/A')}")
    
    print("\n批量获取测试:")
    batch_data = fetcher.batch_get_stock_data([stock_code], calculate_momentum=False, include_fundamental=True)
    if batch_data:
        stock = batch_data[0]
        print(f"  最终PE: {stock.get('pe_ratio', 'N/A')}")
        print(f"  最终PB: {stock.get('pb_ratio', 'N/A')}")
        print(f"  价格: {stock.get('price', 'N/A')}")
        print(f"  ROE: {stock.get('roe', 'N/A')}")

# 测试有问题的股票
test_stocks = ['300308', '300274']  # 中际旭创和阳光电源

for stock_code in test_stocks:
    test_stock_data(stock_code)
