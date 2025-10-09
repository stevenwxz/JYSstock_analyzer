#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_csi300_report():
    """发送沪深300分析报告邮件"""

    # 读取分析报告
    report_file = '2025年9月30日沪深300全量分析结果.md'

    if not os.path.exists(report_file):
        print(f"错误: 找不到报告文件 {report_file}")
        return False

    with open(report_file, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # 邮件配置
    smtp_server = "smtp.qq.com"
    smtp_port = 587
    sender_email = "1120311927@qq.com"
    sender_password = "rnhtflrxhscwhiah"  # QQ邮箱授权码
    receiver_email = "1120311927@qq.com"

    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "📊 2025年9月30日沪深300量化分析报告"

    # 创建HTML邮件内容
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .summary {{ background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .stocks {{ background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .performance {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .highlight {{ color: #d32f2f; font-weight: bold; }}
            .positive {{ color: #388e3c; }}
            .negative {{ color: #d32f2f; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 沪深300量化分析报告</h1>
            <p><strong>分析日期:</strong> 2025年9月30日</p>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>数据范围:</strong> 沪深300全量成分股（300只）</p>
        </div>

        <div class="summary">
            <h2>🔍 分析概况</h2>
            <ul>
                <li><strong>数据获取成功率:</strong> 100.0% (300/300只)</li>
                <li><strong>PE筛选通过:</strong> 180只 (60%通过率)</li>
                <li><strong>亏损股剔除:</strong> 29只</li>
                <li><strong>高PE股剔除:</strong> 91只 (PE>30)</li>
                <li><strong>筛选条件:</strong> PE-TTM > 0 且 PE-TTM ≤ 30</li>
            </ul>
        </div>

        <div class="stocks">
            <h2>🏆 Top 3 精选股票</h2>
            <table>
                <tr>
                    <th>排名</th>
                    <th>股票名称</th>
                    <th>代码</th>
                    <th>收盘价</th>
                    <th>涨跌幅</th>
                    <th>PE-TTM</th>
                    <th>评分</th>
                </tr>
                <tr>
                    <td>1</td>
                    <td>阿特斯</td>
                    <td>688472</td>
                    <td>¥13.44</td>
                    <td class="positive">+4.27%</td>
                    <td>28.50倍</td>
                    <td>70分</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>中国中冶</td>
                    <td>601618</td>
                    <td>¥3.85</td>
                    <td class="positive">+10.00%</td>
                    <td>14.01倍</td>
                    <td>68分</td>
                </tr>
                <tr>
                    <td>3</td>
                    <td>宝丰能源</td>
                    <td>600989</td>
                    <td>¥17.80</td>
                    <td class="positive">+3.19%</td>
                    <td>14.92倍</td>
                    <td>65分</td>
                </tr>
            </table>
        </div>

        <div class="performance">
            <h2>📈 策略表现</h2>
            <ul>
                <li><strong>策略平均收益:</strong> <span class="positive">+5.82%</span></li>
                <li><strong>沪深300平均收益:</strong> <span class="positive">+0.74%</span></li>
                <li><strong>超额收益:</strong> <span class="highlight">+5.08%</span></li>
                <li><strong>选股成功率:</strong> 100% (3只全部上涨)</li>
                <li><strong>上涨股票比例:</strong> 55.0% (165/300只)</li>
            </ul>
        </div>

        <div class="summary">
            <h2>💡 投资建议</h2>
            <ul>
                <li><strong>估值安全:</strong> 所有推荐股票PE≤30，避免泡沫风险</li>
                <li><strong>基本面优质:</strong> 严格剔除亏损股，确保盈利稳定</li>
                <li><strong>流动性充足:</strong> 沪深300成分股均有充足交易量</li>
                <li><strong>行业分散:</strong> 涵盖新能源、建筑、化工等优质行业</li>
                <li><strong>技术面良好:</strong> 综合评分体系确保技术面和基本面双重验证</li>
            </ul>
        </div>

        <hr>
        <p><em>风险提示: 投资有风险，决策需谨慎。本报告仅供参考，不构成投资建议。</em></p>
        <p><em>数据来源: 腾讯财经实时API，确保PE数据准确性</em></p>
    </body>
    </html>
    """

    # 添加HTML内容
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    # 添加Markdown附件
    with open(report_file, 'rb') as f:
        attachment = MIMEText(f.read(), 'base64', 'utf-8')
        attachment.add_header('Content-Disposition', 'attachment', filename=report_file)
        msg.attach(attachment)

    try:
        print("正在连接邮件服务器...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()

        print("正在登录邮箱...")
        server.login(sender_email, sender_password)

        print("正在发送邮件...")
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()

        print("✅ 邮件发送成功！")
        print(f"收件人: {receiver_email}")
        print(f"主题: 📊 2025年9月30日沪深300量化分析报告")
        print(f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return True

    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("沪深300量化分析报告邮件发送")
    print("=" * 60)
    send_csi300_report()