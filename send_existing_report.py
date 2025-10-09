#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from notification.email_sender import EmailSender
from datetime import datetime

def create_analysis_result_from_csi300():
    """基于沪深300全量分析结果创建分析结果数据"""

    # 基于实际分析结果的推荐股票
    selected_stocks = [
        {
            'rank': 1,
            'code': '688472',
            'name': '阿特斯',
            'price': 13.44,
            'change_pct': 4.27,
            'pe_ratio': 28.50,
            'momentum_20d': 4.27,
            'strength_score': 70.0,
            'selection_reason': 'PE=28.50；评分=70；涨跌幅=+4.27%；新能源优质龙头'
        },
        {
            'rank': 2,
            'code': '601618',
            'name': '中国中冶',
            'price': 3.85,
            'change_pct': 10.00,
            'pe_ratio': 14.01,
            'momentum_20d': 10.00,
            'strength_score': 68.0,
            'selection_reason': 'PE=14.01；评分=68；涨跌幅=+10.00%；基建央企龙头'
        },
        {
            'rank': 3,
            'code': '600989',
            'name': '宝丰能源',
            'price': 17.80,
            'change_pct': 3.19,
            'pe_ratio': 14.92,
            'momentum_20d': 3.19,
            'strength_score': 65.0,
            'selection_reason': 'PE=14.92；评分=65；涨跌幅=+3.19%；化工行业龙头'
        }
    ]

    # 构造分析结果
    analysis_result = {
        'analysis_date': '2025-09-30',
        'analysis_time': '22:45:21',
        'selected_stocks': selected_stocks,
        'market_overview': {
            'total_stocks': 300,
            'rising_stocks': 165,
            'falling_stocks': 135,
            'rising_ratio': 55.0,
            'avg_change_pct': 0.74
        },
        'summary': {
            'market_sentiment': '弱势震荡',
            'key_metrics': {
                'avg_price': 11.70,
                'avg_pe_ratio': 19.14,
                'avg_momentum': 5.82,
                'price_range': '¥3.85-¥17.80',
                'pe_range': '14.01-28.50'
            },
            'risk_warnings': [
                '市场处于弱势震荡状态，投资需谨慎',
                '推荐股票虽然基本面良好，但需关注大盘走势',
                '建议分批建仓，控制仓位风险',
                '严格执行止损策略，PE数据基于TTM计算'
            ]
        },
        'strategy_performance': {
            'avg_return': 5.82,
            'success_rate': 100.0,
            'relative_return': 5.08
        }
    }

    return analysis_result

def send_csi300_email():
    """发送沪深300分析结果邮件"""
    print("=" * 60)
    print("发送沪深300量化分析邮件")
    print("=" * 60)

    try:
        # 创建分析结果
        analysis_result = create_analysis_result_from_csi300()

        print("+ 分析结果数据准备完成")
        print(f"  - 分析日期: {analysis_result['analysis_date']}")
        print(f"  - 推荐股票: {len(analysis_result['selected_stocks'])}只")
        print(f"  - 策略收益: +{analysis_result['strategy_performance']['avg_return']:.2f}%")

        # 创建邮件发送器
        email_sender = EmailSender()

        print("\n正在发送邮件...")
        success = email_sender.send_analysis_email(analysis_result)

        if success:
            print("+ 邮件发送成功！")
            print("\n发送内容摘要:")
            print(f"  - 分析日期: 2025年9月30日")
            print(f"  - 策略表现: +5.82% (超额收益+5.08%)")
            print(f"  - Top 3 股票:")
            for stock in analysis_result['selected_stocks']:
                print(f"    #{stock['rank']} {stock['name']} ({stock['code']}) +{stock['change_pct']:.2f}%")
            print(f"  - 收件箱: 1120311927@qq.com")
        else:
            print("- 邮件发送失败")

    except Exception as e:
        print(f"- 发送邮件过程中出现错误: {e}")

if __name__ == "__main__":
    send_csi300_email()