from src.data.data_fetcher import StockDataFetcher

# 测试有问题的股票代码
test_stocks = ['300308', '300274']  # 中际旭创和阳光电源

fetcher = StockDataFetcher()

print("测试有问题的股票PE数据:")
for stock_code in test_stocks:
    print(f"\n获取股票 {stock_code} 的数据:")
    stock_data = fetcher.get_stock_realtime_data(stock_code)
    if stock_data:
        print(f"  股票名称: {stock_data.get('name', 'N/A')}")
        print(f"  股价: {stock_data.get('price', 'N/A')}")
        print(f"  PE比率: {stock_data.get('pe_ratio', 'N/A')}")
        print(f"  PB比率: {stock_data.get('pb_ratio', 'N/A')}")
    else:
        print(f"  获取数据失败")

print("\n批量获取测试:")
batch_data = fetcher.batch_get_stock_data(test_stocks, calculate_momentum=False, include_fundamental=True)
for stock in batch_data:
    print(f"股票 {stock.get('code')} - {stock.get('name')}:")
    print(f"  PE: {stock.get('pe_ratio')}")
    print(f"  PB: {stock.get('pb_ratio')}")
    print(f"  价格: {stock.get('price')}")