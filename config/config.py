import os
from dotenv import load_dotenv

load_dotenv()

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,
    'email': os.getenv('EMAIL_ADDRESS'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'to_email': [email.strip() for email in os.getenv('TO_EMAIL', 'your_email@example.com').split(',')]
}

# 股票筛选参数
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 30,
    'min_turnover_rate': 1.0,  # 最小换手率：1.0%
    'momentum_days': 20,
    'min_price': 1.0,
    'max_stocks': 10,  # 从5只增加到10只
    'min_strength_score': 40   # 从50降低到40
}

# 数据源配置
DATA_CONFIG = {
    'akshare_timeout': 30,
    'retry_times': 3,
    'cache_dir': './data_cache'
}

# 调度配置
SCHEDULE_CONFIG = {
    'analysis_time': '16:00',    # 盘后分析时间
    'email_time': '16:30',       # 收盘后发送邮件时间(分析完成后半小时)
    'weekdays_only': True,       # 仅工作日运行
    'immediate_email': True      # 分析完成后立即发送邮件
}

# 日志配置
LOG_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': './logs/stock_analyzer.log'
}