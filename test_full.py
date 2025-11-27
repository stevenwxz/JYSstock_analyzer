# 简单的测试脚本，测试修改后的功能
from src.analysis.market_analyzer import MarketAnalyzer
from src.data.data_fetcher import StockDataFetcher
import json
from datetime import datetime

print("开始测试修改后的股票分析系统...")

# 测试获取几只股票的数据
fetcher = StockDataFetcher()
test_stocks = ['600000', '000001']  # 浦发银行, 平安银行

print("获取测试股票数据...")
stock_data_list = fetcher.batch_get_stock_data(test_stocks)

print(f"成功获取 {len(stock_data_list)} 只股票的数据")

# 显示其中一只股票的详细信息
if stock_data_list:
    first_stock = stock_data_list[0]
    print(f"\n第一只股票: {first_stock['name']} ({first_stock['code']})")
    print(f"价格: {first_stock['price']}")
    print(f"总市值: {first_stock.get('market_cap', 'N/A')}")
    print(f"总股本: {first_stock.get('total_shares', 'N/A')}")
    print(f"PE: {first_stock.get('pe_ratio', 'N/A')}")
    print(f"PB: {first_stock.get('pb_ratio', 'N/A')}")
    print(f"换手率: {first_stock.get('turnover_rate', 'N/A')}")

print("\n测试完成！修改已成功应用。")