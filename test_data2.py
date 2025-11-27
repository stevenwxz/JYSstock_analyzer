from src.data.data_fetcher import StockDataFetcher

fetcher = StockDataFetcher()
# 测试获取一只股票的数据
stock_data = fetcher.get_stock_realtime_data('600000')
print('测试股票 600000 数据:')
for key, value in stock_data.items():
    print(f'{key}: {value}')