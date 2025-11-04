#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试股息率修正功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.data_fetcher import StockDataFetcher
from src.analysis.stock_filter import StockFilter

def test_dividend_fix():
    """测试中国人寿的股息率修正"""
    print("=" * 80)
    print("测试股息率修正功能 - 中国人寿(601628)")
    print("=" * 80)

    # 1. 获取股票数据
    print("\n步骤1: 获取中国人寿的股票数据...")
    fetcher = StockDataFetcher()

    # 获取实时数据
    realtime_data = fetcher.get_stock_realtime_data('601628')
    if not realtime_data:
        print("[ERROR] 获取实时数据失败")
        return

    print(f"[OK] 股票名称: {realtime_data['name']}")
    print(f"[OK] 当前价格: {realtime_data['price']}")
    print(f"[OK] PE: {realtime_data.get('pe_ratio', 'N/A')}")

    # 获取基本面数据（包含股息率）
    print("\n步骤2: 获取基本面数据...")
    fundamental_data = fetcher.get_stock_fundamental_data('601628')

    if fundamental_data:
        dividend_yield = fundamental_data.get('dividend_yield')
        print(f"[OK] 股息率: {dividend_yield}% {'(手动配置)' if dividend_yield == 1.48 else '(API数据)'}")
        print(f"[OK] PB: {fundamental_data.get('pb_ratio', 'N/A')}")
        print(f"[OK] ROE: {fundamental_data.get('roe', 'N/A')}")
        print(f"[OK] 换手率: {fundamental_data.get('turnover_rate', 'N/A')}")

        # 合并数据
        realtime_data.update(fundamental_data)
    else:
        print("[ERROR] 获取基本面数据失败")
        return

    # 3. 计算评分
    print("\n步骤3: 计算股息评分...")
    filter = StockFilter()
    score_result = filter.calculate_strength_score(realtime_data)

    breakdown = score_result['breakdown']
    dividend_score = breakdown['dividend']

    print(f"\n【评分结果】")
    print(f"  股息率: {dividend_yield}%")
    print(f"  股息得分: {dividend_score}分 / 5分")
    print(f"  ")
    print(f"  评分逻辑:")
    print(f"    - 股息率 > 5%  → 5分")
    print(f"    - 股息率 > 3%  → 4分")
    print(f"    - 股息率 > 2%  → 2分")
    print(f"    - 股息率 > 0%  → 1分")
    print(f"  ")
    print(f"  当前股息率 {dividend_yield}% → 应得 1分")

    if dividend_score == 1:
        print(f"  [OK] 评分正确！")
    else:
        print(f"  [ERROR] 评分错误！应该是1分，但得到{dividend_score}分")

    # 4. 显示完整评分
    print(f"\n【完整评分明细】")
    print(f"  技术面:   {breakdown['technical']:>2}分 / 30分")
    print(f"  估值:     {breakdown['valuation']:>2}分 / 25分")
    print(f"  盈利质量: {breakdown['profitability']:>2}分 / 30分")
    print(f"  安全性:   {breakdown['safety']:>2}分 / 10分")
    print(f"  分红:     {breakdown['dividend']:>2}分 /  5分")
    print(f"  " + "-" * 30)
    print(f"  总分:     {score_result['total']:>2.1f}分 / 100分")
    print(f"  评级:     {score_result['grade']}级")

    print("\n" + "=" * 80)
    if dividend_score == 1 and dividend_yield == 1.48:
        print("[SUCCESS] 测试通过！股息率已成功修正为1.48%，评分为1分")
    else:
        print("[FAILED] 测试失败！请检查配置")
    print("=" * 80)

if __name__ == '__main__':
    test_dividend_fix()
