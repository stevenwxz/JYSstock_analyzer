# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

沪深300股票量化分析系统。系统每日盘后自动分析沪深300成分股，通过多维度评分筛选强势股票，并通过邮件推送结果。

## 常用命令

```bash
# 在 stock_analyzer/ 目录下执行
cd stock_analyzer

# 安装依赖
pip install -r requirements.txt

# 手动执行分析
python main.py --mode analysis

# 守护进程模式（定时16:00分析，16:30发邮件）
python main.py --mode daemon

# 发送邮件报告
python main.py --mode email

# 运行回测
python run_backtest_optimized.py
```

## 架构

**stock_analyzer/** — Python后端（作为git子模块引用）
- `src/data/data_fetcher.py` — 通过腾讯财经API获取A股实时数据
- `src/data/async_data_fetcher.py` — 异步批量获取（默认，并发20）
- `src/data/financial_report_fetcher.py` — 通过akshare获取真实财报数据（ROE、利润增长率）
- `src/analysis/stock_filter.py` — 核心评分筛选逻辑（技术面30分+估值25分+盈利30分+安全性10分+股息5分）
- `src/analysis/market_analyzer.py` — 市场分析协调器
- `src/notification/email_sender.py` — QQ邮箱SMTP发送HTML报告
- `src/scheduler/task_scheduler.py` — 基于schedule库的定时任务
- `config/config.py` — 实盘筛选参数（PE<30, 换手率>1%, 评分>=40）
- `config/backtest_config.py` — 回测参数（成交额门槛更低）
- `config/dividend_override.py` — 股息率手动修正（修正API数据不准确的情况）

## 数据流

```
腾讯财经API → async_data_fetcher(实时数据+基本面) → financial_report_fetcher(真实财报覆盖ROE/利润增长)
    ↓
stock_filter(评分筛选) → market_analyzer → 输出
                                            ├── email_sender (邮件)
                                            └── reports/ (Markdown报告)
```

## 财报数据策略

- ROE：取最近年报（ak.stock_yjbb_em(date='20251231')），代表稳定盈利能力
- 利润增长率：取最新季报（ak.stock_yjbb_em(date='20260331')），代表当前趋势
- 缓存在 `cache/financial_reports/` 目录，每天一份JSON文件
- 获取失败时降级为 PB/PE 反推估算值

## 注意事项

- 代码中主动禁用HTTP代理（访问国内akshare数据源不需要代理）
- 环境变量通过 `.env` 文件配置（EMAIL_ADDRESS, EMAIL_PASSWORD, TO_EMAIL）
- 数据缓存在 `cache/` 目录，7天过期自动失效
- `stock_analyzer` 是git子模块，修改后需在父仓库更新子模块引用
