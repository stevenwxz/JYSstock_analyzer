from src.data.data_fetcher import StockDataFetcher

fetcher = StockDataFetcher()
# 测试获取一只股票的数据
stock_data = fetcher.get_stock_realtime_data('600000')
print('测试股票 600000 数据:')
print('代码:', stock_data.get('code'))
print('名称:', stock_data.get('name'))
print('价格:', stock_data.get('price'))
print('总市值:', stock_data.get('market_cap'))
print('总股本:', stock_data.get('total_shares'))
print('PB比率:', stock_data.get('pb_ratio'))
print('PE比率:', stock_data.get('pe_ratio'))
print('换手率:', stock_data.get('turnover_rate'))