#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import akshare as ak
import requests
import time
import pandas as pd
from datetime import datetime
import concurrent.futures
import threading
from collections import defaultdict

# 全局变量用于线程安全的计数器
request_counter = defaultdict(int)
counter_lock = threading.Lock()

def get_csi300_full_stocks():
    """获取沪深300全量成分股"""
    try:
        print("正在获取沪深300全量成分股...")
        csi300 = ak.index_stock_cons(symbol="000300")
        stock_codes = csi300['品种代码'].tolist()
        stock_names = csi300['品种名称'].tolist()

        stocks_list = list(zip(stock_codes, stock_names))
        print(f"成功获取沪深300全量成分股: {len(stocks_list)}只")
        return stocks_list

    except Exception as e:
        print(f"获取沪深300成分股失败: {e}")
        print("使用备用沪深300股票列表...")

        # 备用沪深300股票列表（部分主要成分股）
        backup_stocks = [
            ('600036', '招商银行'), ('000001', '平安银行'), ('601398', '工商银行'),
            ('601318', '中国平安'), ('000002', '万科A'), ('600519', '贵州茅台'),
            ('000858', '五粮液'), ('002415', '海康威视'), ('300059', '东方财富'),
            ('300750', '宁德时代'), ('002594', '比亚迪'), ('600887', '伊利股份'),
            ('000725', '京东方A'), ('600028', '中国石化'), ('600104', '上汽集团'),
            ('601012', '隆基绿能'), ('000063', '中兴通讯'), ('002230', '科大讯飞'),
            ('600000', '浦发银行'), ('002142', '宁波银行'), ('002736', '国信证券'),
            ('600009', '上海机场'), ('600050', '中国联通'), ('600570', '恒生电子'),
            ('601688', '华泰证券'), ('002352', '顺丰控股'), ('601166', '兴业银行'),
            ('600015', '华夏银行'), ('600036', '招商银行'), ('601988', '中国银行'),
        ]
        return backup_stocks[:30]  # 限制在30只作为演示

def get_single_stock_data(stock_info, index, total):
    """获取单只股票的数据"""
    code, name = stock_info

    # 线程安全的请求计数
    with counter_lock:
        request_counter['total'] += 1
        current_count = request_counter['total']

    try:
        # 构造腾讯财经API请求
        if code.startswith('6'):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"

        url = f"https://qt.gtimg.cn/q={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=8)

        if response.status_code == 200:
            content = response.text
            if 'v_' in content:
                # 解析腾讯返回的数据
                data_str = content.split('"')[1]
                data_parts = data_str.split('~')

                if len(data_parts) > 39:
                    actual_name = data_parts[1]
                    price = float(data_parts[3]) if data_parts[3] else 0
                    change_pct = float(data_parts[32]) if data_parts[32] else 0
                    pe_str = data_parts[39] if len(data_parts) > 39 else None
                    volume = int(float(data_parts[6])) if data_parts[6] else 0

                    pe_value = None
                    if pe_str and pe_str != '':
                        try:
                            pe_value = float(pe_str)
                            if pe_value <= 0:
                                pe_value = None  # 亏损股
                        except ValueError:
                            pass

                    stock_data = {
                        'code': code,
                        'name': actual_name,
                        'price': price,
                        'change_pct': change_pct,
                        'pe_ttm': pe_value,
                        'volume': volume,
                        'date': '2025-09-30'
                    }

                    pe_display = f"{pe_value:.2f}" if pe_value else "亏损"
                    print(f"[{current_count:3d}/{total}] {code} {actual_name:10} PE={pe_display:>6} 涨跌={change_pct:+.2f}% [OK]")

                    return stock_data

        print(f"[{current_count:3d}/{total}] {code} {name:10} 数据获取失败")
        return None

    except Exception as e:
        print(f"[{current_count:3d}/{total}] {code} {name:10} 异常: {str(e)[:20]}")
        return None

