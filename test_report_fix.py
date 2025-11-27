#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的报告生成功能
"""
from src.analysis.market_analyzer import MarketAnalyzer

def test_latest_analysis():
    analyzer = MarketAnalyzer()
    result = analyzer.get_latest_analysis()
    print('Found latest analysis:', result is not None)
    
    if result:
        print("Analysis date:", result.get('analysis_date'))
        selected_stocks = result.get('selected_stocks', [])
        print(f"Selected {len(selected_stocks)} stocks")
        
        # 重新生成报告以测试修复
        success = analyzer._generate_markdown_report(result)
        print("Report regeneration success:", success)

if __name__ == "__main__":
    test_latest_analysis()