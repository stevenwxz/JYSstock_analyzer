#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
from datetime import datetime

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def generate_backtest_report(json_file):
    """生成回测分析报告"""

    # 读取JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 生成Markdown报告
    report = f"""# 📊 策略回测报告

## 📅 回测信息

- **分析日期**: {data['analysis_date']}
- **卖出日期**: {data['sell_date']}
- **持有天数**: {data['hold_days']}天
- **筛选股票数**: {data['selected_count']}只
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 策略表现

### 整体收益
- **平均收益率**: {data['summary']['avg_return']:+.2f}%
- **最高收益率**: {data['summary']['max_return']:+.2f}%
- **最低收益率**: {data['summary']['min_return']:+.2f}%
- **胜率**: {data['summary']['win_rate']:.1f}% ({data['summary']['win_count']}/{data['summary']['total_count']})

## 📋 持仓详情

| 股票代码 | 买入价 | 卖出价 | 收益率 | PE估值 |
|---------|--------|--------|--------|--------|
"""

    # 添加股票详情
    for stock in data['performance']:
        arrow = "🔺" if stock['return_pct'] > 0 else "🔻" if stock['return_pct'] < 0 else "➖"
        report += f"| {stock['code']} | ¥{stock['buy_price']:.2f} | ¥{stock['sell_price']:.2f} | {arrow} {stock['return_pct']:+.2f}% | {stock['pe_ratio']:.2f} |\n"

    report += f"""
## 📊 回测分析

### ✅ 策略优势
1. **严格筛选**: PE ≤ 30，确保估值安全
2. **流动性保证**: 成交量 > 100万手
3. **多维评分**: 综合涨跌幅、PE、成交量等指标

### ⚠️ 风险提示
1. **回测样本**: 基于历史数据，不代表未来表现
2. **市场风险**: 股市有风险，投资需谨慎
3. **数据限制**: 回测数据可能不完整

## 💡 改进建议

### 策略优化方向
1. **扩大样本**: 增加回测交易日数量
2. **调整参数**: 优化PE阈值和评分权重
3. **风控机制**: 增加止损止盈策略
4. **多因子模型**: 引入更多技术指标

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据来源**: 历史回测数据
"""

    return report


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python generate_backtest_report.py <backtest_json_file>")
        print("示例: python generate_backtest_report.py backtest_2025-09-30_1days.json")
        return

    json_file = sys.argv[1]

    if not os.path.exists(json_file):
        print(f"错误: 找不到文件 {json_file}")
        return

    # 生成报告
    report = generate_backtest_report(json_file)

    # 保存报告
    output_file = json_file.replace('.json', '_report.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 回测报告已生成: {output_file}")
    print("\n" + "="*60)
    print(report)


if __name__ == "__main__":
    main()
