import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List
import threading
import json

from src.analysis.market_analyzer import MarketAnalyzer
from src.notification.email_sender import EmailSender
from config.config import SCHEDULE_CONFIG

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.market_analyzer = MarketAnalyzer()
        self.email_sender = EmailSender()
        self.is_running = False
        self.latest_analysis = None
        self.task_history = []

    def is_trading_day(self) -> bool:
        """判断是否为交易日"""
        today = datetime.now()
        weekday = today.weekday()

        # 排除周末
        if weekday >= 5:  # 5=Saturday, 6=Sunday
            return False

        # 这里可以进一步添加节假日判断
        # 简化处理，仅排除周末
        return True

    def run_daily_analysis(self):
        """执行每日分析任务"""
        if not self.is_trading_day() and SCHEDULE_CONFIG.get('weekdays_only', True):
            logger.info("今日非交易日，跳过分析")
            return

        try:
            logger.info("开始执行定时分析任务")
            start_time = datetime.now()

            # 执行分析
            analysis_result = self.market_analyzer.run_daily_analysis()

            if analysis_result:
                self.latest_analysis = analysis_result
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # 记录任务历史
                task_record = {
                    'task_type': 'daily_analysis',
                    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_seconds': duration,
                    'status': 'success',
                    'stocks_analyzed': analysis_result.get('total_analyzed', 0),
                    'stocks_selected': len(analysis_result.get('selected_stocks', []))
                }

                self.task_history.append(task_record)
                logger.info(f"分析任务完成，耗时 {duration:.2f} 秒")

                # 如果配置了立即发送邮件，则分析完成后立即发送
                if SCHEDULE_CONFIG.get('immediate_email', False):
                    logger.info("分析完成，立即发送邮件")
                    self.send_analysis_email_immediate()

            else:
                logger.error("分析任务失败")
                self._record_task_failure('daily_analysis', "分析任务返回空结果")

        except Exception as e:
            logger.error(f"执行分析任务失败: {e}")
            self._record_task_failure('daily_analysis', str(e))
            # 发送错误通知
            self.email_sender.send_error_notification(f"分析任务失败: {str(e)}")

    def send_analysis_email_immediate(self):
        """分析完成后立即发送邮件"""
        try:
            logger.info("开始立即发送分析邮件")
            start_time = datetime.now()

            if self.latest_analysis:
                # 发送分析邮件
                success = self.email_sender.send_analysis_email(self.latest_analysis)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                if success:
                    task_record = {
                        'task_type': 'immediate_email',
                        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration_seconds': duration,
                        'status': 'success',
                        'email_sent': True
                    }

                    self.task_history.append(task_record)
                    logger.info(f"立即邮件发送成功，耗时 {duration:.2f} 秒")
                else:
                    logger.error("立即邮件发送失败")
                    self._record_task_failure('immediate_email', "邮件发送失败")

            else:
                logger.warning("没有可发送的分析结果")
                self._record_task_failure('immediate_email', "没有可发送的分析结果")

        except Exception as e:
            logger.error(f"立即发送邮件失败: {e}")
            self._record_task_failure('immediate_email', str(e))

    def send_backup_email(self):
        """备用邮件发送任务（检查是否有遗漏的邮件）"""
        if not self.is_trading_day() and SCHEDULE_CONFIG.get('weekdays_only', True):
            logger.info("今日非交易日，跳过备用邮件检查")
            return

        # 检查今天是否已发送立即邮件
        today = datetime.now().strftime('%Y-%m-%d')
        immediate_emails_today = [
            task for task in self.task_history
            if task['task_type'] == 'immediate_email'
            and task['start_time'].startswith(today)
            and task['status'] == 'success'
        ]

        if immediate_emails_today:
            logger.info("今日已发送立即邮件，跳过备用邮件")
            return

        logger.info("今日未发送立即邮件，执行备用邮件发送")
        self.send_daily_email()

    def send_daily_email(self):
        """发送每日邮件任务"""
        if not self.is_trading_day() and SCHEDULE_CONFIG.get('weekdays_only', True):
            logger.info("今日非交易日，跳过邮件发送")
            return

        try:
            logger.info("开始执行邮件发送任务")
            start_time = datetime.now()

            # 获取最新分析结果
            if not self.latest_analysis:
                # 尝试从文件加载最新分析
                self.latest_analysis = self.market_analyzer.get_latest_analysis()

            if self.latest_analysis:
                # 发送分析邮件
                success = self.email_sender.send_analysis_email(self.latest_analysis)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                if success:
                    task_record = {
                        'task_type': 'send_email',
                        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration_seconds': duration,
                        'status': 'success',
                        'email_sent': True
                    }

                    self.task_history.append(task_record)
                    logger.info(f"邮件发送成功，耗时 {duration:.2f} 秒")
                else:
                    logger.error("邮件发送失败")
                    self._record_task_failure('send_email', "邮件发送失败")

            else:
                logger.warning("没有可发送的分析结果")
                self._record_task_failure('send_email', "没有可发送的分析结果")

        except Exception as e:
            logger.error(f"执行邮件发送任务失败: {e}")
            self._record_task_failure('send_email', str(e))

    def _record_task_failure(self, task_type: str, error_message: str):
        """记录任务失败"""
        task_record = {
            'task_type': task_type,
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': 0,
            'status': 'failed',
            'error_message': error_message
        }
        self.task_history.append(task_record)

    def setup_schedule(self):
        """设置定时任务"""
        try:
            analysis_time = SCHEDULE_CONFIG.get('analysis_time', '16:00')
            email_time = SCHEDULE_CONFIG.get('email_time', '16:30')
            immediate_email = SCHEDULE_CONFIG.get('immediate_email', False)

            # 设置每日分析任务 (交易日16:00)
            schedule.every().monday.at(analysis_time).do(self.run_daily_analysis)
            schedule.every().tuesday.at(analysis_time).do(self.run_daily_analysis)
            schedule.every().wednesday.at(analysis_time).do(self.run_daily_analysis)
            schedule.every().thursday.at(analysis_time).do(self.run_daily_analysis)
            schedule.every().friday.at(analysis_time).do(self.run_daily_analysis)

            if immediate_email:
                # 如果配置立即发送邮件，备用邮件任务作为保险
                schedule.every().monday.at(email_time).do(self.send_backup_email)
                schedule.every().tuesday.at(email_time).do(self.send_backup_email)
                schedule.every().wednesday.at(email_time).do(self.send_backup_email)
                schedule.every().thursday.at(email_time).do(self.send_backup_email)
                schedule.every().friday.at(email_time).do(self.send_backup_email)

                logger.info(f"定时任务已设置: 分析时间={analysis_time}, 立即邮件=是, 备用邮件时间={email_time}")
            else:
                # 原有的邮件发送逻辑
                schedule.every().monday.at(email_time).do(self.send_daily_email)
                schedule.every().tuesday.at(email_time).do(self.send_daily_email)
                schedule.every().wednesday.at(email_time).do(self.send_daily_email)
                schedule.every().thursday.at(email_time).do(self.send_daily_email)
                schedule.every().friday.at(email_time).do(self.send_daily_email)

                logger.info(f"定时任务已设置: 分析时间={analysis_time}, 邮件时间={email_time}")

        except Exception as e:
            logger.error(f"设置定时任务失败: {e}")

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return

        try:
            self.setup_schedule()
            self.is_running = True
            logger.info("任务调度器已启动")

            # 在单独线程中运行调度器
            def run_scheduler():
                while self.is_running:
                    schedule.run_pending()
                    time.sleep(60)  # 每分钟检查一次

            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()

            logger.info("调度器线程已启动")

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")

    def stop(self):
        """停止调度器"""
        self.is_running = False
        schedule.clear()
        logger.info("任务调度器已停止")

    def run_manual_analysis(self) -> Dict:
        """手动执行分析"""
        logger.info("手动执行分析任务")
        self.run_daily_analysis()
        return self.latest_analysis or {}

    def send_test_email(self) -> bool:
        """发送测试邮件"""
        return self.email_sender.send_test_email()

    def get_schedule_status(self) -> Dict:
        """获取调度状态"""
        next_runs = []
        for job in schedule.jobs:
            next_run = job.next_run
            if next_run:
                next_runs.append({
                    'job': str(job.job_func.__name__),
                    'next_run': next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'interval': str(job.interval)
                })

        return {
            'is_running': self.is_running,
            'total_jobs': len(schedule.jobs),
            'next_runs': next_runs,
            'latest_analysis_date': self.latest_analysis.get('analysis_date') if self.latest_analysis else None,
            'task_history_count': len(self.task_history)
        }

    def get_task_history(self, limit: int = 10) -> List[Dict]:
        """获取任务历史记录"""
        return self.task_history[-limit:] if self.task_history else []

    def get_performance_summary(self) -> Dict:
        """获取性能总结"""
        if not self.task_history:
            return {}

        analysis_tasks = [t for t in self.task_history if t['task_type'] == 'daily_analysis']
        email_tasks = [t for t in self.task_history if t['task_type'] == 'send_email']

        analysis_success = len([t for t in analysis_tasks if t['status'] == 'success'])
        email_success = len([t for t in email_tasks if t['status'] == 'success'])

        avg_analysis_duration = 0
        if analysis_tasks:
            durations = [t['duration_seconds'] for t in analysis_tasks if 'duration_seconds' in t]
            avg_analysis_duration = sum(durations) / len(durations) if durations else 0

        return {
            'total_tasks': len(self.task_history),
            'analysis_tasks': {
                'total': len(analysis_tasks),
                'success': analysis_success,
                'success_rate': analysis_success / len(analysis_tasks) * 100 if analysis_tasks else 0,
                'avg_duration': avg_analysis_duration
            },
            'email_tasks': {
                'total': len(email_tasks),
                'success': email_success,
                'success_rate': email_success / len(email_tasks) * 100 if email_tasks else 0
            }
        }

    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            self.task_history = [
                task for task in self.task_history
                if datetime.strptime(task['start_time'], '%Y-%m-%d %H:%M:%S') > cutoff_date
            ]
            logger.info(f"已清理 {days} 天前的任务记录")

        except Exception as e:
            logger.error(f"清理旧日志失败: {e}")