# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

沪深300股票量化分析系统。基于MA60趋势择时，在牛市使用进攻模式（高动量+高成长）选股，熊市切换超防守模式（低波动+低PB+高ROE）选股。每日盘后自动分析并通过邮件推送结果。

## 常用命令

```bash
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

- `src/data/data_fetcher.py` — 通过腾讯财经API获取A股实时数据
- `src/data/async_data_fetcher.py` — 异步批量获取（默认，并发20），计算动量/波动率/最大回撤
- `src/data/financial_report_fetcher.py` — 通过akshare获取真实财报数据（ROE、利润增长率）
- `src/analysis/stock_filter.py` — 核心评分筛选，含三种模式：
  - `select_top_stocks()` — 基础模式（技术面30+估值25+盈利30+安全10+股息5）
  - `select_top_stocks_offensive()` — 进攻模式（基础分+动量加分+成长加分）
  - `select_top_stocks_ultra_defensive()` — 超防守模式（低波动30+低PB25+高ROE25+小回撤20+动量5）
- `src/analysis/market_analyzer.py` — 市场分析协调器，含MA60趋势检测和模式切换
- `src/notification/email_sender.py` — QQ邮箱SMTP发送HTML报告
- `src/scheduler/task_scheduler.py` — 基于schedule库的定时任务
- `config/config.py` — 筛选参数（PE<30, 换手率>1%, 最大持仓6只, 止损-5%）
- `config/backtest_config.py` — 回测参数（区间、持仓天数、交易成本）
- `config/dividend_override.py` — 股息率手动修正

## 核心策略逻辑

```
1. 趋势判断: 沪深300收盘价 vs MA60
   - 站上MA60 → 牛市 → 进攻模式
   - 跌破MA60 → 熊市 → 超防守模式

2. 进攻模式: 基础评分 + 高动量加分(最高12) + 高成长加分(5)
3. 超防守模式: 低波动(30) + 低PB(25) + 高ROE(25) + 小回撤(20) + 温和动量(5)
4. 止损: 单只股票 -5% 止损
5. 持仓: 最多6只，7个交易日调仓
```

## 数据流

```
腾讯财经API → async_data_fetcher(实时+基本面+动量+波动率+回撤)
    ↓
financial_report_fetcher(真实财报覆盖ROE/利润增长)
    ↓
market_analyzer.detect_market_trend() → 判断牛/熊
    ↓
牛市: stock_filter.select_top_stocks_offensive()
熊市: stock_filter.select_top_stocks_ultra_defensive()
    ↓
email_sender / reports/
```

## 财报数据策略

- ROE：取最近年报（ak.stock_yjbb_em），代表稳定盈利能力
- 利润增长率：取最新季报，代表当前趋势
- 缓存在 `cache/financial_reports/`，每天一份，只保留沪深300数据

## 回测结果（2024-01-02 ~ 2026-05-13）

- 策略收益: +92.80%
- 最大回撤: 16.5%
- 胜率: 51.9%
- 超额收益: +45.20%（vs 沪深300 +47.60%）

## 注意事项

- 代码中主动禁用HTTP代理（访问国内akshare数据源不需要代理）
- 环境变量通过 `.env` 文件配置（EMAIL_ADDRESS, EMAIL_PASSWORD, TO_EMAIL）
- 数据缓存在 `cache/` 目录，7天过期自动失效
- MA60趋势检测通过腾讯K线API获取沪深300指数数据
