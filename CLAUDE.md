# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

沪深300股票量化分析系统。基于MA60趋势择时（±2%缓冲带），牛市用进攻模式（高动量+高成长）选股，熊市切换超防守模式（低波动+低PB+高ROE）。每日盘后自动分析并通过邮件推送结果。

## 常用命令

```bash
pip install -r requirements.txt

# 日常分析
python main.py --mode analysis      # 手动执行分析
python main.py --mode daemon        # 守护进程（16:00分析，16:30发邮件）
python main.py --mode email         # 发送最新报告邮件

# 回测 & 分析
python scripts/run_backtest.py      # 月度回测（MA60±2%缓冲带+止损）
python scripts/run_attribution.py   # 逐月涨跌归因
python scripts/plot_daily_curve.py  # 绘制净值曲线
```

## 目录结构

```
├── main.py                     # 入口（daemon/analysis/email/test）
├── start.bat                   # Windows快捷启动
├── config/
│   ├── config.py               # 筛选参数 + iFinD配置
│   ├── backtest_config.py      # 回测参数（区间、成本）
│   └── dividend_override.py    # 股息率手动修正
├── src/
│   ├── data/
│   │   ├── ifind_client.py     # iFinD SDK客户端（单例）
│   │   ├── data_fetcher.py     # iFinD优先+腾讯兜底
│   │   ├── async_data_fetcher.py  # 异步并发20获取
│   │   └── financial_report_fetcher.py  # 财报（iFinD/akshare）
│   ├── analysis/
│   │   ├── stock_filter.py     # 核心评分（进攻/防守/基础三模式）
│   │   └── market_analyzer.py  # MA60趋势+选股+止损监控+报告生成
│   ├── notification/
│   │   └── email_sender.py     # QQ邮箱SMTP
│   └── scheduler/
│       └── task_scheduler.py   # 定时任务
├── scripts/
│   ├── run_backtest.py         # 月度回测主脚本
│   ├── run_attribution.py      # 逐月归因分析
│   ├── plot_daily_curve.py     # 净值曲线绘图
│   └── generate_md_report.py   # 从JSON生成MD报告
├── data/
│   └── csi300_stocks.json      # 沪深300成分股列表
├── reports/YYYY-MM/            # 按月分类的分析报告（gitignored）
├── charts/                     # 回测图表输出（gitignored）
├── cache/                      # 数据缓存（gitignored，7天过期）
└── logs/                       # 运行日志（gitignored）
```

## 核心策略

```
趋势判断: 沪深300 vs MA60（±2%缓冲带）
  - 突破 MA60×1.02 → 进攻模式
  - 跌破 MA60×0.98 → 防守模式
  - 缓冲带内维持上次模式

进攻模式: 基础评分 + 动量加分(最高+12) + 成长加分(+5)
防守模式: 低波动(30) + 低PB(25) + 高ROE(25) + 小回撤(20) + 动量(5)
止损: -5%（每日监控，报告标红）
持仓: 最多6只，月度调仓
```

## 数据流

```
iFinD/腾讯API → async_data_fetcher(批量300只)
    → financial_report_fetcher(ROE/利润增长覆盖)
    → market_analyzer.detect_market_trend()
    → 进攻/防守选股 + 止损检查
    → 报告生成(reports/YYYY-MM/) + 邮件推送
```

## 回测结果（2024-01 ~ 2026-07，月度调仓）

- 策略收益: +84.07%
- 基准收益: +46.44%（沪深300）
- 超额收益: +37.63%
- 最大回撤: 19.63%
- 胜率: 51.1%

## 注意事项

- 代码中主动禁用HTTP代理（国内数据源不需要）
- 环境变量通过 `.env` 配置：邮件(EMAIL_ADDRESS/PASSWORD/TO_EMAIL) + iFinD(IFIND_USERNAME/PASSWORD/ENABLED/PREFER)
- iFinD未安装时自动回退到腾讯+akshare免费方案
- 数据返回带 `data_source` 字段标识来源（ifind/tencent）
