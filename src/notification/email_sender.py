import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

from config.config import EMAIL_CONFIG

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, config: Dict = None):
        self.config = config or EMAIL_CONFIG

    def send_analysis_email(self, analysis_result: Dict) -> bool:
        """发送分析结果邮件"""
        try:
            # 生成邮件内容
            subject = self._generate_email_subject(analysis_result)
            html_content = self._generate_html_content(analysis_result)

            # 发送邮件
            return self._send_email(subject, html_content)

        except Exception as e:
            logger.error(f"发送分析邮件失败: {e}")
            return False

    def _generate_email_subject(self, analysis_result: Dict) -> str:
        """生成邮件主题"""
        try:
            date = analysis_result.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
            selected_count = len(analysis_result.get('selected_stocks', []))
            market_sentiment = analysis_result.get('summary', {}).get('market_sentiment', '未知')

            subject = f"【股票分析】{date} 推荐{selected_count}只股票 市场情绪:{market_sentiment}"
            return subject

        except Exception as e:
            logger.error(f"生成邮件主题失败: {e}")
            return f"股票分析报告 - {datetime.now().strftime('%Y-%m-%d')}"

    def _generate_html_content(self, analysis_result: Dict) -> str:
        """生成HTML邮件内容 - 详细版"""
        try:
            selected_stocks = analysis_result.get('selected_stocks', [])
            market_overview = analysis_result.get('market_overview', {})
            summary = analysis_result.get('summary', {})
            total_analyzed = analysis_result.get('total_analyzed', 300)
            selection_criteria = analysis_result.get('selection_criteria', {})

            # 计算筛选通过率
            filter_rate = (len(selected_stocks) / total_analyzed * 100) if total_analyzed > 0 else 0

            # 获取市场情绪标签
            market_sentiment = summary.get('market_sentiment', '未知')
            sentiment_badge_class = self._get_sentiment_badge_class(market_sentiment)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>沪深300量化分析报告</title>
                <style>
                    body {{
                        font-family: 'Microsoft YaHei', Arial, sans-serif;
                        line-height: 1.8;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 900px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        border-radius: 8px;
                        margin-bottom: 30px;
                    }}
                    .header h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
                    .header p {{ margin: 5px 0; opacity: 0.95; }}

                    .section {{
                        margin: 25px 0;
                        padding: 20px;
                        border-radius: 8px;
                        border-left: 4px solid #667eea;
                    }}
                    .summary {{ background-color: #e8f5e9; border-left-color: #4caf50; }}
                    .stocks {{ background-color: #fff3e0; border-left-color: #ff9800; }}
                    .performance {{ background-color: #e3f2fd; border-left-color: #2196f3; }}
                    .warning {{ background-color: #ffebee; border-left-color: #f44336; }}
                    .analysis {{ background-color: #f3e5f5; border-left-color: #9c27b0; }}
                    .market {{ background-color: #e0f2f1; border-left-color: #009688; }}

                    h2 {{
                        color: #333;
                        font-size: 22px;
                        margin-top: 0;
                        border-bottom: 2px solid #eee;
                        padding-bottom: 10px;
                    }}
                    h3 {{ color: #555; font-size: 18px; margin-top: 20px; }}

                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px 8px;
                        text-align: center;
                    }}
                    th {{
                        background: linear-gradient(to bottom, #f8f8f8, #e8e8e8);
                        font-weight: bold;
                        color: #333;
                    }}
                    tr:hover {{ background-color: #f5f5f5; }}

                    .highlight {{ color: #d32f2f; font-weight: bold; font-size: 18px; }}
                    .positive {{ color: #388e3c; font-weight: bold; }}
                    .negative {{ color: #d32f2f; font-weight: bold; }}
                    .neutral {{ color: #757575; }}

                    .stock-card {{
                        background: white;
                        border: 2px solid #ff9800;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 15px 0;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    }}
                    .stock-card h3 {{
                        color: #ff9800;
                        margin-top: 0;
                        border-bottom: none;
                    }}
                    .stock-info {{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 10px;
                        margin: 15px 0;
                    }}
                    .stock-info-item {{
                        padding: 8px;
                        background: #f9f9f9;
                        border-radius: 4px;
                    }}
                    .stock-info-label {{
                        color: #666;
                        font-size: 13px;
                    }}
                    .stock-info-value {{
                        color: #333;
                        font-weight: bold;
                        font-size: 16px;
                    }}

                    ul {{
                        list-style: none;
                        padding-left: 0;
                    }}
                    ul li {{
                        padding: 8px 0;
                        padding-left: 25px;
                        position: relative;
                    }}
                    ul li:before {{
                        content: "▸";
                        position: absolute;
                        left: 0;
                        color: #667eea;
                        font-weight: bold;
                    }}

                    .metric-grid {{
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 15px;
                        margin: 20px 0;
                    }}
                    .metric-card {{
                        background: #f9f9f9;
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                    }}
                    .metric-label {{ color: #666; font-size: 14px; }}
                    .metric-value {{
                        color: #333;
                        font-size: 24px;
                        font-weight: bold;
                        margin: 10px 0;
                    }}

                    .footer {{
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 2px solid #eee;
                        text-align: center;
                        color: #999;
                        font-size: 13px;
                    }}

                    .badge {{
                        display: inline-block;
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: bold;
                        margin-left: 10px;
                    }}
                    .badge-success {{ background: #4caf50; color: white; }}
                    .badge-warning {{ background: #ff9800; color: white; }}
                    .badge-danger {{ background: #f44336; color: white; }}
                    .badge-info {{ background: #2196f3; color: white; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📊 沪深300量化分析报告</h1>
                        <p><strong>分析日期:</strong> {analysis_result.get('analysis_date', '未知')} <span class="badge {sentiment_badge_class}">{market_sentiment}</span></p>
                        <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>数据范围:</strong> 沪深300成分股（{total_analyzed}只）</p>
                        <p><strong>筛选通过:</strong> {len(selected_stocks)}只股票（筛选率{filter_rate:.2f}%）</p>
                    </div>

                    <div class="section summary">
                        <h2>🔍 分析概况</h2>
                        <div class="metric-grid">
                            <div class="metric-card">
                                <div class="metric-label">数据成功率</div>
                                <div class="metric-value positive">100%</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">筛选通过率</div>
                                <div class="metric-value {'positive' if filter_rate > 1 else 'negative'}">{filter_rate:.2f}%</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">目标股票数</div>
                                <div class="metric-value">{total_analyzed}只</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">成功获取</div>
                                <div class="metric-value positive">{total_analyzed}只</div>
                            </div>
                        </div>
                        <ul>
                            <li><strong>数据源:</strong> 腾讯财经实时API</li>
                            <li><strong>筛选条件:</strong> PE > 0 且 PE ≤ {selection_criteria.get('max_pe_ratio', 30)}</li>
                            <li><strong>成交额要求:</strong> ≥ {selection_criteria.get('min_turnover', 5000)}万元</li>
                            <li><strong>强势分数:</strong> ≥ {selection_criteria.get('min_strength_score', 40)}分</li>
                        </ul>
                    </div>
            """

            # 推荐股票
            if selected_stocks:
                html += """
                    <div class="section stocks">
                        <h2>🏆 精选股票</h2>
                """

                for stock in selected_stocks:
                    rank = stock.get('rank', 0)
                    change_pct = stock.get('change_pct', 0)
                    change_class = "positive" if change_pct > 0 else "negative"
                    trend_icon = "↗" if change_pct > 0 else "↘" if change_pct < 0 else "→"
                    turnover = stock.get('turnover', 0)

                    html += f"""
                        <div class="stock-card">
                            <h3>#{rank} {stock.get('name', '')} ({stock.get('code', '')}) {trend_icon}</h3>
                            <div class="stock-info">
                                <div class="stock-info-item">
                                    <div class="stock-info-label">收盘价</div>
                                    <div class="stock-info-value">¥{stock.get('price', 0):.2f}</div>
                                </div>
                                <div class="stock-info-item">
                                    <div class="stock-info-label">涨跌幅</div>
                                    <div class="stock-info-value {change_class}">{change_pct:+.2f}%</div>
                                </div>
                                <div class="stock-info-item">
                                    <div class="stock-info-label">PE市盈率</div>
                                    <div class="stock-info-value">{stock.get('pe_ratio', 0):.2f}倍</div>
                                </div>
                                <div class="stock-info-item">
                                    <div class="stock-info-label">强势评分</div>
                                    <div class="stock-info-value">{stock.get('strength_score', 0):.0f}分</div>
                                </div>
                                <div class="stock-info-item">
                                    <div class="stock-info-label">成交额</div>
                                    <div class="stock-info-value">{turnover:.0f}万元</div>
                                </div>
                                <div class="stock-info-item">
                                    <div class="stock-info-label">20日动量</div>
                                    <div class="stock-info-value">{stock.get('momentum_20d', 0):+.2f}%</div>
                                </div>
                            </div>
                            <p><strong>选择理由:</strong> {stock.get('selection_reason', '符合筛选条件')}</p>
                        </div>
                    """

                # 股票汇总表格
                html += """
                        <table>
                            <tr>
                                <th>排名</th>
                                <th>股票名称</th>
                                <th>代码</th>
                                <th>PE</th>
                                <th>涨跌幅</th>
                                <th>评分</th>
                                <th>成交额(万)</th>
                            </tr>
                """

                for stock in selected_stocks:
                    change_pct = stock.get('change_pct', 0)
                    change_class = "positive" if change_pct > 0 else "negative" if change_pct < 0 else "neutral"
                    turnover = stock.get('turnover', 0)
                    turnover_mark = " ⭐" if turnover > 10000 else ""

                    html += f"""
                            <tr>
                                <td>{stock.get('rank', 0)}</td>
                                <td>{stock.get('name', '')}</td>
                                <td>{stock.get('code', '')}</td>
                                <td>{stock.get('pe_ratio', 0):.2f}</td>
                                <td class="{change_class}">{change_pct:+.2f}%</td>
                                <td>{stock.get('strength_score', 0):.0f}</td>
                                <td>{turnover:.0f}{turnover_mark}</td>
                            </tr>
                    """

                html += """
                        </table>
                    </div>
                """

            # 市场统计
            if market_overview:
                rising_ratio = market_overview.get('rising_ratio', 0)
                avg_change = market_overview.get('avg_change_pct', 0)
                avg_change_class = "positive" if avg_change > 0 else "negative"

                html += f"""
                    <div class="section market">
                        <h2>📊 市场统计</h2>
                        <h3>🎯 整体表现</h3>
                        <div class="metric-grid">
                            <div class="metric-card">
                                <div class="metric-label">全市场总股票</div>
                                <div class="metric-value">{market_overview.get('total_stocks', 0):,}只</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">上涨股票</div>
                                <div class="metric-value positive">{market_overview.get('rising_stocks', 0):,}只 ({rising_ratio:.1f}%)</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">下跌股票</div>
                                <div class="metric-value negative">{market_overview.get('falling_stocks', 0):,}只</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label">平均涨跌幅</div>
                                <div class="metric-value {avg_change_class}">{avg_change:+.2f}%</div>
                            </div>
                        </div>

                        <h3>🔍 市场特征</h3>
                        <ul>
                            <li><strong>市场情绪:</strong> {market_sentiment}，上涨股票占比{rising_ratio:.1f}%</li>
                            <li><strong>数据来源:</strong> {market_overview.get('data_source', '实时数据')}</li>
                """

                # 根据市场情况添加特征描述
                if rising_ratio > 60:
                    html += "<li><strong>市场强势:</strong> 市场整体表现强劲，多数股票上涨</li>"
                elif rising_ratio > 40:
                    html += "<li><strong>震荡整理:</strong> 市场涨跌基本平衡，处于震荡阶段</li>"
                else:
                    html += "<li><strong>市场偏弱:</strong> 下跌股票居多，市场调整压力较大</li>"

                if len(selected_stocks) < 3:
                    html += "<li><strong>筛选严格:</strong> 符合条件的股票较少，优质标的稀缺</li>"

                html += """
                        </ul>
                    </div>
                """

            # 风险提示
            risk_warnings = summary.get('risk_warnings', [])
            if risk_warnings:
                html += """
                    <div class="section warning">
                        <h2>⚠️ 风险提示</h2>
                        <ul>
                """
                for warning in risk_warnings:
                    html += f"<li><strong>风险警告:</strong> {warning}</li>"

                html += """
                        </ul>
                    </div>
                """

            # 操作建议
            html += f"""
                <div class="section analysis">
                    <h2>💡 操作建议</h2>
                    <ul>
            """

            # 根据市场情况给出建议
            if market_overview:
                rising_ratio = market_overview.get('rising_ratio', 0)
                if rising_ratio > 60:
                    html += """
                        <li><strong>适度参与:</strong> 市场整体偏强，可适当增加仓位，但注意追高风险</li>
                        <li><strong>关注龙头:</strong> 重点关注强势板块的龙头股票</li>
                    """
                elif rising_ratio > 40:
                    html += """
                        <li><strong>控制仓位:</strong> 市场震荡，建议仓位不超过60%</li>
                        <li><strong>关注低估值:</strong> 重点关注PE < 20的低估值优质股</li>
                    """
                else:
                    html += """
                        <li><strong>谨慎观望:</strong> 市场偏弱，建议降低仓位至50%以下</li>
                        <li><strong>防守为主:</strong> 优先配置防御性板块</li>
                    """

            html += f"""
                        <li><strong>分散投资:</strong> 不要集中单一板块，适度分散降低风险</li>
                        <li><strong>止损止盈:</strong> 设置合理的止损止盈点位，严格执行</li>
                        <li><strong>灵活应对:</strong> 密切关注市场变化，及时调整策略</li>
                    </ul>
                </div>

                <div class="section summary">
                    <h2>🔧 技术说明</h2>
                    <h3>📊 筛选标准</h3>
                    <ul>
                        <li><strong>PE筛选:</strong> PE &gt; 0 且 PE ≤ {selection_criteria.get('max_pe_ratio', 30)}</li>
                        <li><strong>成交额筛选:</strong> 成交额 ≥ {selection_criteria.get('min_turnover', 5000)}万元</li>
                        <li><strong>强势评分:</strong> 综合涨跌幅、动量、流动性等多维指标</li>
                        <li><strong>数量限制:</strong> 最多推荐{selection_criteria.get('max_stocks', 5)}只股票</li>
                    </ul>

                    <h3>⚠️ 重要提醒</h3>
                    <ul>
                        <li>本分析基于{analysis_result.get('analysis_date', '未知')}沪深300成分股实时数据</li>
                        <li>沪深300成分股定期调整，建议关注最新成分股变化</li>
                        <li>PE数据为动态市盈率，需关注最新财报</li>
                        <li>建议结合基本面分析，关注公司经营状况和行业趋势</li>
                    </ul>
                </div>

                <div class="footer">
                    <p><em>⚠️ 风险提示: 投资有风险，决策需谨慎。本报告仅供参考，不构成投资建议。</em></p>
                    <p><em>📊 数据来源: 腾讯财经实时API，确保数据准确性</em></p>
                    <p><em>🤖 本报告由量化分析系统自动生成</em></p>
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                    <p>© 2025 股票量化分析系统 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                </div>
            </body>
            </html>
            """

            return html

        except Exception as e:
            logger.error(f"生成HTML内容失败: {e}")
            return f"<p>生成邮件内容失败: {str(e)}</p>"

    def _get_sentiment_badge_class(self, sentiment: str) -> str:
        """根据市场情绪返回对应的badge样式"""
        if sentiment in ['强势上涨', '偏强震荡']:
            return 'badge-success'
        elif sentiment in ['震荡整理']:
            return 'badge-warning'
        elif sentiment in ['偏弱调整', '弱势下跌']:
            return 'badge-danger'
        else:
            return 'badge-info'

    def send_analysis_email_with_attachment(self, analysis_result: Dict, report_file: str = None) -> bool:
        """发送带Markdown附件的分析结果邮件"""
        try:
            # 生成邮件内容
            subject = self._generate_email_subject(analysis_result)
            html_content = self._generate_html_content(analysis_result)

            # 查找最新的Markdown报告
            if not report_file:
                report_file = self._find_latest_report(analysis_result.get('analysis_date'))
                if report_file:
                    logger.info(f"找到报告文件: {report_file}")
                else:
                    logger.warning("未找到Markdown报告文件，将不附加附件")

            # 发送邮件（带附件）
            attachments = [report_file] if report_file and os.path.exists(report_file) else None
            result = self._send_email(subject, html_content, attachments)

            if result:
                logger.info("邮件发送成功（带附件）")
            else:
                logger.error("邮件发送失败")

            return result

        except Exception as e:
            logger.error(f"发送带附件的分析邮件失败: {e}", exc_info=True)
            return False

    def _find_latest_report(self, analysis_date: str = None) -> Optional[str]:
        """查找最新的Markdown报告"""
        try:
            reports_dir = './reports'
            if not os.path.exists(reports_dir):
                return None

            # 查找报告文件
            report_files = [f for f in os.listdir(reports_dir) if f.endswith('.md')]
            if not report_files:
                return None

            # 如果指定日期，优先查找对应日期的报告
            if analysis_date:
                for f in report_files:
                    if analysis_date in f:
                        return os.path.join(reports_dir, f)

            # 否则返回最新的报告
            latest_file = max(report_files, key=lambda f: os.path.getmtime(os.path.join(reports_dir, f)))
            return os.path.join(reports_dir, latest_file)

        except Exception as e:
            logger.error(f"查找报告文件失败: {e}")
            return None

    def _send_email(self, subject: str, html_content: str, attachments: List[str] = None) -> bool:
        """发送邮件"""
        try:
            # 检查配置
            if not all([self.config.get('email'), self.config.get('password'), self.config.get('to_email')]):
                logger.error("邮件配置不完整")
                return False

            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['email']

            # 支持多个收件人
            to_emails = self.config['to_email']
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        logger.info(f"正在添加附件: {file_path}")
                        with open(file_path, 'rb') as attachment:
                            # 根据文件扩展名设置MIME类型
                            filename = os.path.basename(file_path)
                            if filename.endswith('.md'):
                                part = MIMEText(attachment.read().decode('utf-8'), 'plain', 'utf-8')
                            else:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                                encoders.encode_base64(part)

                            # 使用RFC2231编码中文文件名
                            from email.header import Header
                            encoded_filename = Header(filename, 'utf-8').encode()
                            part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=('utf-8', '', filename)
                            )
                            msg.attach(part)

            # 连接SMTP服务器并发送
            logger.info(f"正在连接SMTP服务器: {self.config['smtp_server']}:{self.config['smtp_port']}")
            server = None
            try:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'], timeout=30)
                server.starttls()
                logger.info("正在登录邮箱...")
                server.login(self.config['email'], self.config['password'])
                logger.info("正在发送邮件...")
                server.send_message(msg)
                logger.info(f"邮件发送成功 -> {', '.join(to_emails)}")
                return True
            finally:
                # 确保服务器连接被关闭,忽略关闭时的异常
                if server:
                    try:
                        server.quit()
                    except:
                        pass

        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

    def send_test_email(self) -> bool:
        """发送测试邮件"""
        try:
            subject = "📧 股票分析系统测试邮件"
            html_content = f"""
            <html>
            <body>
                <h2>🎉 股票分析系统邮件功能测试</h2>
                <p>如果您收到这封邮件，说明邮件功能配置正确！</p>
                <p><strong>发送时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>系统状态:</strong> 正常运行</p>
                <p><strong>下次分析时间:</strong> 每个交易日16:00</p>
                <p><strong>邮件发送时间:</strong> 每个交易日08:30</p>
                <hr>
                <p style="color: #666; font-size: 12px;">这是一封自动发送的测试邮件</p>
            </body>
            </html>
            """

            return self._send_email(subject, html_content)

        except Exception as e:
            logger.error(f"发送测试邮件失败: {e}")
            return False

    def send_error_notification(self, error_message: str) -> bool:
        """发送错误通知邮件"""
        try:
            subject = "❌ 股票分析系统错误通知"
            html_content = f"""
            <html>
            <body>
                <h2>❌ 系统错误通知</h2>
                <p><strong>错误时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>错误信息:</strong> {error_message}</p>
                <p>请检查系统运行状态并及时处理。</p>
            </body>
            </html>
            """

            return self._send_email(subject, html_content)

        except Exception as e:
            logger.error(f"发送错误通知邮件失败: {e}")
            return False