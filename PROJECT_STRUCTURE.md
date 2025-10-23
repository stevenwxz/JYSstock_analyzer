# 📁 项目结构说明

## 完整目录树

```
stock_analyzer/
├── 📄 README.md                      # 项目主文档
├── 📄 USAGE.md                       # 详细使用说明
├── 📄 PROJECT_STRUCTURE.md           # 本文件
├── 📄 requirements.txt               # Python依赖包
├── 📄 .env.example                   # 环境变量模板
├── 📄 .env                           # 环境变量配置（不提交）
├── 📄 .gitignore                     # Git忽略规则
│
├── 🚀 main.py                        # 实盘运行入口
├── 🔄 run_backtest_optimized.py     # 回测系统入口
├── 📧 send_detailed_report.py       # 邮件报告发送
├── 📊 generate_backtest_report.py   # 回测报告生成
│
├── 📂 config/                        # 配置目录
│   ├── config.py                    # 实盘配置（严格标准）
│   └── backtest_config.py           # 回测配置（略宽松）
│
├── 📂 src/                           # 源代码目录
│   ├── __init__.py
│   │
│   ├── 📂 data/                     # 数据获取模块
│   │   ├── __init__.py
│   │   └── data_fetcher.py          # 股票数据获取（akshare）
│   │
│   ├── 📂 analysis/                 # 分析模块
│   │   ├── __init__.py
│   │   ├── stock_filter.py          # 核心筛选逻辑
│   │   ├── market_analyzer.py       # 市场分析
│   │   └── backtest.py              # 回测引擎
│   │
│   ├── 📂 notification/             # 通知模块
│   │   ├── __init__.py
│   │   └── email_sender.py          # 邮件发送
│   │
│   └── 📂 scheduler/                # 调度模块
│       ├── __init__.py
│       └── task_scheduler.py        # 定时任务
│
├── 📂 cache/                         # 数据缓存（自动生成）
│   ├── csi300_stocks_with_names.pkl # 沪深300成分股
│   └── stock_*.pkl                  # 股票历史数据
│
├── 📂 logs/                          # 日志文件
│   └── stock_analyzer.log           # 系统运行日志
│
└── 📂 tests/                         # 测试目录（未来）
    └── __init__.py
```

## 核心文件说明

### 入口文件

| 文件 | 用途 | 运行方式 |
|------|------|---------|
| `main.py` | 实盘选股 | `python main.py` |
| `run_backtest_optimized.py` | 历史回测 | `python run_backtest_optimized.py` |
| `send_detailed_report.py` | 发送邮件 | 自动调用或手动运行 |

### 配置文件

| 文件 | 说明 | 关键参数 |
|------|------|---------|
| `config/config.py` | 实盘配置 | PE=30, 成交额=5000万, 分数≥50 |
| `config/backtest_config.py` | 回测配置 | PE=30, 成交额=3000万, 分数≥50 |
| `.env` | 邮箱密码 | EMAIL_ADDRESS, EMAIL_PASSWORD |

### 核心模块

#### 1. 数据获取 (`src/data/data_fetcher.py`)

```python
class StockDataFetcher:
    - get_stock_realtime_data()      # 获取实时数据
    - get_stock_historical_data()    # 获取历史数据
    - calculate_momentum()           # 计算动量指标
```

#### 2. 股票筛选 (`src/analysis/stock_filter.py`)

```python
class StockFilter:
    - calculate_strength_score()     # 计算强势分数（包含分项得分）
    - filter_by_pe_ratio()          # PE筛选
    - filter_by_strength()          # 强势筛选
    - select_top_stocks()           # 选择TOP3
```

**分项得分说明**:
- **技术面 (30分)**: 涨跌幅、动量、成交额活跃度
- **估值 (25分)**: PE、PB、PEG等估值指标
- **盈利能力 (30分)**: ROE、利润增长率等盈利指标
- **安全性 (10分)**: PB安全边际、股息率稳定性、换手率波动性
- **股息 (5分)**: 股息率得分

#### 3. 回测引擎 (`run_backtest_optimized.py`)

```python
class OptimizedBacktest:
    - backtest_single_day()         # 单日回测
    - backtest_multi_days()         # 多日回测
    - get_csi300_stocks()           # 获取成分股
```

## 数据流程

### 实盘流程

```
main.py
  ↓
获取沪深300成分股 (data_fetcher)
  ↓
获取实时数据 (data_fetcher)
  ↓
计算动量和强势分数 (stock_filter)
  ↓
多维度筛选 (stock_filter)
  ↓
选出TOP3 (stock_filter)
  ↓
发送邮件 (email_sender)
```

### 回测流程

```
run_backtest_optimized.py
  ↓
加载配置 (backtest_config)
  ↓
获取历史数据（带缓存）
  ↓
计算历史动量
  ↓
使用回测配置筛选
  ↓
模拟买卖，计算收益
  ↓
保存JSON结果
```

## 配置文件对比

### 实盘 vs 回测

| 参数 | 实盘 | 回测 | 原因 |
|------|------|------|------|
| PE上限 | 30 | 30 | 一致 |
| 成交额 | 5000万 | 3000万 | 回测放宽，增加样本 |
| 强势分数 | ≥50 | ≥50 | 一致 |
| 推荐数量 | 3只 | 3只 | 一致 |
| 股票池 | 300只 | 300只 | 全量分析 |

## 缓存机制

### 缓存文件

```
cache/
├── csi300_stocks_with_names.pkl    # 沪深300成分股（7天有效）
├── stock_600519_2025-04-07.pkl    # 茅台历史数据
└── stock_000001_2025-04-07.pkl    # 平安银行历史数据
```

### 缓存策略

- **成分股**: 缓存7天
- **股票数据**: 按日期缓存，7天过期
- **自动清理**: 超过7天自动失效

## 日志系统

### 日志文件

```
logs/
├── stock_analyzer.log              # 主日志
└── backtest_*.txt                  # 回测报告
```

### 日志级别

- `INFO`: 正常运行信息
- `WARNING`: 警告信息（如数据缺失）
- `ERROR`: 错误信息（如网络故障）

## 环境变量

### .env 文件结构

```env
# 邮箱配置
EMAIL_ADDRESS=your_email@qq.com
EMAIL_PASSWORD=your_smtp_password
```

### 使用方式

```python
from dotenv import load_dotenv
import os

load_dotenv()
email = os.getenv('EMAIL_ADDRESS')
```

## 开发指南

### 添加新的筛选指标

1. 修改 `src/analysis/stock_filter.py`
2. 在 `calculate_strength_score()` 中添加新指标
3. 调整权重分配

### 添加新的数据源

1. 修改 `src/data/data_fetcher.py`
2. 添加新的获取方法
3. 更新缓存逻辑

### 自定义邮件模板

1. 修改 `src/notification/email_sender.py`
2. 更新 `generate_report()` 方法

## 依赖关系

```
main.py
  ├── data_fetcher (获取数据)
  ├── stock_filter (筛选股票)
  └── email_sender (发送邮件)

run_backtest_optimized.py
  ├── data_fetcher (获取历史数据)
  ├── stock_filter (筛选股票)
  └── backtest_config (回测配置)
```

## 注意事项

1. **不要提交 .env 文件** - 包含敏感信息
2. **定期清理 cache/** - 避免占用太多空间
3. **备份 logs/** - 保留重要日志
4. **测试后再实盘** - 先用回测验证策略

---

📚 更多信息请查看 [README.md](README.md) 和 [USAGE.md](USAGE.md)
