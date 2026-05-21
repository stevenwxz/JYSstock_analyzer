#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
优化回测脚本 - 使用回测专用配置
- 放宽筛选条件，确保足够样本
- 添加数据缓存
- 自动生成报告
"""

import sys
import os

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import time
import pickle

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter
from config.backtest_config import BACKTEST_FILTER_CONFIG, BACKTEST_SAMPLE_CONFIG

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedBacktest:
    """优化回测系统 - 使用宽松配置"""

    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        # 使用回测专用配置
        self.stock_filter = StockFilter(config=BACKTEST_FILTER_CONFIG)
        self.cache_dir = './cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        self.stock_name_cache = {}  # 股票名称缓存

    def get_cache_file(self, cache_key):
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.pkl")

    def load_from_cache(self, cache_key):
        """从缓存加载数据"""
        cache_file = self.get_cache_file(cache_key)
        if os.path.exists(cache_file):
            try:
                # 检查缓存是否过期
                expire_days = BACKTEST_SAMPLE_CONFIG.get('cache_expire_days', 7)
                if time.time() - os.path.getmtime(cache_file) < (expire_days * 86400):
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
            except Exception:
                pass
        return None

    def save_to_cache(self, cache_key, data):
        """保存数据到缓存"""
        cache_file = self.get_cache_file(cache_key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    def get_stock_name(self, stock_code: str):
        """获取股票名称（带缓存）"""
        if stock_code in self.stock_name_cache:
            return self.stock_name_cache[stock_code]

        try:
            # 使用akshare获取股票信息
            info = ak.stock_individual_info_em(symbol=stock_code)
            if not info.empty:
                name = info[info['item'] == '股票简称']['value'].values
                if len(name) > 0:
                    stock_name = str(name[0])
                    self.stock_name_cache[stock_code] = stock_name
                    return stock_name
        except Exception:
            pass

        # 如果获取失败，使用代码作为名称
        return f'股票{stock_code}'

    def get_csi300_stocks(self):
        """获取沪深300成分股列表（带缓存）"""
        cache_key = "csi300_stocks_with_names"
        cached_data = self.load_from_cache(cache_key)

        if cached_data:
            logger.info(f"从缓存加载沪深300成分股: {len(cached_data.get('stocks', []))} 只")
            # 恢复名称缓存
            if isinstance(cached_data, dict):
                self.stock_name_cache = cached_data.get('name_cache', {})
                return cached_data.get('stocks', [])
            return cached_data

        # 尝试多种方法获取成分股
        stocks = []

        # 方法1: 使用akshare获取（可能失败）
        try:
            logger.info("正在获取沪深300成分股列表（方法1：akshare）...")
            csi300 = ak.index_stock_cons(symbol="000300")
            stocks = csi300['品种代码'].tolist()

            # 同时获取股票名称
            logger.info("正在获取股票名称...")
            for i, code in enumerate(stocks):
                name = csi300[csi300['品种代码'] == code]['品种名称'].values
                if len(name) > 0:
                    self.stock_name_cache[code] = str(name[0])
                if (i + 1) % 50 == 0:
                    logger.info(f"  名称获取进度: {i+1}/{len(stocks)}")

            logger.info(f"✅ 成功获取 {len(stocks)} 只沪深300成分股及名称")
        except Exception as e:
            logger.warning(f"⚠️ 方法1失败: {e}")

            # 方法2: 使用备用接口
            try:
                logger.info("正在尝试方法2：备用接口...")
                time.sleep(2)
                csi300 = ak.index_stock_cons_csindex(symbol="000300")
                stocks = csi300['成分券代码'].tolist()
                logger.info(f"✅ 方法2成功获取 {len(stocks)} 只股票")
            except Exception as e2:
                logger.error(f"❌ 方法2也失败: {e2}")

        if not stocks:
            logger.error("❌ 无法获取沪深300成分股列表，所有方法均失败")
            return []

        # 保存股票列表和名称缓存
        cache_data = {
            'stocks': stocks,
            'name_cache': self.stock_name_cache
        }
        self.save_to_cache(cache_key, cache_data)
        return stocks

    def get_stock_data_for_date(self, stock_code: str, date: str, pe_ratio: float = None, purpose: str = "buy"):
        """获取指定日期的股票数据（带缓存）"""
        # 为买入和卖出使用不同的缓存键，避免冲突
        cache_key = f"stock_{stock_code}_{date}_{purpose}"
        cached_data = self.load_from_cache(cache_key)

        if cached_data:
            # 如果提供了新的PE值，更新缓存数据
            if pe_ratio is not None and pe_ratio > 0:
                cached_data['pe_ratio'] = pe_ratio
            return cached_data

        try:
            end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=5)).strftime('%Y%m%d')
            start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=35)).strftime('%Y%m%d')

            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily",
                                   start_date=start_date, end_date=end_date, adjust="qfq")

            if df.empty:
                return None

            df['日期'] = pd.to_datetime(df['日期'])
            target_date = pd.to_datetime(date)

            df_on_date = df[df['日期'] <= target_date]
            if df_on_date.empty:
                return None

            row = df_on_date.iloc[-1]

            # 获取真实股票名称
            stock_name = self.get_stock_name(stock_code)

            # 获取PE数据（优先使用传入的值）
            final_pe_ratio = 20.0  # 默认值
            if pe_ratio is not None and pe_ratio > 0:
                final_pe_ratio = pe_ratio
            elif '市盈率' in row:
                try:
                    pe_value = row['市盈率']
                    if pe_value and pe_value > 0:
                        final_pe_ratio = float(pe_value)
                except Exception:
                    pass

            # 计算20日动量
            momentum_20d = 0
            if len(df_on_date) >= 20:
                price_20d_ago = df_on_date.iloc[-20]['收盘']
                current_price = row['收盘']
                momentum_20d = (current_price / price_20d_ago - 1) * 100
            elif len(df_on_date) >= 2:
                # 如果数据不足20天，使用可用的天数
                price_start = df_on_date.iloc[0]['收盘']
                current_price = row['收盘']
                momentum_20d = (current_price / price_start - 1) * 100

            data = {
                'code': stock_code,
                'name': stock_name,
                'price': float(row['收盘']),
                'change_pct': float(row['涨跌幅']),
                'volume': int(row['成交量']),
                'turnover': float(row['成交额']),
                'pe_ratio': final_pe_ratio,
                'momentum_20d': momentum_20d,
                'strength_score': 0
            }

            self.save_to_cache(cache_key, data)
            return data

        except Exception as e:
            logger.debug(f"获取 {stock_code} 数据失败: {e}")
            return None

    def get_next_trading_day(self, date: str, days: int = 1):
        """获取下一个交易日"""
        try:
            current = datetime.strptime(date, '%Y-%m-%d')
            for i in range(1, 15):
                next_date = current + timedelta(days=i*days)
                if next_date.weekday() < 5:
                    return next_date.strftime('%Y-%m-%d')
            return (current + timedelta(days=days)).strftime('%Y-%m-%d')
        except Exception:
            return date

    def fetch_pe_ratios_batch(self, stock_codes: list) -> dict:
        """批量获取股票PE数据(使用腾讯API)"""
        pe_dict = {}
        logger.info("📊 正在获取PE数据(使用腾讯财经API)...")

        success_count = 0
        for i, code in enumerate(stock_codes):
            try:
                stock_data = self.data_fetcher.get_stock_realtime_data(code)
                if stock_data and stock_data.get('pe_ratio'):
                    pe_dict[code] = stock_data['pe_ratio']
                    success_count += 1

                # 每50个股票显示一次进度
                if (i + 1) % 50 == 0:
                    logger.info(f"   进度: {i+1}/{len(stock_codes)}")
            except Exception:
                pass

        logger.info(f"✅ 成功获取 {success_count}/{len(stock_codes)} 只股票的PE数据")
        return pe_dict

    def backtest_single_day(self, analysis_date: str, hold_days: int = 1):
        """回测单日策略"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📅 回测日期: {analysis_date} | 持有{hold_days}天")
        logger.info(f"{'='*70}")

        # 获取沪深300成分股
        stock_list = self.get_csi300_stocks()
        if not stock_list:
            logger.error("无法获取沪深300成分股列表")
            return None

        # 采样（如果sample_size >= 300则使用全部）
        sample_size = BACKTEST_SAMPLE_CONFIG['sample_size']
        if sample_size >= len(stock_list):
            logger.info(f"📊 使用全部沪深300成分股: {len(stock_list)}只")
            sampled_stocks = stock_list
        else:
            logger.info(f"📊 采样配置: {sample_size}只股票")
            import random
            random.seed(BACKTEST_SAMPLE_CONFIG['random_seed'])
            sampled_stocks = random.sample(stock_list, min(sample_size, len(stock_list)))

        # 批量获取PE数据
        pe_ratios = self.fetch_pe_ratios_batch(sampled_stocks)

        stock_data = []
        for i, code in enumerate(sampled_stocks):
            if i % 20 == 0:
                logger.info(f"⏳ 数据获取进度: {i+1}/{len(sampled_stocks)}")

            # 获取买入数据时标记purpose为"buy"
            data = self.get_stock_data_for_date(code, analysis_date, pe_ratios.get(code), "buy")
            if data:
                stock_data.append(data)

            if i % 20 == 19:
                time.sleep(0.3)

        logger.info(f"✅ 成功获取 {len(stock_data)}/{sample_size} 只股票数据")

        if len(stock_data) < 10:
            logger.error("❌ 获取的股票数据太少")
            return None

        # 使用回测配置筛选
        logger.info(f"\n🔍 筛选配置:")
        logger.info(f"   • PE上限: {BACKTEST_FILTER_CONFIG['max_pe_ratio']}")
        logger.info(f"   • 成交额: {BACKTEST_FILTER_CONFIG['min_turnover']/10000:.0f}万元")
        logger.info(f"   • 强势分数: ≥{BACKTEST_FILTER_CONFIG['min_strength_score']}")
        logger.info(f"   • 推荐数量: {BACKTEST_FILTER_CONFIG['max_stocks']}只")

        # 调用筛选器选择股票
        selected_stocks = self.stock_filter.select_top_stocks(stock_data)

        if not selected_stocks:
            logger.warning("⚠️  未筛选出任何股票")
            return {
                'analysis_date': analysis_date,
                'selected_count': 0,
                'performance': [],
                'config_used': 'backtest_relaxed'
            }

        # 在输出筛选结果前增加去重检查
        unique_stocks = []
        seen_codes = set()
        
        for stock in selected_stocks:
            if stock['code'] not in seen_codes:
                unique_stocks.append(stock)
                seen_codes.add(stock['code'])
            else:
                logger.warning(f"发现重复股票代码: {stock['code']} ({stock['name']})，已跳过重复项")
        
        selected_stocks = unique_stocks
        
        logger.info(f"\n🏆 筛选结果 ({len(selected_stocks)}只):")
        for stock in selected_stocks:
            logger.info(f"   #{stock['rank']} {stock['name']} ({stock['code']}): "
                       f"¥{stock['price']:.2f}, PE={stock.get('pe_ratio', 0):.1f}, "
                       f"分数={stock.get('strength_score', 0):.0f}")

        # 计算收益
        sell_date = self.get_next_trading_day(analysis_date, hold_days)
        logger.info(f"\n💰 收益计算 (卖出日期: {sell_date}):")

        performance = []
        for stock in selected_stocks:
            # 获取卖出数据时标记purpose为"sell"
            sell_data = self.get_stock_data_for_date(stock['code'], sell_date, purpose="sell")
            if sell_data:
                buy_price = stock['price']
                sell_price = sell_data['price']
                return_pct = (sell_price / buy_price - 1) * 100

                performance.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'return_pct': return_pct,
                    'pe_ratio': stock.get('pe_ratio', 0),
                    'strength_score': stock.get('strength_score', 0)
                })

                emoji = "📈" if return_pct > 0 else "📉" if return_pct < 0 else "➖"
                logger.info(f"   {emoji} {stock['name']}: ¥{buy_price:.2f} → ¥{sell_price:.2f} ({return_pct:+.2f}%)")

        # 统计
        if performance:
            returns = [p['return_pct'] for p in performance]
            avg_return = sum(returns) / len(returns)
            max_return = max(returns)
            min_return = min(returns)
            win_count = len([r for r in returns if r > 0])
            win_rate = win_count / len(returns) * 100

            logger.info(f"\n📊 策略表现:")
            logger.info(f"   • 平均收益: {avg_return:+.2f}%")
            logger.info(f"   • 收益区间: {min_return:+.2f}% ~ {max_return:+.2f}%")
            logger.info(f"   • 胜率: {win_rate:.1f}% ({win_count}/{len(returns)})")

        return {
            'analysis_date': analysis_date,
            'sell_date': sell_date,
            'hold_days': hold_days,
            'selected_count': len(selected_stocks),
            'sample_size': len(stock_data),
            'performance': performance,
            'config_used': 'backtest_relaxed',
            'filter_config': BACKTEST_FILTER_CONFIG,
            'summary': {
                'avg_return': avg_return if performance else 0,
                'max_return': max_return if performance else 0,
                'min_return': min_return if performance else 0,
                'win_rate': win_rate if performance else 0,
                'win_count': win_count if performance else 0,
                'total_count': len(performance)
            }
        }

    def backtest_multi_days(self, start_date: str, end_date: str, hold_days: int = 1):
        """多日回测"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📅 多日回测: {start_date} ~ {end_date}")
        logger.info(f"{'='*70}")

        # 生成交易日
        trading_days = []
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        while current <= end:
            if current.weekday() < 5:
                trading_days.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)

        logger.info(f"共 {len(trading_days)} 个交易日")

        all_results = []
        for i, date in enumerate(trading_days):
            logger.info(f"\n{'='*70}")
            logger.info(f"进度: {i+1}/{len(trading_days)}")

            result = self.backtest_single_day(date, hold_days)
            if result and result['selected_count'] > 0:
                all_results.append(result)

            time.sleep(1)

        # 汇总
        if all_results:
            all_returns = []
            for r in all_results:
                all_returns.extend([p['return_pct'] for p in r['performance']])

            logger.info(f"\n{'='*70}")
            logger.info(f"📊 回测总结:")
            logger.info(f"{'='*70}")
            logger.info(f"   • 有效交易日: {len(all_results)}")
            logger.info(f"   • 总交易次数: {len(all_returns)}")
            if all_returns:
                logger.info(f"   • 整体平均收益: {sum(all_returns)/len(all_returns):+.2f}%")
                logger.info(f"   • 最佳单笔: {max(all_returns):+.2f}%")
                logger.info(f"   • 最差单笔: {min(all_returns):+.2f}%")
                win_count = len([r for r in all_returns if r > 0])
                logger.info(f"   • 整体胜率: {win_count/len(all_returns)*100:.1f}%")

        return all_results


def main():
    """主函数"""
    print("="*70)
    print("📊 沪深300策略回测系统 (优化配置版)")
    print("="*70)
    print("✨ 配置特性:")
    print(f"   • PE上限: {BACKTEST_FILTER_CONFIG['max_pe_ratio']} (实盘30)")
    print(f"   • 成交额: {BACKTEST_FILTER_CONFIG['min_turnover']/10000:.0f}万元 (实盘5000万)")
    print(f"   • 强势分数: ≥{BACKTEST_FILTER_CONFIG['min_strength_score']} (实盘50)")
    print(f"   • 推荐数量: {BACKTEST_FILTER_CONFIG['max_stocks']}只 (实盘3只)")
    if BACKTEST_SAMPLE_CONFIG['sample_size'] >= 300:
        print(f"   • 股票池: 全部沪深300成分股")
    else:
        print(f"   • 采样数量: {BACKTEST_SAMPLE_CONFIG['sample_size']}只")
    print("="*70)

    backtest = OptimizedBacktest()

    print("\n请选择回测模式:")
    print("1. 单日回测")
    print("2. 多日回测 (建议≤5天)")

    choice = input("\n请输入选项 (1/2): ").strip()

    if choice == '1':
        date = input("请输入回测日期 (例: 2025-09-25): ").strip() or '2025-09-25'
        hold_days = int(input("请输入持有天数 (默认1天): ").strip() or '1')

        result = backtest.backtest_single_day(date, hold_days)

        if result:
            # 确保目录存在
            os.makedirs('./logs/backtest', exist_ok=True)
            filename = f"./logs/backtest/backtest_opt_{date}_{hold_days}days.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"\n✅ 回测结果已保存: {filename}")

    elif choice == '2':
        start_date = input("请输入开始日期 (例: 2025-09-23): ").strip() or '2025-09-23'
        end_date = input("请输入结束日期 (例: 2025-09-27): ").strip() or '2025-09-27'
        hold_days = int(input("请输入持有天数 (默认1天): ").strip() or '1')

        results = backtest.backtest_multi_days(start_date, end_date, hold_days)

        if results:
            # 确保目录存在
            os.makedirs('./logs/backtest', exist_ok=True)
            filename = f"./logs/backtest/backtest_opt_{start_date}_to_{end_date}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"\n✅ 回测结果已保存: {filename}")

    else:
        print("无效的选项")


if __name__ == "__main__":
    main()