#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分析脚本 - 自动判断交易日
- 交易时段：分析当日实时数据
- 非交易时段：分析上一个交易日历史数据
"""

import sys
import os
import io

# 设置UTF-8编码输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import akshare as ak
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter
from config.config import STOCK_FILTER_CONFIG

def get_last_trading_day():
    """获取上一个交易日"""
    try:
        # 获取交易日历
        today = datetime.now()
        
        # 如果是周六，回退到周五
        if today.weekday() == 5:  # 周六
            last_day = today - timedelta(days=1)
        # 如果是周日，回退到周五
        elif today.weekday() == 6:  # 周日
            last_day = today - timedelta(days=2)
        # 工作日
        else:
            # 判断当前时间
            current_hour = today.hour
            if current_hour < 16:  # 16:00前，使用前一个交易日
                if today.weekday() == 0:  # 周一
                    last_day = today - timedelta(days=3)
                else:
                    last_day = today - timedelta(days=1)
            else:  # 16:00后，可以使用今天
                last_day = today
        
        return last_day.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"获取交易日失败: {e}")
        return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

def is_trading_time():
    """判断是否在交易时段"""
    now = datetime.now()
    # 周末不是交易时段
    if now.weekday() >= 5:
        return False
    # 9:30-15:00是交易时段
    hour = now.hour
    minute = now.minute
    if (hour == 9 and minute >= 30) or (10 <= hour < 15):
        return True
    return False

def analyze_historical_day(date_str):
    """分析历史某一天的数据（类似回测）"""
    print('=' * 70)
    print(f'📊 沪深300历史分析 - {date_str}')
    print('=' * 70)
    
    print(f'\n🔍 筛选配置:')
    print(f'   • PE上限: {STOCK_FILTER_CONFIG["max_pe_ratio"]}')
    print(f'   • 成交额: {STOCK_FILTER_CONFIG["min_turnover"]/10000:.0f}万元')
    print(f'   • 强势分数: ≥{STOCK_FILTER_CONFIG["min_strength_score"]}')
    print(f'   • 推荐数量: {STOCK_FILTER_CONFIG["max_stocks"]}只')
    
    # 使用回测逻辑获取历史数据
    print(f'\n⏳ 正在获取 {date_str} 的历史数据...')
    
    try:
        # 获取沪深300成分股
        csi300 = ak.index_stock_cons(symbol="000300")
        stock_codes = csi300['品种代码'].tolist()
        print(f'✅ 获取到 {len(stock_codes)} 只沪深300成分股')
        
        # 获取历史数据
        stock_data = []
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        end_date = (target_date + timedelta(days=5)).strftime('%Y%m%d')
        start_date = (target_date - timedelta(days=35)).strftime('%Y%m%d')
        
        print(f'\n⏳ 获取股票历史数据...')
        for i, code in enumerate(stock_codes):
            if i % 50 == 0:
                print(f'   进度: {i+1}/{len(stock_codes)}')
            
            try:
                df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                       start_date=start_date, end_date=end_date, adjust="qfq")
                
                if df.empty:
                    continue
                
                df['日期'] = pd.to_datetime(df['日期'])
                df_on_date = df[df['日期'] <= target_date]
                
                if df_on_date.empty:
                    continue
                
                row = df_on_date.iloc[-1]
                
                # 计算动量
                momentum_20d = 0
                if len(df_on_date) >= 20:
                    price_20d_ago = df_on_date.iloc[-20]['收盘']
                    current_price = row['收盘']
                    momentum_20d = (current_price / price_20d_ago - 1) * 100
                
                # 获取股票名称
                name = csi300[csi300['品种代码'] == code]['品种名称'].values
                stock_name = str(name[0]) if len(name) > 0 else f'股票{code}'
                
                data = {
                    'code': code,
                    'name': stock_name,
                    'price': float(row['收盘']),
                    'change_pct': float(row['涨跌幅']),
                    'volume': int(row['成交量']),
                    'turnover': float(row['成交额']),
                    'pe_ratio': 20.0,
                    'momentum_20d': momentum_20d,
                    'strength_score': 0
                }
                stock_data.append(data)
                
            except Exception as e:
                continue
        
        print(f'\n✅ 成功获取 {len(stock_data)} 只股票数据')
        
        # 筛选
        print('\n🎯 开始筛选...')
        stock_filter = StockFilter(config=STOCK_FILTER_CONFIG)
        selected = stock_filter.select_top_stocks(stock_data)
        
        if selected:
            print(f'\n🏆 {date_str} 推荐股票 ({len(selected)}只):\n')
            for stock in selected:
                print(f'   #{stock["rank"]} {stock["name"]} ({stock["code"]})')
                print(f'      价格: ¥{stock["price"]:.2f}')
                print(f'      涨跌幅: {stock["change_pct"]:+.2f}%')
                print(f'      PE: {stock.get("pe_ratio", 0):.1f}')
                print(f'      20日动量: {stock.get("momentum_20d", 0):+.2f}%')
                print(f'      成交额: {stock.get("turnover", 0)/10000:.0f}万元')
                print(f'      强势分数: {stock.get("strength_score", 0):.0f}')
                print()
        else:
            print(f'\n⚠️  {date_str} 未筛选出符合条件的股票')
        
        print('=' * 70)
        
    except Exception as e:
        print(f'\n❌ 分析失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import pandas as pd
    
    # 判断是否在交易时段
    if is_trading_time():
        print('⏰ 当前处于交易时段，建议收盘后运行分析')
        print('   现在可以运行实盘脚本: python main.py --mode analysis')
    else:
        # 获取上一个交易日
        last_trading_day = get_last_trading_day()
        print(f'⏰ 非交易时段，自动分析上一个交易日: {last_trading_day}')
        print()
        
        # 分析历史数据
        analyze_historical_day(last_trading_day)
