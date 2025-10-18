import os
from dotenv import load_dotenv

load_dotenv()

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,
    'email': os.getenv('EMAIL_ADDRESS'),
    'password': os.getenv('EMAIL_PASSWORD'),
    'to_email': ['1120311927@qq.com', '18943656696@163.com', '1356163565@qq.com']
}

# 股票筛选参数
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 30,
    'min_turnover': 5000,  # 最小成交额：5000万元（API返回单位为万元）
    'momentum_days': 20,
    'min_price': 1.0,
    'max_stocks': 5,  # 从3只增加到5只
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