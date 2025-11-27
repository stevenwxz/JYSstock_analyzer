# 测试新格式的表格生成
from datetime import datetime

# 模拟股票数据
selected_stocks = [
    {
        'rank': 1,
        'code': '600000',
        'name': '浦发银行',
        'price': 11.69,
        'market_cap': 34567890000,
        'pb_ratio': 0.75,
        'pe_ratio': 11.66,
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
        'market_cap': 298765400000,
        'pb_ratio': 0.85,
        'pe_ratio': 8.75,
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

# 生成HTML表格
html = "<table>\n"
html += "    <tr>\n"
html += "        <th>排名</th>\n"
html += "        <th>股票名称</th>\n"
html += "        <th>代码</th>\n"
html += "        <th>股价</th>\n"
html += "        <th>总市值(亿)</th>\n"
html += "        <th>PB</th>\n"
html += "        <th>PE</th>\n"
html += "        <th>ROE</th>\n"
html += "        <th>涨跌幅</th>\n"
html += "        <th>评分</th>\n"
html += "        <th>评级</th>\n"
html += "        <th>技术面</th>\n"
html += "        <th>估值</th>\n"
html += "        <th>盈利</th>\n"
html += "        <th>安全</th>\n"
html += "        <th>股息</th>\n"
html += "    </tr>\n"

for stock in selected_stocks:
    change_pct = stock.get('change_pct', 0)
    roe = stock.get('roe', 0)
    roe_display = f"{roe:.1f}%" if roe else "-"
    grade = stock.get('strength_grade', '-')
    price = stock.get('price', 0)
    pb = stock.get('pb_ratio', 0)
    
    # 获取总市值
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
    
    # 获取分项得分
    score_detail = stock.get('strength_score_detail', {})
    tech_score = 0
    val_score = 0
    prof_score = 0
    safe_score = 0
    div_score = 0
    if score_detail:
        breakdown = score_detail.get('breakdown', {})
        tech_score = breakdown.get('technical', 0)
        val_score = breakdown.get('valuation', 0)
        prof_score = breakdown.get('profitability', 0)
        safe_score = breakdown.get('safety', 0)
        div_score = breakdown.get('dividend', 0)

    html += f"""    <tr>
        <td>{stock.get('rank', 0)}</td>
        <td>{stock.get('name', '')}</td>
        <td>{stock.get('code', '')}</td>
        <td>{price:.2f}</td>
        <td>{market_cap_display}</td>
        <td>{pb:.2f}</td>
        <td>{stock.get('pe_ratio', 0):.2f}</td>
        <td>{roe_display}</td>
        <td>{change_pct:+.2f}%</td>
        <td>{stock.get('strength_score', 0):.0f}</td>
        <td><strong>{grade}</strong></td>
        <td>{tech_score}</td>
        <td>{val_score}</td>
        <td>{prof_score}</td>
        <td>{safe_score}</td>
        <td>{div_score}</td>
    </tr>
"""

html += "</table>"

print("更新后的HTML表格格式:")
print(html)
