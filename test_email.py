#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邮件发送功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from dotenv import load_dotenv
load_dotenv()

from src.notification.email_sender import EmailSender
from config.config import EMAIL_CONFIG

def test_email():
    """测试邮件发送功能"""
    print("正在测试邮件发送功能...")
    
    # 创建邮件发送器实例
    email_sender = EmailSender(EMAIL_CONFIG)
    
    # 发送测试邮件
    result = email_sender.send_test_email()
    
    if result:
        print("✅ 邮件发送成功！")
        print("邮件功能配置正确，您可以接收每日的股票分析报告。")
    else:
        print("❌ 邮件发送失败！")
        print("请检查以下配置：")
        print("1. .env 文件中的 EMAIL_ADDRESS 是否正确")
        print("2. .env 文件中的 EMAIL_PASSWORD 是否为SMTP授权码（不是登录密码）")
        print("3. .env 文件中的 TO_EMAIL 是否正确")
        print("4. QQ邮箱是否开启了IMAP/SMTP服务")
    
    return result

if __name__ == "__main__":
    test_email()