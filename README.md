# 沪深300股票量化分析系统

基于 Python 的沪深300成分股量化分析系统，每日盘后自动筛选强势股票并推送邮件报告。

## 功能

- 沪深300全量成分股实时分析
- 五维评分系统（技术面 + 估值 + 盈利 + 安全性 + 股息）
- 自动生成 Markdown 分析报告
- QQ邮箱 HTML 格式报告推送
- 历史回测验证策略有效性
- 定时任务自动运行（交易日16:00分析，16:30发邮件）

## 快速开始

```bash
cd stock_analyzer
pip install -r requirements.txt

# 配置邮箱（可选）
cp .env.example .env
# 编辑 .env 填入 EMAIL_ADDRESS, EMAIL_PASSWORD, TO_EMAIL

# 执行分析
python main.py --mode analysis
```

## 运行模式

| 模式 | 命令 | 说明 |
|------|------|------|
| 手动分析 | `python main.py --mode analysis` | 立即执行一次分析 |
| 守护进程 | `python main.py --mode daemon` | 定时自动分析+发邮件 |
| 发送邮件 | `python main.py --mode email` | 发送最近一次分析报告 |
| 回测 | `python run_backtest_optimized.py` | 历史数据回测 |

## 评分体系

| 维度 | 权重 | 指标 |
|------|------|------|
| 技术面 | 30分 | 涨跌幅、20日动量、换手率 |
| 估值 | 25分 | PE、PB、PR市赚率 |
| 盈利能力 | 30分 | ROE、净利润增长率 |
| 安全性 | 10分 | PB安全边际、股息率、换手率 |
| 股息 | 5分 | 股息率（支持手动修正） |

## 技术栈

- **数据源**: akshare（开源金融数据接口）
- **分析**: pandas, numpy
- **异步**: aiohttp（并发获取300只股票数据）
- **通知**: SMTP 邮件
- **调度**: schedule 定时任务

## 项目结构

```
stock_analyzer/          # 核心代码（git子模块）
├── main.py             # 主入口
├── config/             # 配置（筛选参数、股息修正）
├── src/
│   ├── data/           # 数据获取（腾讯财经API + akshare）
│   ├── analysis/       # 评分筛选 + 回测引擎
│   ├── notification/   # 邮件发送
│   └── scheduler/      # 定时任务
└── reports/            # 生成的分析报告
```

## 许可证

仅供学习交流，不构成投资建议。

