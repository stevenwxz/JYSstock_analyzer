#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成Markdown格式分析报告
用法: python generate_md_report.py [JSON文件路径]
"""
import sys
import os
import io
import json
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def generate_markdown_report(json_file):
    """生成Markdown报告"""
    # 读取JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 判断是回测数据还是实盘数据
    is_backtest = 'performance' in data
    
    if is_backtest:
        analysis_date = data['analysis_date']
        selected_stocks = [
            {
                'rank': i+1,
                'code': s['code'],
                'name': s['name'],
                'price': s['buy_price'],
                'change_pct': s.get('return_pct', 0),
                'pe_ratio': s.get('pe_ratio', 0),
                'strength_score': s['strength_score'],
                'volume': 0,
                'selection_reason': f"强势分数={s['strength_score']:.0f}"
            }
            for i, s in enumerate(data['performance'])
        ]
        total_analyzed = data.get('sample_size', 300)
        config = data.get('filter_config', {})
    else:
        analysis_date = data['analysis_date']
        selected_stocks = data.get('selected_stocks', [])
        total_analyzed = data.get('total_analyzed', 300)
        config = data.get('selection_criteria', {})
    
    # 转换日期格式
    date_obj = datetime.strptime(analysis_date, '%Y-%m-%d')
    date_cn = date_obj.strftime('%Y年%m月%d日')
    
    # 生成Markdown内容
    md_content = f"""# 📊 {date_cn}沪深300成分股分析结果

## 🔍 **分析概况**

### 📅 **基本信息**
- **分析日期**: {analysis_date}
- **分析时间**: {datetime.now().strftime('%H:%M:%S')}
- **数据源**: {'历史回测数据' if is_backtest else '实时数据'}
- **股票池**: 沪深300成分股
- **目标股票数**: {total_analyzed}只
- **筛选条件**: PE ≤ {config.get('max_pe_ratio', 30)}, 换手率 ≥ {config.get('min_turnover_rate', 1.0)}%

## 🏆 **Top {len(selected_stocks)} 精选股票**

"""
    
    # 添加每只股票的详细信息
    for stock in selected_stocks:
        trend = "↗" if stock.get('change_pct', 0) > 0 else "↘" if stock.get('change_pct', 0) < 0 else "→"
        md_content += f"""### #{stock['rank']} {stock['name']} ({stock['code']}) [{trend}]
- **价格**: ¥{stock['price']:.2f}
- **涨跌幅**: {stock.get('change_pct', 0):+.2f}%
- **PE**: {stock['pe_ratio']:.2f}倍
- **强势分数**: {stock.get('strength_score', 0):.0f}分
- **选择理由**: {stock.get('selection_reason', '符合筛选条件')}

"""
    
    # 添加候选股票表格
    md_content += f"""## 📋 **Top {len(selected_stocks)} 候选股票**

| 排名 | 股票名称 | 代码 | 股价 | PB | PE | PR | ROE | 20日动量 | 评分 | 评级 | 技术面 | 估值 | 盈利 | 安全 | 股息 |
|------|----------|------|------|------|------|------|-------|---------|-----|------|--------|------|------|------|------|
"""
    
    for stock in selected_stocks:
        # 获取分项得分
        score_detail = stock.get('strength_score_detail', {})
        breakdown = score_detail.get('breakdown', {})
        tech_score = breakdown.get('technical', 0)
        val_score = breakdown.get('valuation', 0)
        prof_score = breakdown.get('profitability', 0)
        safe_score = breakdown.get('safety', 0)
        div_score = breakdown.get('dividend', 0)
        grade = score_detail.get('grade', '-')
        roe = stock.get('roe', 0)
        roe_display = f"{roe:.1f}%" if roe else "-"
        price = stock.get('price', 0)
        pb = stock.get('pb_ratio', 0)
        # 计算PR（市赚率）
        pe_ratio = stock.get('pe_ratio', 0)
        roe_decimal = roe / 100 if roe > 0 else 0  # ROE是百分比形式，需要转换为小数
        pr_display = "-"
        if pe_ratio > 0 and roe_decimal > 0:
            pr = pe_ratio / (100 * roe_decimal)
            pr_display = f"{pr:.2f}"
        momentum_20d = stock.get('momentum_20d', 0)
        md_content += f"|  {stock['rank']} | {stock['name']} | {stock['code']} | {price:.2f} | {pb:.2f} | {stock['pe_ratio']:.2f} | {pr_display} | {roe_display} | {momentum_20d:+.2f}% | {stock.get('strength_score', 0):.0f} | {grade} | {tech_score} | {val_score} | {prof_score} | {safe_score} | {div_score} |\n"
    
    # 添加筛选统计
    md_content += f"""