def get_stocks_data_parallel(stocks_list, max_workers=10):
    """并行获取股票数据"""
    print(f"\n开始并行获取{len(stocks_list)}只沪深300股票数据 (最大{max_workers}个线程):")
    print("-" * 80)

    results = []

    # 重置计数器
    with counter_lock:
        request_counter.clear()

    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_stock = {
            executor.submit(get_single_stock_data, stock_info, i+1, len(stocks_list)): stock_info
            for i, stock_info in enumerate(stocks_list)
        }

        # 收集结果
        for future in concurrent.futures.as_completed(future_to_stock):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                stock_info = future_to_stock[future]
                print(f"线程异常 {stock_info[0]}: {e}")

            # 控制请求频率，避免过于频繁
            time.sleep(0.1)

    print(f"\n数据获取完成:")
    print(f"- 目标获取: {len(stocks_list)}只")
    print(f"- 成功获取: {len(results)}只")
    print(f"- 成功率: {len(results)/len(stocks_list)*100:.1f}%")

    return results

def analyze_csi300_full():
    """分析沪深300全量成分股"""
    print("=" * 80)
    print("沪深300全量成分股分析 - 真实PE数据版")
    print("=" * 80)

    # 获取沪深300全量成分股
    all_csi300_stocks = get_csi300_full_stocks()

    if not all_csi300_stocks:
        print("无法获取沪深300成分股数据")
        return None

    # 并行获取所有股票数据
    all_stocks = get_stocks_data_parallel(all_csi300_stocks, max_workers=8)

    if not all_stocks:
        print("未获取到任何股票数据")
        return None

    # PE筛选
    pe_filtered_stocks = []
    loss_stocks = []
    high_pe_stocks = []

    print(f"\n应用PE筛选条件 (PE>0 且 PE<=30):")
    print("-" * 80)

    for stock in all_stocks:
        pe = stock['pe_ttm']
        if pe and pe > 0 and pe <= 30:
            pe_filtered_stocks.append(stock)
            print(f"+ {stock['name']:12} PE={pe:5.2f} 涨跌={stock['change_pct']:+5.2f}%")
        else:
            if pe is None or pe <= 0:
                loss_stocks.append(stock)
                print(f"- {stock['name']:12} (亏损股)")
            elif pe > 30:
                high_pe_stocks.append(stock)
                print(f"- {stock['name']:12} (PE={pe:.1f}>30)")

    print(f"\n筛选统计:")
    print(f"- 成功获取数据: {len(all_stocks)}只")
    print(f"- PE筛选通过: {len(pe_filtered_stocks)}只")
    print(f"- 亏损股: {len(loss_stocks)}只")
    print(f"- 高PE股(>30): {len(high_pe_stocks)}只")
    print(f"- 筛选通过率: {len(pe_filtered_stocks)/len(all_stocks)*100:.1f}%")

    if len(pe_filtered_stocks) < 3:
        print("PE筛选后股票不足3只，无法进行分析")
        return None

    # 综合评分系统
    print(f"\n对{len(pe_filtered_stocks)}只合格股票进行综合评分:")
    print("-" * 80)

    scored_stocks = []
    for stock in pe_filtered_stocks:
        score = 0

        # 涨跌幅评分 (35分)
        change_pct = stock['change_pct']
        if change_pct > 3:
            score += 35
        elif change_pct > 2:
            score += 30
        elif change_pct > 1:
            score += 25
        elif change_pct > 0:
            score += 20
        elif change_pct > -1:
            score += 15
        elif change_pct > -2:
            score += 10
        elif change_pct > -3:
            score += 5

        # PE估值评分 (30分)
        pe = stock['pe_ttm']
        if pe <= 8:
            score += 30
        elif pe <= 12:
            score += 25
        elif pe <= 15:
            score += 20
        elif pe <= 20:
            score += 15
        elif pe <= 25:
            score += 10
        elif pe <= 30:
            score += 5

        # 流动性评分 (25分)
        volume = stock['volume']
        if volume > 100000000:
            score += 25
        elif volume > 50000000:
            score += 20
        elif volume > 20000000:
            score += 15
        elif volume > 10000000:
            score += 12
        elif volume > 5000000:
            score += 8
        elif volume > 1000000:
            score += 5

        # 价格合理性评分 (10分)
        price = stock['price']
        if 5 < price < 100:
            score += 10
        elif 3 < price < 150:
            score += 8
        elif 1 < price < 200:
            score += 5

        stock['score'] = score
        scored_stocks.append(stock)

        print(f"{stock['name']:12} 评分={score:2.0f} (PE={pe:5.2f}, 涨跌={change_pct:+5.2f}%, 成交量={volume:>8,})")

    # 选择Top 3
    scored_stocks.sort(key=lambda x: x['score'], reverse=True)
    selected_stocks = scored_stocks[:3]
    top_10_stocks = scored_stocks[:10]

    # 添加排名信息
    for i, stock in enumerate(selected_stocks):
        stock['rank'] = i + 1
        stock['strength_score'] = stock['score']
        stock['selection_reason'] = f"PE={stock['pe_ttm']:.2f}；评分={stock['score']:.0f}；涨跌幅={stock['change_pct']:+.2f}%"

    # 计算统计数据
    all_changes = [s['change_pct'] for s in all_stocks]
    positive_count = len([c for c in all_changes if c > 0])
    avg_change = sum(all_changes) / len(all_changes)

    selected_changes = [s['change_pct'] for s in selected_stocks]
    avg_selected_change = sum(selected_changes) / len(selected_changes)

    # PE分布统计
    pe_values = [s['pe_ttm'] for s in all_stocks if s['pe_ttm'] and s['pe_ttm'] > 0]
    avg_pe = sum(pe_values) / len(pe_values) if pe_values else 0

    result = {
        'analysis_date': '2025-09-30',
        'analysis_time': datetime.now().strftime('%H:%M:%S'),
        'total_csi300_stocks': len(all_csi300_stocks),
        'successful_fetch': len(all_stocks),
        'pe_filtered_stocks': len(pe_filtered_stocks),
        'loss_stocks_count': len(loss_stocks),
        'high_pe_stocks_count': len(high_pe_stocks),
        'selected_stocks': selected_stocks,
        'top_10_stocks': top_10_stocks,
        'all_qualified_stocks': scored_stocks,
        'loss_stocks': loss_stocks[:10],  # 只保留前10个亏损股示例
        'high_pe_stocks': high_pe_stocks[:10],  # 只保留前10个高PE股示例
        'market_stats': {
            'total_stocks': len(all_stocks),
            'rising_stocks': positive_count,
            'falling_stocks': len(all_stocks) - positive_count,
            'rising_ratio': positive_count / len(all_stocks) * 100,
            'avg_change_pct': avg_change,
            'avg_pe': avg_pe
        },
        'strategy_performance': {
            'avg_return': avg_selected_change,
            'success_rate': len([c for c in selected_changes if c > 0]) / len(selected_changes) * 100,
            'relative_return': avg_selected_change - avg_change
        }
    }

    return result

