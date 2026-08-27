import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
import requests
import time

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
        self._last_market_mode = None  # 缓存上次趋势模式，用于缓冲带逻辑

    def detect_market_trend(self) -> Dict:
        """检测沪深300趋势：价格vs MA60，带±2%缓冲带避免频繁切换"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d')
            url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000300,day,{start_date},{end_date},100,qfq'
            resp = requests.get(url, timeout=10)
            data = resp.json()
            klines = data.get('data', {}).get('sh000300', {}).get('day', [])
            if not klines:
                klines = data.get('data', {}).get('sh000300', {}).get('qfqday', [])
            if not klines or len(klines) < 60:
                logger.warning("沪深300K线数据不足60根，默认防守模式")
                return {'mode': 'defensive', 'price': 0, 'ma60': 0, 'reason': '数据不足'}

            closes = [float(k[2]) for k in klines]
            current_price = closes[-1]
            ma60 = np.mean(closes[-60:])

            # 缓冲带逻辑：站上MA60*1.02切进攻，跌破MA60*0.98切防守，中间维持上次模式
            upper_band = ma60 * 1.02
            lower_band = ma60 * 0.98

            if current_price > upper_band:
                mode = 'offensive'
            elif current_price < lower_band:
                mode = 'defensive'
            else:
                # 在缓冲带内，维持上次模式（首次默认防守）
                mode = self._last_market_mode if self._last_market_mode else 'defensive'
                logger.info(f"在缓冲带内 [{lower_band:.2f}, {upper_band:.2f}]，维持{mode}模式")

            self._last_market_mode = mode
            diff_pct = (current_price / ma60 - 1) * 100
            logger.info(f"趋势检测: 沪深300={current_price:.2f}, MA60={ma60:.2f}(±2%), 偏离{diff_pct:+.2f}%, 模式={mode}")

            return {
                'mode': mode,
                'price': current_price,
                'ma60': round(ma60, 2),
                'upper_band': round(upper_band, 2),
                'lower_band': round(lower_band, 2),
                'reason': f'沪深300({current_price:.2f}) vs MA60({ma60:.2f}), 偏离{diff_pct:+.1f}%'
            }
        except Exception as e:
            logger.error(f"趋势检测失败: {e}，默认防守模式")
            return {'mode': 'defensive', 'price': 0, 'ma60': 0, 'reason': f'检测失败: {e}'}

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

            # 4. 趋势检测 + 模式切换选股
            trend_info = self.detect_market_trend()
            market_mode = trend_info['mode']

            if market_mode == 'offensive':
                logger.info("当前为牛市模式（进攻），使用进攻评分选股")
                selected_stocks = self.stock_filter.select_top_stocks_offensive(all_stock_data)
            else:
                logger.info("当前为熊市模式（防守），使用超防守评分选股")
                selected_stocks = self.stock_filter.select_top_stocks_ultra_defensive(all_stock_data)

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
                'market_trend': trend_info,
                'market_mode': market_mode,
                'scoring_mode': market_mode if market_mode in ('offensive', 'defensive') else 'basic',
                'selected_stocks': selected_stocks,
                'total_analyzed': len(all_stock_data),
                'selection_criteria': STOCK_FILTER_CONFIG,
                'summary': self._generate_analysis_summary(selected_stocks, market_overview)
            }

            # 7. 止损检查（对比上次推荐持仓的当前价格）
            stop_loss_warnings = self.check_stop_loss()
            analysis_result['stop_loss_warnings'] = stop_loss_warnings

            # 8. 保存分析结果
            self._save_analysis_result(analysis_result)

            # 9. 自动生成Markdown报告
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

    def check_stop_loss(self) -> List[Dict]:
        """检查上次推荐股票是否触及止损线 -5%"""
        warnings = []
        try:
            prev_analysis = self.get_latest_analysis()
            if not prev_analysis:
                logger.info("无历史分析结果，跳过止损检查")
                return warnings

            prev_stocks = prev_analysis.get('selected_stocks', [])
            if not prev_stocks:
                return warnings

            logger.info(f"开始止损检查，上次推荐 {len(prev_stocks)} 只股票")
            stop_loss_pct = STOCK_FILTER_CONFIG.get('stop_loss_pct', -0.05)

            for prev_stock in prev_stocks:
                code = prev_stock.get('code')
                name = prev_stock.get('name')
                orig_price = prev_stock.get('price', 0)
                if not code or not orig_price:
                    continue

                # 获取当前价格
                current_data = self.data_fetcher.get_stock_realtime_data(code)
                if not current_data:
                    continue

                current_price = current_data.get('price', 0)
                if current_price == 0:
                    continue

                # 计算收益率
                pnl_pct = (current_price / orig_price - 1)
                if pnl_pct <= stop_loss_pct:
                    warnings.append({
                        'code': code,
                        'name': name,
                        'orig_price': orig_price,
                        'current_price': current_price,
                        'pnl_pct': pnl_pct * 100,
                        'reason': f'触及止损线 {stop_loss_pct*100:.0f}%'
                    })
                    logger.warning(f"止损警告: {name}({code}) {orig_price:.2f}→{current_price:.2f} ({pnl_pct*100:+.2f}%)")

            if warnings:
                logger.warning(f"止损检查完成，发现 {len(warnings)} 只触及止损线")
            else:
                logger.info("止损检查完成，无股票触及止损线")

        except Exception as e:
            logger.error(f"止损检查失败: {e}")

        return warnings

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
            trend_info = analysis_result.get('market_trend', {})
            market_mode = analysis_result.get('market_mode', 'unknown')

            date_obj = datetime.strptime(analysis_date, '%Y-%m-%d')
            date_cn = date_obj.strftime('%Y年%m月%d日')

            is_bull = market_mode == 'offensive'
            mode_label = '进攻' if is_bull else '防守'
            trend_price = trend_info.get('price', 0)
            trend_ma60 = trend_info.get('ma60', 0)
            diff_pct = (trend_price / trend_ma60 - 1) * 100 if trend_ma60 > 0 else 0
            sentiment = analysis_result.get('summary', {}).get('market_sentiment', '未知')
            rising_ratio = market_overview.get('rising_ratio', 0)
            avg_chg = market_overview.get('avg_change_pct', 0)

            md_content = f"# {date_cn} 量化选股\n\n"
            md_content += f"**{mode_label}模式** | "
            md_content += f"沪深300 `{trend_price:.2f}` {'>' if is_bull else '<'} MA60 `{trend_ma60:.2f}` | "
            md_content += f"偏离 `{diff_pct:+.1f}%`\n\n"
            md_content += f"市场: {sentiment} | "
            md_content += f"涨跌比 {market_overview.get('rising_stocks', 0)}/{market_overview.get('falling_stocks', 0)} | "
            md_content += f"均幅 {avg_chg:+.2f}%\n\n"
            md_content += "---\n\n"

            # 选股逻辑说明
            if is_bull:
                md_content += "**选股逻辑（进攻）**: 基础分(技术面+估值+盈利+安全+股息) + 动量加分(>15%:+12, >10%:+8, >5%:+4) + 高成长加分(>30%:+5)\n\n"
            else:
                md_content += "**选股逻辑（防守）**: 安全性(50) + 低PB(25) + 高ROE(25) + 温和动量(5) = 满分105\n\n"

            # 止损警告（如果有）
            stop_loss_warnings = analysis_result.get('stop_loss_warnings', [])
            if stop_loss_warnings:
                md_content += "## ⚠️ 止损警告\n\n"
                md_content += "| 股票 | 原价 | 现价 | 收益率 |\n"
                md_content += "|:-----|-----:|-----:|-------:|\n"
                for w in stop_loss_warnings:
                    md_content += f"| **{w.get('name')} {w.get('code')}** | {w.get('orig_price', 0):.2f} | {w.get('current_price', 0):.2f} | **{w.get('pnl_pct', 0):+.2f}%** |\n"
                md_content += "\n"

            if is_bull:
                md_content += self._build_offensive_table(selected_stocks)
            else:
                md_content += self._build_defensive_table(selected_stocks)

            # 统计数据来源
            ifind_count = sum(1 for s in selected_stocks if s.get('data_source') == 'ifind')
            tencent_count = sum(1 for s in selected_stocks if s.get('data_source') == 'tencent')
            if ifind_count > 0:
                md_content += f"\n<sub>数据源: iFinD {ifind_count}只"
                if tencent_count > 0:
                    md_content += f" + 腾讯 {tencent_count}只"
                md_content += "</sub>\n"
            elif tencent_count > 0:
                md_content += f"\n<sub>数据源: 腾讯财经 {tencent_count}只</sub>\n"

            md_content += "\n---\n\n"
            md_content += f"PE≤{config.get('max_pe_ratio', 30)} | "
            md_content += f"持仓≤{config.get('max_stocks', 6)}只 | "
            md_content += f"止损{config.get('stop_loss_pct', -0.05)*100:.0f}% | "
            md_content += f"调仓7日 | "
            md_content += f"分析{total_analyzed}只\n\n"
            md_content += f"<sub>{datetime.now().strftime('%H:%M:%S')} · v4.0 · 仅供参考，不构成投资建议</sub>\n"

            month_dir = f"./reports/{date_obj.strftime('%Y-%m')}"
            os.makedirs(month_dir, exist_ok=True)
            output_file = f"{month_dir}/{date_cn}沪深300分析结果.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            logger.info(f"Markdown报告已生成: {output_file}")
            return True

        except Exception as e:
            logger.error(f"生成Markdown报告失败: {e}")
            return False

    def _build_offensive_table(self, stocks: List[Dict]) -> str:
        """进攻模式股票表格（含分项得分）"""
        table = "| 排名 | 股票 | 价格 | PE | ROE | 动量 | 增长 | 技术 | 估值 | 盈利 | 安全 | 加分 | 总分 |\n"
        table += "|:----:|:-----|-----:|----:|----:|-----:|-----:|:----:|:----:|:----:|:----:|:----:|-----:|\n"
        for s in stocks:
            roe_d = f"{s.get('roe', 0):.1f}%" if s.get('roe') else "-"
            growth_d = f"{s.get('profit_growth', 0):+.0f}%" if s.get('profit_growth') else "-"
            name = f"{s.get('name', '-')} {s.get('code', '-')}"
            detail = s.get('strength_score_detail', {})
            breakdown = detail.get('breakdown', {})
            tech = breakdown.get('technical', 0)
            val = breakdown.get('valuation', 0)
            prof = breakdown.get('profitability', 0)
            safe = breakdown.get('safety', 0)
            bonus = detail.get('bonus', 0)
            table += f"| {s.get('rank', 0)} | {name} "
            table += f"| {s.get('price', 0):.2f} | {s.get('pe_ratio', 0):.1f} | {roe_d} "
            table += f"| {s.get('momentum_20d', 0):+.1f}% | {growth_d} "
            table += f"| {tech} | {val} | {prof} | {safe} | {bonus} "
            table += f"| **{s.get('strength_score', 0):.0f}** |\n"
        return table

    def _build_defensive_table(self, stocks: List[Dict]) -> str:
        """防守模式股票表格（含分项得分，隐藏波动/回撤原始值，低波动+小回撤合并为安全性）"""
        table = "| 排名 | 股票 | 价格 | PB | ROE | 安全性 | 低PB | 高ROE | 动量加分 | 总分 |\n"
        table += "|:----:|:-----|-----:|----:|----:|:------:|:----:|:-----:|:--------:|-----:|\n"
        for s in stocks:
            roe_d = f"{s.get('roe', 0):.1f}%" if s.get('roe') else "-"
            name = f"{s.get('name', '-')} {s.get('code', '-')}"
            detail = s.get('strength_score_detail', {})
            breakdown = detail.get('breakdown', {})
            safety = breakdown.get('low_volatility', 0) + breakdown.get('small_drawdown', 0)
            lpb = breakdown.get('low_pb', 0)
            hroe = breakdown.get('high_roe', 0)
            mb = breakdown.get('momentum_bonus', 0)
            table += f"| {s.get('rank', 0)} | {name} "
            table += f"| {s.get('price', 0):.2f} | {s.get('pb_ratio', 0):.2f} | {roe_d} "
            table += f"| {safety} | {lpb} | {hroe} | {mb} "
            table += f"| **{s.get('strength_score', 0):.0f}** |\n"
        return table
