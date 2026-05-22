import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os

from src.data.data_fetcher import StockDataFetcher
from src.data.async_data_fetcher import batch_get_stock_data_sync, get_market_overview_sync
from src.analysis.stock_filter import StockFilter
from config.config import STOCK_FILTER_CONFIG, DATA_CONFIG

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, use_async: bool = True):
        """
        初始化市场分析器

        Args:
            use_async: 是否使用异步数据获取器 (默认True,大幅提升性能)
        """
        self.data_fetcher = StockDataFetcher()
        self.stock_filter = StockFilter()
        self.analysis_results = {}
        self.use_async = use_async

    def _load_csi300_stocks(self) -> pd.DataFrame:
        """加载沪深300成分股列表 - 优先使用本地缓存"""
        try:
            # 方法1: 从本地JSON文件加载(快速)
            local_file = './data/csi300_stocks.json'
            if os.path.exists(local_file):
                logger.info("从本地文件加载沪深300成分股列表...")
                with open(local_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stocks = data['stocks']
                    logger.info(f"成功从本地加载 {len(stocks)} 只沪深300成分股 (更新日期: {data.get('update_date', '未知')})")
                    return pd.DataFrame(stocks)

            # 方法2: 使用akshare在线获取(慢速,作为备用)
            logger.warning("本地文件不存在,尝试在线获取沪深300成分股列表(可能较慢)...")
            import akshare as ak
            csi300_stocks = ak.index_stock_cons(symbol="000300")
            if not csi300_stocks.empty:
                logger.info(f"在线获取成功: {len(csi300_stocks)} 只")
                # 保存到本地以便下次使用
                result = pd.DataFrame({
                    'code': csi300_stocks['品种代码'].tolist(),
                    'name': csi300_stocks['品种名称'].tolist()
                })
                # 保存到本地
                os.makedirs('./data', exist_ok=True)
                save_data = {
                    'update_date': datetime.now().strftime('%Y-%m-%d'),
                    'note': '沪深300成分股列表 - 自动生成',
                    'stocks': result.to_dict('records')
                }
                with open(local_file, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存到本地文件: {local_file}")
                return result

            logger.error("无法获取沪深300成分股列表")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"加载沪深300成分股列表失败: {e}")
            return pd.DataFrame()

    def run_daily_analysis(self) -> Dict:
        """执行每日盘后分析"""
        logger.info("开始执行盘后分析...")

        try:
            # 1. 获取沪深300成分股列表（优先使用本地缓存）
            a_share_list = self._load_csi300_stocks()
            if a_share_list.empty:
                logger.error("无法获取沪深300成分股列表")
                return {}

            logger.info(f"开始分析沪深300成分股，共 {len(a_share_list)} 只")

            # 3. 批量获取股票数据
            stock_codes = a_share_list['code'].tolist()

            if self.use_async:
                # 使用异步获取器 - 大幅提升性能
                logger.info("使用异步批量获取模式 (性能优化)")
                all_stock_data = batch_get_stock_data_sync(
                    stock_codes,
                    calculate_momentum=True,
                    include_fundamental=True,
                    max_concurrent=20  # 可以调整并发数
                )
            else:
                # 使用原有的同步方式 - 兼容模式
                logger.info("使用同步批量获取模式 (兼容模式)")
                batch_size = 100
                all_stock_data = []

                for i in range(0, len(stock_codes), batch_size):
                    batch = stock_codes[i:i+batch_size]
                    logger.info(f"处理第 {i//batch_size + 1} 批股票，共 {len(batch)} 只")

                    batch_data = self.data_fetcher.batch_get_stock_data(batch)
                    all_stock_data.extend(batch_data)

            logger.info(f"成功获取 {len(all_stock_data)} 只股票的数据")

            # 4. 筛选股票
            selected_stocks = self.stock_filter.select_top_stocks(all_stock_data)

            # 5. 获取市场概况
            if self.use_async:
                market_overview = get_market_overview_sync()
            else:
                market_overview = self.data_fetcher.get_market_overview()

            # 6. 生成分析结果
            analysis_result = {
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'analysis_time': datetime.now().strftime('%H:%M:%S'),
                'market_overview': market_overview,
                'selected_stocks': selected_stocks,
                'total_analyzed': len(all_stock_data),
                'selection_criteria': STOCK_FILTER_CONFIG,
                'summary': self._generate_analysis_summary(selected_stocks, market_overview)
            }

            # 7. 保存分析结果
            self._save_analysis_result(analysis_result)

            # 8. 自动生成Markdown报告
            self._generate_markdown_report(analysis_result)

            logger.info("盘后分析完成")
            return analysis_result

        except Exception as e:
            logger.error(f"盘后分析失败: {e}")
            return {}

    def _generate_analysis_summary(self, selected_stocks: List[Dict], market_overview: Dict) -> Dict:
        """生成分析摘要"""
        try:
            summary = {
                'market_sentiment': self._analyze_market_sentiment(market_overview),
                'stock_recommendations': [],
                'risk_warnings': [],
                'key_metrics': {}
            }

            # 分析选中的股票
            for stock in selected_stocks:
                recommendation = {
                    'rank': stock.get('rank', 0),
                    'code': stock.get('code', ''),
                    'name': stock.get('name', ''),
                    'current_price': stock.get('price', 0),
                    'change_pct': stock.get('change_pct', 0),
                    'pe_ratio': stock.get('pe_ratio', 0),
                    'momentum_20d': stock.get('momentum_20d', 0),
                    'strength_score': stock.get('strength_score', 0),
                    'reason': stock.get('selection_reason', '')
                }
                summary['stock_recommendations'].append(recommendation)

            # 关键指标
            if selected_stocks:
                prices = [s.get('price', 0) for s in selected_stocks]
                pe_ratios = [s.get('pe_ratio', 0) for s in selected_stocks if s.get('pe_ratio', 0) > 0]
                momentums = [s.get('momentum_20d', 0) for s in selected_stocks]

                summary['key_metrics'] = {
                    'avg_price': np.mean(prices),
                    'avg_pe_ratio': np.mean(pe_ratios) if pe_ratios else 0,
                    'avg_momentum': np.mean(momentums),
                    'price_range': f"{min(prices):.2f} - {max(prices):.2f}",
                    'pe_range': f"{min(pe_ratios):.2f} - {max(pe_ratios):.2f}" if pe_ratios else "N/A"
                }

            # 风险提示
            if market_overview.get('rising_ratio', 0) < 30:
                summary['risk_warnings'].append("市场整体表现较弱，注意控制仓位")

            if any(s.get('pe_ratio', 0) > 25 for s in selected_stocks):
                summary['risk_warnings'].append("部分推荐股票PE较高，注意估值风险")

            return summary

        except Exception as e:
            logger.error(f"生成分析摘要失败: {e}")
            return {}

    def _analyze_market_sentiment(self, market_overview: Dict) -> str:
        """分析市场情绪"""
        try:
            rising_ratio = market_overview.get('rising_ratio', 0)
            avg_change = market_overview.get('avg_change_pct', 0)

            if rising_ratio > 70 and avg_change > 1:
                return "强势上涨"
            elif rising_ratio > 60 and avg_change > 0.5:
                return "偏强震荡"
            elif rising_ratio > 40:
                return "震荡整理"
            elif rising_ratio > 30:
                return "偏弱调整"
            else:
                return "弱势下跌"

        except Exception as e:
            logger.error(f"分析市场情绪失败: {e}")
            return "未知"

    def _save_analysis_result(self, result: Dict) -> bool:
        """保存分析结果"""
        try:
            # 确保目录存在
            os.makedirs('./logs/analysis', exist_ok=True)

            # 保存到文件
            filename = f"./logs/analysis/analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"分析结果已保存到: {filename}")
            return True

        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")
            return False

    def get_latest_analysis(self) -> Optional[Dict]:
        """获取最新的分析结果"""
        try:
            log_dir = './logs/analysis'
            if not os.path.exists(log_dir):
                return None

            # 查找最新的分析文件
            analysis_files = [f for f in os.listdir(log_dir) if f.startswith('analysis_') and f.endswith('.json')]
            if not analysis_files:
                return None

            latest_file = max(analysis_files)
            filepath = os.path.join(log_dir, latest_file)

            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)

            return result

        except Exception as e:
            logger.error(f"获取最新分析结果失败: {e}")
            return None

    def generate_performance_report(self, days: int = 7) -> Dict:
        """生成表现报告"""
        try:
            # 这里可以实现回测功能，分析过去推荐股票的表现
            # 简化实现，返回基本统计
            latest_analysis = self.get_latest_analysis()
            if not latest_analysis:
                return {}

            selected_stocks = latest_analysis.get('selected_stocks', [])
            current_data = []

            # 获取当前价格
            for stock in selected_stocks:
                current_stock_data = self.data_fetcher.get_stock_realtime_data(stock['code'])
                if current_stock_data:
                    current_data.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'original_price': stock['price'],
                        'current_price': current_stock_data['price'],
                        'performance': (current_stock_data['price'] / stock['price'] - 1) * 100
                    })

            report = {
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'analysis_date': latest_analysis.get('analysis_date'),
                'stock_performance': current_data,
                'summary': {
                    'total_stocks': len(current_data),
                    'avg_performance': np.mean([s['performance'] for s in current_data]) if current_data else 0,
                    'best_performer': max(current_data, key=lambda x: x['performance']) if current_data else None,
                    'worst_performer': min(current_data, key=lambda x: x['performance']) if current_data else None
                }
            }

            return report

        except Exception as e:
            logger.error(f"生成表现报告失败: {e}")
            return {}
    def _generate_markdown_report(self, analysis_result: Dict) -> bool:
        """生成Markdown格式报告"""
        try:
            from datetime import datetime
            
            analysis_date = analysis_result.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
            selected_stocks = analysis_result.get('selected_stocks', [])
            total_analyzed = analysis_result.get('total_analyzed', 300)
            config = analysis_result.get('selection_criteria', {})
            market_overview = analysis_result.get('market_overview', {})
            
            # 转换日期格式
            date_obj = datetime.strptime(analysis_date, '%Y-%m-%d')
            date_cn = date_obj.strftime('%Y年%m月%d日')
            
            # 生成Markdown内容
            md_content = f"""# 📊 {date_cn}沪深300成分股分析结果

## 🔍 **分析概况**

### 📅 **基本信息**
- **分析日期**: {analysis_date}
- **分析时间**: {analysis_result.get('analysis_time', '--')}
- **数据源**: 实时交易数据
- **股票池**: 沪深300成分股
- **目标股票数**: {total_analyzed}只
- **筛选条件**: PE ≤ {config.get('max_pe_ratio', 30)}, 换手率 ≥ {config.get('min_turnover_rate', 1.0)}%

## 🏆 **Top {len(selected_stocks)} 精选股票**

"""
            
            # 添加每只股票的详细信息
            for stock in selected_stocks:
                trend = "↗" if stock.get('change_pct', 0) > 0 else "↘" if stock.get('change_pct', 0) < 0 else "→"
                md_content += f"""### #{stock.get('rank', 0)} {stock['name']} ({stock['code']}) [{trend}]
- **价格**: ¥{stock.get('price', 0):.2f}
- **涨跌幅**: {stock.get('change_pct', 0):+.2f}%
- **PE**: {stock.get('pe_ratio', 0):.2f}倍
- **强势分数**: {stock.get('strength_score', 0):.0f}分
"""
                
                # 添加分项得分
                score_detail = stock.get('strength_score_detail', {})
                if score_detail:
                    breakdown = score_detail.get('breakdown', {})
                    md_content += f"""- **分项得分**:
  - 技术面: {breakdown.get('technical', 0)}分
  - 估值: {breakdown.get('valuation', 0)}分
  - 盈利能力: {breakdown.get('profitability', 0)}分
  - 安全性: {breakdown.get('safety', 0)}分
  - 股息: {breakdown.get('dividend', 0)}分
- **评级**: {score_detail.get('grade', '')}
"""
                
                md_content += f"""- **选择理由**: {stock.get('selection_reason', '符合筛选条件')}

"""
            
            # 添加候选股票表格
            if selected_stocks:
                md_content += f"""## 📋 **Top {len(selected_stocks)} 候选股票**

> ⚠️ **免责声明**: 本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。

| 排名 | 股票名称 | 代码 | 股价 | PB | PE | PR | ROE | 20日动量 | 评分 | 评级 | 技术面 | 估值 | 盈利 | 安全 | 股息 |
|------|----------|------|------|------|------|------|-------|---------|-----|------|--------|------|------|------|------|
"""

                for stock in selected_stocks:
                    roe_display = f"{stock.get('roe', 0):.1f}%" if stock.get('roe') else "-"
                    grade = stock.get('strength_grade', '-')
                    
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
                    
                    # 获取股价和计算总市值（如果可能获取总股本数据）
                    price = stock.get('price', 0)
                    # 尝试从股票数据中获取总市值信息，如果不存在则尝试计算
                    market_cap = stock.get('market_cap', None)  # 单位是万元
                    if market_cap:
                        market_cap_display = f"{market_cap/10000:.2f}"  # 转换为亿元并格式化
                    else:
                        # 尝试使用总股本计算总市值
                        total_shares = stock.get('total_shares', None)  # 单位是万股
                        if total_shares and price > 0:
                            market_cap = price * total_shares * 10000  # 总市值 = 股价 * 总股本
                            market_cap_display = f"{market_cap/100000000:.2f}"  # 转换为亿元并格式化
                        else:
                            market_cap_display = "-"  # 无法获取总市值，显示为"-"
                    
                    # 计算PR（市赚率）
                    pe_ratio = stock.get('pe_ratio', 0)
                    roe = stock.get('roe', 0)
                    roe_decimal = roe / 100 if roe > 0 else 0  # ROE是百分比形式，需要转换为小数
                    pr_display = "-"
                    if pe_ratio > 0 and roe_decimal > 0:
                        pr = pe_ratio / (100 * roe_decimal)
                        pr_display = f"{pr:.2f}"
                    
                    momentum_20d = stock.get('momentum_20d', 0)
                    
                    md_content += f"|  {stock.get('rank', 0)} | {stock.get('name', '-')} | {stock.get('code', '-')} | {price:.2f} | {stock.get('pb_ratio', 0):.2f} | {stock.get('pe_ratio', 0):.2f} | {pr_display} | {roe_display} | {momentum_20d:+.2f}% | {stock.get('strength_score', 0):.0f} | {grade} | {tech_score} | {val_score} | {prof_score} | {safe_score} | {div_score} |\n"
            
            # 添加筛选统计
            md_content += f"""
## 📊 **沪深300筛选统计**

### 🔍 **筛选结果**
- **沪深300总数**: {total_analyzed}只
- **筛选通过**: {len(selected_stocks)}只
- **筛选通过率**: {len(selected_stocks)/total_analyzed*100 if total_analyzed > 0 else 0:.2f}%

### 📊 **筛选标准**
- **PE筛选**: PE ≤ {config.get('max_pe_ratio', 30)}
- **换手率筛选**: 换手率 ≥ {config.get('min_turnover_rate', 1.0)}%
- **强势分数**: ≥ {config.get('min_strength_score', 50)}
- **数量限制**: 最多推荐{config.get('max_stocks', 3)}只股票

## 📊 **市场统计**

### 🎯 **整体表现**
- **全市场总股票**: {market_overview.get('total_stocks', 0):,}只
- **上涨股票**: {market_overview.get('rising_stocks', 0):,}只 ({market_overview.get('rising_ratio', 0):.2f}%)
- **下跌股票**: {market_overview.get('falling_stocks', 0):,}只
- **全市场平均涨跌幅**: {market_overview.get('avg_change_pct', 0):.2f}%
- **市场情绪**: {analysis_result.get('summary', {}).get('market_sentiment', '未知')}

## 🎯 **投资分析**

### 📈 **投资价值**
- **市场代表性**: 基于沪深300成分股,代表A股核心优质资产
- **估值安全**: 严格PE筛选避免高风险标的  
- **流动性保证**: 成交额要求确保充足的交易流动性
- **技术筛选**: 基于20日动量、强势分数等多维度技术指标

### ⚠️ **风险提示**
1. **市场风险**: 股市有风险,投资需谨慎
2. **估值风险**: PE为历史数据,需关注最新财报
3. **流动性风险**: 市场波动可能影响交易流动性
4. **投资建议**: 本报告仅供参考,不构成投资建议

## 💡 **技术说明**

### 🔧 **策略特点**
- **多维度筛选**: PE估值、成交额、动量、强势评分综合评估
- **20日动量**: 基于20日价格动量捕捉趋势
- **成交额过滤**: 确保足够的市场流动性
- **智能评分**: 综合涨跌幅、动量、流动性等指标

### 📊 **数据来源**
- **股票池**: 沪深300成分股
- **数据频率**: 实时交易数据
- **更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析版本**: v3.0 (量化策略优化版)
**数据范围**: 沪深300成分股分析 ✓
"""
            
            # 确保reports目录存在
            os.makedirs('./reports', exist_ok=True)

            # 保存文件
            output_file = f"./reports/{date_cn}沪深300分析结果.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            logger.info(f"Markdown报告已生成: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"生成Markdown报告失败: {e}")
            return False