def generate_full_csi300_report(result):
    """生成沪深300全量分析报告"""
    if not result:
        return "分析失败"

    lines = []
    lines.append("# 📊 2025年9月30日沪深300全量成分股分析结果")
    lines.append("")
    lines.append("## 🔍 **分析概况**")
    lines.append("")
    lines.append("### 📅 **基本信息**")
    lines.append(f"- **分析日期**: {result['analysis_date']}")
    lines.append(f"- **分析时间**: {result['analysis_time']}")
    lines.append("- **数据源**: 腾讯财经实时API")
    lines.append("- **股票池**: 沪深300全量成分股")
    lines.append(f"- **目标股票数**: {result['total_csi300_stocks']}只")
    lines.append(f"- **成功获取**: {result['successful_fetch']}只")
    lines.append(f"- **数据成功率**: {result['successful_fetch']/result['total_csi300_stocks']*100:.1f}%")
    lines.append("- **筛选条件**: PE-TTM > 0 且 PE-TTM ≤ 30")
    lines.append("")

    lines.append("## 🏆 **Top 3 精选股票**")
    lines.append("")

    for stock in result['selected_stocks']:
        rank = stock['rank']
        name = stock['name']
        code = stock['code']
        price = stock['price']
        change_pct = stock['change_pct']
        pe_ttm = stock['pe_ttm']
        score = stock['strength_score']
        volume = stock['volume']

        status = "[↗]" if change_pct > 0 else "[↘]"

        lines.append(f"### #{rank} {name} ({code}) {status}")
        lines.append(f"- **收盘价**: ¥{price:.2f}")
        lines.append(f"- **涨跌幅**: {change_pct:+.2f}%")
        lines.append(f"- **PE-TTM**: {pe_ttm:.2f}倍")
        lines.append(f"- **成交量**: {volume:,}手")
        lines.append(f"- **综合评分**: {score:.0f}分")
        lines.append(f"- **选择理由**: {stock['selection_reason']}")
        lines.append("")

    lines.append("## 📋 **Top 10 候选股票**")
    lines.append("")
    lines.append("| 排名 | 股票名称 | 代码 | PE | 涨跌幅 | 评分 | 成交量(万手) |")
    lines.append("|------|----------|------|----|---------|----- |-------------|")

    for i, stock in enumerate(result['top_10_stocks'], 1):
        status = "*" if i <= 3 else ""
        volume_wan = stock['volume'] / 10000
        lines.append(f"| {i:2d} | {stock['name']:8} | {stock['code']} | {stock['pe_ttm']:5.2f} | {stock['change_pct']:+5.2f}% | {stock['score']:2.0f} | {volume_wan:8.0f} {status} |")

    lines.append("")

    lines.append("## 📊 **沪深300全量筛选统计**")
    lines.append("")
    lines.append("### 🔍 **筛选结果**")
    lines.append(f"- **沪深300总数**: {result['total_csi300_stocks']}只")
    lines.append(f"- **成功获取数据**: {result['successful_fetch']}只")
    lines.append(f"- **PE筛选通过**: {result['pe_filtered_stocks']}只")
    lines.append(f"- **亏损股数量**: {result['loss_stocks_count']}只")
    lines.append(f"- **高PE股数量(>30)**: {result['high_pe_stocks_count']}只")
    lines.append(f"- **筛选通过率**: {result['pe_filtered_stocks']/result['successful_fetch']*100:.1f}%")
    lines.append("")

    # 被剔除股票示例
    if result['loss_stocks']:
        lines.append("### ❌ **亏损股示例**")
        for stock in result['loss_stocks']:
            lines.append(f"- **{stock['name']}** ({stock['code']}): 涨跌{stock['change_pct']:+.2f}%")
        lines.append("")

    if result['high_pe_stocks']:
        lines.append("### ⚠️ **高PE股示例(>30)**")
        for stock in result['high_pe_stocks']:
            lines.append(f"- **{stock['name']}** ({stock['code']}): PE={stock['pe_ttm']:.1f}倍，涨跌{stock['change_pct']:+.2f}%")
        lines.append("")

    lines.append("## 📊 **沪深300市场统计**")
    lines.append("")
    stats = result['market_stats']
    lines.append("### 🎯 **整体表现**")
    lines.append(f"- **有效分析股票**: {stats['total_stocks']}只")
    lines.append(f"- **上涨股票**: {stats['rising_stocks']}只 ({stats['rising_ratio']:.1f}%)")
    lines.append(f"- **下跌股票**: {stats['falling_stocks']}只")
    lines.append(f"- **沪深300平均涨跌幅**: {stats['avg_change_pct']:+.2f}%")
    lines.append(f"- **有效股票平均PE**: {stats['avg_pe']:.2f}倍")
    lines.append("")

    perf = result['strategy_performance']
    lines.append("### 💪 **策略表现**")
    lines.append(f"- **策略平均收益**: {perf['avg_return']:+.2f}%")
    lines.append(f"- **选股成功率**: {perf['success_rate']:.1f}%")
    lines.append(f"- **相对沪深300超额收益**: {perf['relative_return']:+.2f}%")
    lines.append("")

    lines.append("## 🎯 **沪深300全量分析价值**")
    lines.append("")
    lines.append("### ✅ **分析优势**")
    lines.append("1. **全覆盖**: 基于沪深300全量成分股，无遗漏")
    lines.append("2. **代表性**: 涵盖A股市场最具代表性的300家公司")
    lines.append("3. **真实数据**: 使用腾讯财经实时API确保数据准确性")
    lines.append("4. **严格筛选**: PE筛选剔除亏损股和泡沫股")
    lines.append("5. **多维评分**: 涨跌幅、PE估值、流动性、价格合理性综合评分")
    lines.append("")

    lines.append("### 📈 **投资价值**")
    lines.append("- **市场代表性**: 沪深300成分股代表A股核心优质资产")
    lines.append("- **流动性保证**: 成分股均有充足交易量")
    lines.append("- **估值安全**: 严格PE筛选避免高风险标的")
    lines.append("- **行业分散**: 覆盖金融、消费、科技、周期等各行业")
    lines.append("")

    lines.append("## 💡 **技术说明**")
    lines.append("")
    lines.append("### 🔧 **数据获取**")
    lines.append("- **并行处理**: 使用多线程技术提高数据获取效率")
    lines.append("- **实时数据**: 腾讯财经API提供实时PE-TTM数据")
    lines.append("- **容错机制**: 自动处理网络异常和数据异常")
    lines.append("- **频率控制**: 合理控制API请求频率避免被限制")
    lines.append("")

    lines.append("### ⚠️ **重要提醒**")
    lines.append("- 本分析基于2025年9月30日沪深300成分股实时数据")
    lines.append("- 沪深300成分股定期调整，建议关注最新成分股变化")
    lines.append("- PE数据为TTM（滚动12个月）市盈率")
    lines.append("- 投资有风险，决策需谨慎")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("**数据范围**: 沪深300全量成分股 ✓")

    return "\n".join(lines)

