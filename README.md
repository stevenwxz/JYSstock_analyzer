# 沪深300股票量化分析系统

基于MA60趋势择时的沪深300量化选股系统。牛市进攻、熊市防守，追求低回撤高收益。

> **v2.0 更新**：已集成**同花顺 iFinD 专业金融数据接口**（TRAE Work 平台插件），数据质量与速度双提升。详见下方「同花顺 iFinD 集成」章节。

## 策略逻辑

```
沪深300 > MA60 → 牛市 → 进攻模式（高动量 + 高成长）
沪深300 < MA60 → 熊市 → 超防守模式（低波动 + 低PB + 高ROE + 小回撤）
```

- 止损: 单只 -7%
- 持仓: 最多6只，月度调仓
- 回测(2024-01~2026-07): +137.19%收益，19.59%最大回撤，55.0%胜率，超额+90.75%
- 本月持仓建议自动追踪实际表现并对比沪深300基准

---

## 同花顺 iFinD 集成

### 为什么集成 iFinD？

| 维度 | 免费方案（腾讯API+akshare） | 同花顺 iFinD 专业数据 |
|------|--------------------------|---------------------|
| ROE 数据 | PB/PE 间接估算（误差大） | 标准财报原始数据 |
| PE/PB 实时性 | 3-5 分钟延迟 | 毫秒级实时更新 |
| 利润增长率 | akshare 抓取（偶缺失） | 财报全量 + 一致预期 |
| 行业分类 | 东方财富单维度 | 申万/同花顺双体系 |
| 历史数据深度 | 1-2 年 K 线 | 上市以来全历史 |
| 缺失率 | 10%-20% | < 1% |
| 批量速度 | 逐只爬取（约15分钟/300只） | THS_RQ 批量一次调用 |
| 稳定性 | 公开接口可能限流/变更 | 商用授权，稳定保障 |

### 快速接入

#### 第1步：安装 iFinDPy SDK

1. 登录 [同花顺量化开放平台](https://quantapi.10jqka.com.cn)，下载 **Windows SDK 安装包**
2. 解压后运行 `Bin/Tool/SuperCommand.exe`，登录你的 iFinD 账号
3. 「工具 → 环境设置 → 选择 Python」，添加当前项目虚拟环境路径，执行环境修复
4. 修复成功后，Python 的 `Lib/site-packages` 下会出现 `iFinDPy.pth`

#### 第2步：配置环境变量

在项目根目录创建或编辑 `.env` 文件：

```env
# iFinD 账号（如不配置，自动回退到腾讯财经+akshare）
IFIND_USERNAME=你的账号
IFIND_PASSWORD=你的密码

# iFinD 开关（默认 true）
IFIND_ENABLED=true
# 是否优先使用 iFinD（默认 true）
IFIND_PREFER=true
```

#### 第3步：运行验证

```bash
# 执行一次分析，日志会标记数据来源
python main.py --mode analysis
# 成功时日志：iFinD 数据源已就绪（优先使用）
# 账号未配置时日志：iFinDPy SDK 未安装，将使用 akshare 作为数据源
```

### iFinD 能力封装（`src/data/ifind_client.py`）

| 封装方法 | 底层接口 | 功能 |
|----------|----------|------|
| `IFinDClient.get_csi300_constituents()` | `THS_DP` | 沪深300最新成分股 |
| `IFinDClient.get_financial_map(codes)` | `THS_BD` | ROE/增长率/PB/PE/毛利率/股息率/市值/资产负债率等 |
| `IFinDClient.get_industry_map(codes)` | `THS_BD` | 申万行业 + 同花顺行业 + 概念板块 |
| `IFinDClient.get_realtime_quotes(codes)` | `THS_RQ` | 批量实时行情（支持300只一次返回） |
| `IFinDClient.get_historical_kline(code, days)` | `THS_HF` | 历史高频 K 线（前复权） |
| `IFinDClient.iwencai_query(query, type)` | `THS_WC` | 智能问财自然语言取数（不消耗流量） |

### 数据回退机制

系统实现了**四层容错**，保证 iFinD 不可用时不中断：

```
1. iFinD 可用且优先 → 全量 iFinD 数据
2. iFinD 行情失败 → 单只降级腾讯财经 API
3. iFinD 财报失败 → 回退 akshare 财报接口
4. iFinD 完全不可用（未安装/未登录） → 保持原有免费方案
```

---

## 参数优化验证

通过逐日模拟对比不同参数组合（2024-01~2026-07，月度调仓）：

### 调仓周期 × 止损线（夏普比）

| 调仓 | 止损 | 累计收益 | 最大回撤 | 夏普比 |
|------|------|----------|----------|--------|
| 月度 | -7% | +137.19% | 19.59% | **1.63** |
| 月度 | -5% | +119.62% | 16.32% | 1.48 |
| 月度 | -10% | +125.47% | 22.10% | 1.41 |
| 周度 | -7% | +98.34% | 21.50% | 1.12 |

结论：月度调仓 + -7%止损为最优组合（夏普比最高）。

## 快速开始

```bash
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
| 回测 | `python scripts/run_backtest.py` | 月度回测+HTML报告+本月持仓建议 |

## 评分体系

### 进攻模式（牛市）

基础评分（技术面+估值+盈利+安全+股息）+ 动量加分（最高12分）+ 成长加分（5分）

### 超防守模式（熊市）

| 维度 | 权重 | 指标 |
|------|------|------|
| 低波动 | 30分 | 20日收益率标准差 |
| 低PB | 25分 | 市净率越低越好 |
| 高ROE | 25分 | 净资产收益率 |
| 小回撤 | 20分 | 20日最大回撤 |
| 温和动量 | 5分 | 0~5%正动量加分 |

## 技术栈

- **数据源（推荐）**: 同花顺 iFinD SDK（批量行情+财报+行业，专业稳定）
- **数据源（兜底）**: 腾讯财经K线API + akshare财报数据
- **分析**: pandas, numpy
- **异步**: aiohttp（并发获取300只股票数据）
- **通知**: SMTP 邮件（QQ邮箱）
- **调度**: schedule 定时任务

## 项目结构

```
├── main.py                 # 主入口
├── config/
│   ├── config.py           # 筛选参数 + iFinD开关配置
│   └── backtest_config.py  # 回测参数（动态end_date）
├── scripts/
│   ├── run_backtest.py     # 月度回测+HTML报告+本月持仓建议
│   ├── run_attribution.py  # 逐月归因分析
│   ├── run_param_compare.py # 参数对比（调仓×止损）
│   └── plot_daily_curve.py # 净值曲线绘图
├── src/
│   ├── data/
│   │   ├── ifind_client.py          # 同花顺iFinD客户端
│   │   ├── async_data_fetcher.py    # 异步数据获取
│   │   ├── data_fetcher.py          # iFinD优先 + 腾讯API兜底
│   │   └── financial_report_fetcher.py # 财报数据
│   ├── analysis/
│   │   ├── stock_filter.py    # 三种评分模式（基础/进攻/超防守）
│   │   └── market_analyzer.py # MA60趋势检测 + 模式切换
│   ├── notification/          # 邮件发送
│   └── scheduler/             # 定时任务
├── data/                      # 沪深300成分股列表
├── reports/                   # 回测报告（HTML）
├── charts/                    # 净值曲线图
└── cache/                     # 数据缓存
```

## 许可证

仅供学习交流，不构成投资建议。

