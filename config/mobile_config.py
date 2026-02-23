#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手机端优化配置
针对Termux等移动环境的性能优化配置
"""

# 数据获取配置 - 减少并发数和历史数据量
MOBILE_DATA_CONFIG = {
    'max_concurrent': 5,        # 并发数从20降到5(减少内存占用)
    'history_days': 20,         # 历史数据从60天降到20天
    'timeout': 30,              # 超时时间30秒
    'retry_times': 2,           # 重试次数从3降到2
    'chunk_size': 20,           # 每批处理20只股票
}

# 内存优化配置
MEMORY_CONFIG = {
    'enable_gc': True,          # 启用垃圾回收
    'gc_threshold': 50,         # 每处理50只股票进行一次gc
    'clear_cache': True,        # 处理完立即清除缓存
}

# 日志配置 - 减少日志输出
MOBILE_LOG_CONFIG = {
    'level': 'WARNING',         # 只记录警告和错误(从INFO改为WARNING)
    'max_size': 1024 * 1024,    # 日志文件最大1MB
    'backup_count': 2,          # 只保留2个备份
}

# 报告配置
MOBILE_REPORT_CONFIG = {
    'auto_cleanup': True,       # 自动清理
    'keep_days': 30,            # 只保留30天内的报告
    'compress_old': True,       # 压缩旧报告
}

# 推送配置(可选)
NOTIFICATION_CONFIG = {
    'enable': True,
    'type': 'termux',           # termux | bark | webhook
    'title': '股票分析完成',
    'play_sound': True,
}

def apply_mobile_optimization():
    """应用手机端优化配置"""
    import gc
    import os

    # 启用垃圾回收优化
    if MEMORY_CONFIG['enable_gc']:
        gc.enable()
        # 设置gc阈值
        gc.set_threshold(700, 10, 10)

    # 设置环境变量
    os.environ['PYTHONHASHSEED'] = '0'
    os.environ['PYTHONUNBUFFERED'] = '1'

    return True

def send_notification(title, message):
    """发送通知(需要Termux:API)"""
    if not NOTIFICATION_CONFIG['enable']:
        return

    try:
        import subprocess

        if NOTIFICATION_CONFIG['type'] == 'termux':
            # 使用termux-notification
            cmd = [
                'termux-notification',
                '--title', title,
                '--content', message,
                '--priority', 'high'
            ]

            if NOTIFICATION_CONFIG.get('play_sound'):
                cmd.extend(['--sound'])

            subprocess.run(cmd, check=False)

        elif NOTIFICATION_CONFIG['type'] == 'bark':
            # 使用Bark推送(iOS)
            import requests
            bark_url = NOTIFICATION_CONFIG.get('bark_url')
            if bark_url:
                requests.get(f"{bark_url}/{title}/{message}")

    except Exception as e:
        print(f"发送通知失败: {e}")

def cleanup_old_reports():
    """清理旧报告"""
    if not MOBILE_REPORT_CONFIG['auto_cleanup']:
        return

    import os
    import time
    from pathlib import Path

    reports_dir = Path('./reports')
    if not reports_dir.exists():
        return

    keep_days = MOBILE_REPORT_CONFIG['keep_days']
    cutoff_time = time.time() - (keep_days * 86400)

    for report_file in reports_dir.glob('*.md'):
        if report_file.stat().st_mtime < cutoff_time:
            print(f"删除旧报告: {report_file.name}")
            report_file.unlink()

def check_mobile_environment():
    """检查是否在移动环境中运行"""
    import os
    import platform

    is_mobile = False
    env_info = {
        'platform': platform.system(),
        'is_termux': os.path.exists('/data/data/com.termux'),
        'has_termux_api': os.system('which termux-notification > /dev/null 2>&1') == 0,
    }

    if env_info['is_termux']:
        is_mobile = True
        print("检测到Termux环境")

    return is_mobile, env_info

# 使用示例
if __name__ == '__main__':
    is_mobile, info = check_mobile_environment()
    if is_mobile:
        print("移动环境检测:")
        print(f"  平台: {info['platform']}")
        print(f"  Termux: {info['is_termux']}")
        print(f"  Termux:API: {info['has_termux_api']}")

        # 应用优化
        apply_mobile_optimization()
        print("已应用移动端优化配置")

        # 测试通知
        if info['has_termux_api']:
            send_notification("测试通知", "股票分析系统配置成功")