## 📊 **沪深300筛选统计**

### 🔍 **筛选结果**
- **沪深300总数**: {total_analyzed}只
- **筛选通过**: {len(selected_stocks)}只
- **筛选通过率**: {len(selected_stocks)/total_analyzed*100:.2f}%

### 📊 **筛选标准**
- **PE筛选**: PE ≤ {config.get('max_pe_ratio', 30)}
- **换手率筛选**: 换手率 ≥ {config.get('min_turnover_rate', 1.0)}%
- **强势分数**: ≥ {config.get('min_strength_score', 50)}
- **数量限制**: 最多推荐{config.get('max_stocks', 3)}只股票

## 🎯 **投资分析**

### ✅ **精选股票亮点**
"""
    
    for stock in selected_stocks:
        # 计算优势维度(得分最高的维度)
        score_detail = stock.get('strength_score_detail', {})
        breakdown = score_detail.get('breakdown', {})

        # 维度名称映射
        dimension_names = {
            'technical': '技术面',
            'valuation': '估值',
            'profitability': '盈利能力',
            'safety': '安全性',
            'dividend': '股息'
        }

        # 找出得分最高的维度
        if breakdown:
            max_dimension = max(breakdown.items(), key=lambda x: x[1])
            advantage_dim = f"{dimension_names.get(max_dimension[0], max_dimension[0])} ({max_dimension[1]}分)"
        else:
            advantage_dim = "符合多维度筛选标准"

        md_content += f"""
{stock['rank']}. **{stock['name']} ({stock['code']})**
   - **估值水平**: PE {stock['pe_ratio']:.2f}倍
   - **强势评分**: {stock.get('strength_score', 0):.0f}分
   - **优势维度**: {advantage_dim}
"""
    
    md_content += f"""
### 📈 **投资价值**
- **市场代表性**: 基于沪深300成分股,代表A股核心优质资产
- **估值安全**: 严格PE筛选避免高风险标的  
- **流动性保证**: 换手率要求确保充足的交易流动性
- **技术筛选**: 基于20日动量、强势分数等多维度技术指标

### ⚠️ **风险提示**
1. **市场风险**: 股市有风险,投资需谨慎
2. **估值风险**: PE为历史数据,需关注最新财报
3. **流动性风险**: 市场波动可能影响交易流动性
4. **投资建议**: 本报告仅供参考,不构成投资建议

## 💡 **技术说明**

### 🔧 **策略特点**
- **多维度筛选**: PE估值、换手率、动量、强势评分综合评估
- **20日动量**: 基于20日价格动量捕捉趋势
- **换手率过滤**: 确保足够的市场流动性
- **智能评分**: 综合涨跌幅、动量、流动性等指标

### 📊 **数据来源**
- **股票池**: 沪深300成分股
- **数据频率**: {'历史日线数据' if is_backtest else '实时交易数据'}
- **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析版本**: v3.0 (量化策略优化版)
**数据范围**: 沪深300成分股分析 ✓
"""
    
    # 保存文件到reports目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{date_cn}沪深300分析结果.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f'✅ Markdown报告已生成: {output_file}')
    return output_file

if __name__ == '__main__':
    if len(sys.argv) < 2:
        # 使用最新的回测结果
        import glob
        json_files = glob.glob('backtest_opt_*.json')
        if json_files:
            json_file = max(json_files, key=os.path.getmtime)
            print(f'使用最新回测结果: {json_file}')
        else:
            print('用法: python generate_md_report.py [JSON文件路径]')
            sys.exit(1)
    else:
        json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f'错误: 文件不存在 {json_file}')
        sys.exit(1)
    
    generate_markdown_report(json_file)
