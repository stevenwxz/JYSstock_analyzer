#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import argparse
import sys
import os
from datetime import datetime

# 禁用代理 - 访问国内网站不需要代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scheduler.task_scheduler import TaskScheduler
from src.analysis.market_analyzer import MarketAnalyzer
from src.notification.email_sender import EmailSender
from config.config import LOG_CONFIG

def setup_logging():
    """设置日志配置"""
    os.makedirs(os.path.dirname(LOG_CONFIG['file']), exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG['level']),
        format=LOG_CONFIG['format'],
        handlers=[
            logging.FileHandler(LOG_CONFIG['file'], encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description='股票量化分析系统')
    parser.add_argument('--mode', choices=['daemon', 'analysis', 'email', 'test'],
                       default='daemon', help='运行模式')
    parser.add_argument('--config', help='配置文件路径')

    args = parser.parse_args()

    try:
        logger.info(f"股票分析系统启动 - 模式: {args.mode}")

        if args.mode == 'daemon':
            # 守护进程模式 - 启动定时任务
            logger.info("启动守护进程模式...")
            scheduler = TaskScheduler()
            scheduler.start()

            print("=" * 60)
            print("股票量化分析系统已启动")
            print("=" * 60)
            print("每个交易日 16:00 执行盘后分析")
            print("每个交易日 08:30 发送邮件报告")
            print("分析目标: A股 + 港股通")
            print("筛选条件: 强势股票，PE < 30")
            print("邮件发送: 1120311927@qq.com")
            print("=" * 60)
            print("按 Ctrl+C 停止程序")
            print("=" * 60)

            try:
                # 保持程序运行
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到停止信号，正在关闭...")
                scheduler.stop()
                print("\n程序已停止")

        elif args.mode == 'analysis':
            # 手动分析模式
            logger.info("执行手动分析...")
            print("正在执行股票分析...")

            analyzer = MarketAnalyzer()
            result = analyzer.run_daily_analysis()

            if result:
                selected_stocks = result.get('selected_stocks', [])
                print(f"\n分析完成！推荐 {len(selected_stocks)} 只股票:")
                print("-" * 50)

                for stock in selected_stocks:
                    print(f"#{stock.get('rank', 0)} {stock.get('name', '')} ({stock.get('code', '')})")
                    print(f"   价格: {stock.get('price', 0):.2f}元")
                    print(f"   涨跌幅: {stock.get('change_pct', 0):+.2f}%")
                    print(f"   PE: {stock.get('pe_ratio', 0):.2f}")
                    print(f"   20日动量: {stock.get('momentum_20d', 0):.2f}%")
                    print(f"   强势分数: {stock.get('strength_score', 0):.1f}")
                    print(f"   理由: {stock.get('selection_reason', '')}")
                    print()

                print("详细结果已保存到 ./logs/ 目录")
            else:
                print("分析失败，请检查日志")

        elif args.mode == 'email':
            # 邮件发送模式
            logger.info("发送邮件...")
            print("正在发送邮件...")

            analyzer = MarketAnalyzer()
            email_sender = EmailSender()

            # 获取最新分析结果
            latest_analysis = analyzer.get_latest_analysis()

            if latest_analysis:
                # 使用带附件的发送方式
                success = email_sender.send_analysis_email_with_attachment(latest_analysis)
                if success:
                    print("[成功] 邮件发送成功！")
                    print("邮件内容包括：")
                    print("  - 精美的HTML格式报告")
                    print("  - 详细的数据分析和可视化")
                    print("  - 市场分析和操作建议")
                    print("  - Markdown格式附件")
                else:
                    print("[失败] 邮件发送失败，请检查配置")
            else:
                print("没有找到分析结果，请先执行分析")

        elif args.mode == 'test':
            # 测试模式
            logger.info("运行系统测试...")
            print("正在运行系统测试...")

            # 测试邮件发送
            email_sender = EmailSender()
            email_success = email_sender.send_test_email()

            if email_success:
                print("邮件功能测试成功")
            else:
                print("邮件功能测试失败，请检查邮件配置")

            # 测试数据获取
            try:
                from src.data.data_fetcher import StockDataFetcher
                fetcher = StockDataFetcher()
                market_overview = fetcher.get_market_overview()

                if market_overview:
                    print("数据获取功能正常")
                    print(f"   总股票数: {market_overview.get('total_stocks', 0)}")
                    print(f"   上涨股票: {market_overview.get('rising_stocks', 0)}")
                    print(f"   下跌股票: {market_overview.get('falling_stocks', 0)}")
                else:
                    print("数据获取功能异常")

            except Exception as e:
                print(f"数据获取测试失败: {e}")

            print("测试完成")

    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()