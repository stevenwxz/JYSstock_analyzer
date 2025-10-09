# 股票量化分析系统

一个基于 Python 的自动化股票筛选与分析系统，支持 A股 和港股通市场，能够自动执行技术分析、筛选强势股票，并通过邮件发送分析报告。

## 功能特性

### 核心功能

- **自动化数据获取**：使用 AkShare 获取实时股票数据
- **智能股票筛选**：基于多维度指标筛选优质股票
  - PE 市盈率筛选（默认 < 30）
  - 动量分析（20日涨跌幅）
  - 成交量过滤
  - 强势分数评估
- **技术分析**：
  - 市场概况分析
  - 个股技术指标计算
  - 趋势强度评估
- **回测功能**：历史数据回测，验证策略有效性
- **自动化调度**：定时执行分析任务
  - 每个交易日 16:00 执行盘后分析
  - 分析完成后自动发送邮件报告
- **邮件通知**：自动生成并发送格式化的分析报告

### 分析目标

- A股市场
- 港股通标的
- 沪深300成分股专项分析

## 项目结构

```
jys/
└── stock_analyzer/
    ├── main.py                     # 主程序入口
    ├── requirements.txt            # Python依赖
    ├── start.bat                   # Windows启动脚本
    ├── start_daemon.bat            # 守护进程启动脚本
    ├── config/
    │   └── config.py              # 配置文件
    ├── src/
    │   ├── data/
    │   │   └── data_fetcher.py    # 数据获取模块
    │   ├── analysis/
    │   │   ├── market_analyzer.py  # 市场分析器
    │   │   ├── stock_filter.py     # 股票筛选器
    │   │   └── backtest.py         # 回测模块
    │   ├── notification/
    │   │   └── email_sender.py     # 邮件发送模块
    │   └── scheduler/
    │       └── task_scheduler.py   # 任务调度器
    ├── logs/                       # 日志和分析结果
    └── tests/                      # 测试文件
```

## 快速开始

### 环境要求

- Python 3.8+
- Windows/Linux/macOS

### 安装步骤

1. **克隆项目**

```bash
cd stock_analyzer
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置环境变量**

在项目根目录创建 `.env` 文件：

```env
EMAIL_ADDRESS=your_email@qq.com
EMAIL_PASSWORD=your_smtp_password
```

> 注意：QQ邮箱需要使用授权码，不是登录密码。在 QQ邮箱设置 -> 账户 -> 开启 SMTP 服务获取。

4. **验证安装**

```bash
python check_install.py
```

### 使用方法

#### 1. 守护进程模式（推荐）

自动在每个交易日定时执行分析：

```bash
python main.py --mode daemon
```

或使用 Windows 批处理：

```bash
start_daemon.bat
```

#### 2. 手动分析模式

立即执行一次分析：

```bash
python main.py --mode analysis
```

#### 3. 邮件发送模式

发送最新的分析报告：

```bash
python main.py --mode email
```

#### 4. 测试模式

测试系统各模块功能：

```bash
python main.py --mode test
```

#### 5. 专项分析

沪深300全量分析：

```bash
python csi300_full_analysis.py
```

## 配置说明

主要配置文件位于 `config/config.py`：

### 邮件配置

```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,
    'email': '发件邮箱',
    'password': '邮箱授权码',
    'to_email': '收件邮箱'
}
```

### 筛选参数

```python
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 30,         # 最大PE市盈率
    'min_volume': 1000000,      # 最小成交量
    'momentum_days': 20,        # 动量计算天数
    'min_price': 1.0,           # 最小股价
    'max_stocks': 3             # 最多筛选股票数
}
```

### 调度配置

```python
SCHEDULE_CONFIG = {
    'analysis_time': '16:00',    # 盘后分析时间
    'email_time': '16:30',       # 邮件发送时间
    'weekdays_only': True,       # 仅工作日运行
    'immediate_email': True      # 分析完成立即发送邮件
}
```

## 输出结果

### 分析结果存储

- 位置：`./logs/` 目录
- 格式：JSON 文件（包含时间戳）
- 内容：
  - 市场概况
  - 筛选出的股票列表
  - 每只股票的详细指标
  - 选择理由

### 邮件报告内容

- 分析日期和时间
- 市场整体情况
- 推荐股票列表（最多3只）
- 每只股票的关键指标：
  - 股票代码和名称
  - 当前价格和涨跌幅
  - PE 市盈率
  - 20日动量
  - 强势分数
  - 推荐理由

## 技术栈

- **数据源**：AkShare（免费开源金融数据接口）
- **数据处理**：Pandas、NumPy
- **可视化**：Matplotlib、Seaborn
- **任务调度**：Schedule
- **邮件发送**：smtplib（标准库）

## 注意事项

1. **数据获取限制**：

   - AkShare 数据源可能有访问频率限制
   - 建议合理设置重试次数和超时时间
2. **交易时间**：

   - 系统默认仅在工作日执行
   - 分析时间设置在收盘后（16:00）
3. **邮件发送**：

   - 确保邮箱开启 SMTP 服务
   - QQ邮箱需使用授权码
   - 检查防火墙和网络设置
4. **数据缓存**：

   - 系统会在 `./data_cache` 目录缓存数据
   - 可定期清理以节省空间

## 常见问题

**Q: 邮件发送失败？**
A: 检查 `.env` 文件配置，确认授权码正确，检查网络连接。

**Q: 数据获取失败？**
A: 可能是网络问题或 AkShare API 限制，建议稍后重试。

**Q: 如何修改筛选条件？**
A: 编辑 `config/config.py` 中的 `STOCK_FILTER_CONFIG` 参数。

**Q: 如何停止守护进程？**
A: 按 `Ctrl+C` 即可优雅退出。

## 开发计划

- [ ] 添加更多技术指标（MACD、KDJ等）
- [ ] 支持更多数据源
- [ ] 增加Web界面
- [ ] 完善回测系统
- [ ] 添加风险控制模块
- [ ] 支持数据库存储

## 免责声明

**本系统仅供学习和研究使用，不构成任何投资建议。股市有风险，投资需谨慎。使用本系统进行的任何投资决策及其结果由使用者自行承担。**

## 许可证

本项目仅供个人学习使用。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 邮箱：1120311927@qq.com

---

**最后更新时间**：2025年10月
