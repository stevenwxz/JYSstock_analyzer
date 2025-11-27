from src.analysis.market_analyzer import MarketAnalyzer
from datetime import datetime

# 创建模拟股票数据来测试表格生成
mock_selected_stocks = [
    {
        'rank': 1,
        'code': '600000',
        'name': '浦发银行',
        'price': 11.69,
        'market_cap': 34567890000,  # 3456.79亿元（单位：元）
        'total_shares': 2963040000,  # 29.63亿股（单位：股）
        'pe_ratio': 11.66,
        'pb_ratio': 0.75,
        'roe': 12.5,
        'change_pct': 1.2,
        'strength_score': 85,
        'strength_grade': 'A',
        'strength_score_detail': {
            'breakdown': {
                'technical': 25,
                'valuation': 20,
                'profitability': 25,
                'safety': 10,
                'dividend': 5
            }
        }
    },
    {
        'rank': 2,
        'code': '000001',
        'name': '平安银行',
        'price': 15.23,
        'market_cap': 298765400000,  # 2987.65亿元
        'total_shares': 19617300000,  # 196.17亿股
        'pe_ratio': 8.75,
        'pb_ratio': 0.85,
        'roe': 14.2,
        'change_pct': -0.5,
        'strength_score': 82,
        'strength_grade': 'A',
        'strength_score_detail': {
            'breakdown': {
                'technical': 23,
                'valuation': 22,
                'profitability': 25,
                'safety': 8,
                'dividend': 4
            }
        }
    }
]

# 模拟生成Markdown报告中的表格部分
print("## 📋 **Top 2 候选股票**")
print()
print("| 排名 | 股票名称 | 代码 | 股价 | 总市值(亿) | PB | PE | ROE | 涨跌幅 | 评分 | 评级 | 技术面 | 估值 | 盈利 | 安全 | 股息 |")
print("|------|----------|------|------|------------|----|----|----- |---------|-----|-----|--------|------|------|------|------|")

for stock in mock_selected_stocks:
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
    # 尝试获取总市值
    market_cap = stock.get('market_cap', None)  # 单位是元
    if market_cap:
        market_cap_display = f"{market_cap/100000000:.2f}"  # 转换为亿元并格式化
    else:
        # 尝试使用总股本计算总市值
        total_shares = stock.get('total_shares', None)  # 单位是股
        if total_shares and price > 0:
            total_market_cap = price * total_shares  # 总市值 = 股价 * 总股本
            market_cap_display = f"{total_market_cap/100000000:.2f}"  # 转换为亿元并格式化
        else:
            market_cap_display = "-"  # 无法获取总市值，显示为"-"
    
    row = f"|  {stock['rank']} | {stock['name']} | {stock['code']} | {price:.2f} | {market_cap_display} | {pb:.2f} | {stock['pe_ratio']:.2f} | {roe_display} | {stock.get('change_pct', 0):+.2f}% | {stock.get('strength_score', 0):.0f} | {grade} | {tech_score} | {val_score} | {prof_score} | {safe_score} | {div_score} |"
    print(row)

print()
print("表格生成测试完成！")