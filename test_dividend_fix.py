#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试正泰电器股息率修正是否生效
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'stock_analyzer'))

from stock_analyzer.config.dividend_override import get_dividend_info, get_manual_dividend_yield, has_manual_override

def test_zhengtai_dividend():
    """测试正泰电器股息率修正"""
    stock_code = '601877'
    
    print("=== 正泰电器(601877)股息率修正测试 ===")
    
    # 检查是否有手动配置
    has_override = has_manual_override(stock_code)
    print(f"是否有手动配置: {has_override}")
    
    if has_override:
        # 获取手动配置的股息率
        manual_dividend = get_manual_dividend_yield(stock_code)
        print(f"手动配置股息率: {manual_dividend}%")
        
        # 获取完整股息信息
        dividend_info = get_dividend_info(stock_code)
        if dividend_info:
            print(f"完整股息信息:")
            print(f"  股息率: {dividend_info['dividend_yield']}%")
            print(f"  每股股息: {dividend_info['dividend_per_share']}元")
            print(f"  年份: {dividend_info['year']}")
            print(f"  备注: {dividend_info['note']}")
        
        # 验证数据是否符合预期
        expected_dividend = 1.97  # 根据10派6.0元和股价30.46元计算
        if abs(manual_dividend - expected_dividend) < 0.1:
            print(f"✅ 测试通过！股息率已成功修正为{manual_dividend}%")
            return True
        else:
            print(f"❌ 测试失败！期望股息率约{expected_dividend}%，实际{manual_dividend}%")
            return False
    else:
        print(f"❌ 测试失败！股票{stock_code}没有手动配置")
        return False

if __name__ == "__main__":
    success = test_zhengtai_dividend()
    if success:
        print("\n🎉 正泰电器股息率修正配置成功！")
    else:
        print("\n❌ 正泰电器股息率修正配置失败！")
        sys.exit(1)