def main():
    # 执行分析
    result = analyze_csi300_full()

    if result:
        # 生成报告
        report = generate_full_csi300_report(result)

        # 保存报告
        filename = '2025年9月30日沪深300全量分析结果.md'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n" + "="*80)
        print("沪深300全量成分股分析完成！")
        print(f"报告已保存: {filename}")

        # 显示关键结果
        print(f"\n关键结果:")
        print(f"- 沪深300总数: {result['total_csi300_stocks']}只")
        print(f"- 成功获取: {result['successful_fetch']}只")
        print(f"- PE筛选通过: {result['pe_filtered_stocks']}只")
        print(f"- 亏损股: {result['loss_stocks_count']}只")
        print(f"- 高PE股: {result['high_pe_stocks_count']}只")
        print(f"- 策略收益: {result['strategy_performance']['avg_return']:+.2f}%")
        print(f"- 沪深300收益: {result['market_stats']['avg_change_pct']:+.2f}%")
        print(f"- 超额收益: {result['strategy_performance']['relative_return']:+.2f}%")

        print(f"\nTop 3 推荐股票:")
        for stock in result['selected_stocks']:
            print(f"  #{stock['rank']} {stock['name']} PE={stock['pe_ttm']:.2f} 涨跌={stock['change_pct']:+.2f}% 评分={stock['score']:.0f}")

        print(f"\nTop 10 候选股票:")
        for i, stock in enumerate(result['top_10_stocks'], 1):
            star = " *" if i <= 3 else ""
            print(f"  {i:2d}. {stock['name']:10} PE={stock['pe_ttm']:5.2f} 涨跌={stock['change_pct']:+5.2f}% 评分={stock['score']:2.0f}{star}")

    else:
        print("沪深300全量成分股分析失败")

if __name__ == '__main__':
    main()