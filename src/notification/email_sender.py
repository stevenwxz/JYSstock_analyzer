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
        """生成HTML邮件内容"""
        try:
            selected_stocks = analysis_result.get('selected_stocks', [])
            market_overview = analysis_result.get('market_overview', {})
            summary = analysis_result.get('summary', {})

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>股票分析报告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .stock-card {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                    .rank-1 {{ border-left: 5px solid #gold; }}
                    .rank-2 {{ border-left: 5px solid #silver; }}
                    .rank-3 {{ border-left: 5px solid #cd7f32; }}
                    .positive {{ color: #ff4444; }}
                    .negative {{ color: #00aa00; }}
                    .metric {{ display: inline-block; margin: 5px 10px; }}
                    .market-overview {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin: 15px 0; }}
                    .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📈 股票量化分析报告</h1>
                    <p><strong>分析日期:</strong> {analysis_result.get('analysis_date', '未知')}</p>
                    <p><strong>分析时间:</strong> {analysis_result.get('analysis_time', '未知')}</p>
                    <p><strong>市场情绪:</strong> {summary.get('market_sentiment', '未知')}</p>
                </div>
            """

            # 市场概况
            if market_overview:
                html += f"""
                <div class="market-overview">
                    <h2>🌍 市场概况</h2>
                    <div class="metric">总股票数: {market_overview.get('total_stocks', 0)}</div>
                    <div class="metric">上涨股票: {market_overview.get('rising_stocks', 0)}</div>
                    <div class="metric">下跌股票: {market_overview.get('falling_stocks', 0)}</div>
                    <div class="metric">上涨比例: {market_overview.get('rising_ratio', 0):.1f}%</div>
                    <div class="metric">平均涨跌幅: {market_overview.get('avg_change_pct', 0):.2f}%</div>
                </div>
                """

            # 推荐股票
            if selected_stocks:
                html += "<h2>⭐ 推荐股票</h2>"

                for stock in selected_stocks:
                    rank = stock.get('rank', 0)
                    rank_class = f"rank-{rank}" if rank <= 3 else ""
                    change_class = "positive" if stock.get('change_pct', 0) > 0 else "negative"

                    html += f"""
                    <div class="stock-card {rank_class}">
                        <h3>#{rank} {stock.get('name', '')} ({stock.get('code', '')})</h3>
                        <div class="metric">💰 价格: ¥{stock.get('price', 0):.2f}</div>
                        <div class="metric">📊 涨跌幅: <span class="{change_class}">{stock.get('change_pct', 0):+.2f}%</span></div>
                        <div class="metric">📈 PE: {stock.get('pe_ratio', 0):.2f}</div>
                        <div class="metric">🚀 20日动量: {stock.get('momentum_20d', 0):.2f}%</div>
                        <div class="metric">⚡ 强势分数: {stock.get('strength_score', 0):.1f}</div>
                        <p><strong>选择理由:</strong> {stock.get('selection_reason', '无')}</p>
                    </div>
                    """

            # 关键指标
            key_metrics = summary.get('key_metrics', {})
            if key_metrics:
                html += f"""
                <div class="market-overview">
                    <h2>📊 关键指标</h2>
                    <div class="metric">平均价格: ¥{key_metrics.get('avg_price', 0):.2f}</div>
                    <div class="metric">平均PE: {key_metrics.get('avg_pe_ratio', 0):.2f}</div>
                    <div class="metric">平均动量: {key_metrics.get('avg_momentum', 0):.2f}%</div>
                    <div class="metric">价格区间: ¥{key_metrics.get('price_range', 'N/A')}</div>
                    <div class="metric">PE区间: {key_metrics.get('pe_range', 'N/A')}</div>
                </div>
                """

            # 风险提示
            risk_warnings = summary.get('risk_warnings', [])
            if risk_warnings:
                html += "<h2>⚠️ 风险提示</h2>"
                for warning in risk_warnings:
                    html += f'<div class="warning">⚠️ {warning}</div>'

            # 免责声明
            html += f"""
                <div style="margin-top: 30px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; font-size: 12px; color: #666;">
                    <h3>📋 免责声明</h3>
                    <p>• 本报告仅供参考，不构成投资建议</p>
                    <p>• 股市有风险，投资需谨慎</p>
                    <p>• 请根据自身风险承受能力谨慎投资</p>
                    <p>• 过往表现不代表未来收益</p>
                    <p>• 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </body>
            </html>
            """

            return html

        except Exception as e:
            logger.error(f"生成HTML内容失败: {e}")
            return f"<p>生成邮件内容失败: {str(e)}</p>"

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
            msg['To'] = self.config['to_email']
            msg['Subject'] = subject

            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)

            # 连接SMTP服务器并发送
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['email'], self.config['password'])
                server.send_message(msg)

            logger.info(f"邮件发送成功 -> {self.config['to_email']}")
            return True

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