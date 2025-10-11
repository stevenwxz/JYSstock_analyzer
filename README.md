# 📊 沪深300量化分析系统

基于沪深300成分股的智能选股系统，通过多维度量化指标筛选优质股票，自动生成详细分析报告并发送邮件通知。

## ✨ 核心功能

### 🎯 智能选股
- **沪深300全覆盖**: 分析300只A股核心优质资产
- **多维度筛选**: PE估值、成交量、涨跌幅、强势评分综合评估
- **实时数据**: 使用腾讯财经API获取实时PE-TTM数据
- **严格标准**: PE ≤ 30，成交量 > 100万手

### 📧 智能报告
- **精美HTML邮件**: 渐变色设计、数据可视化展示
- **详细分析内容**:
  - 📈 市场整体统计（5,000+只股票）
  - 🏆 精选股票详细信息
  - 💪 策略表现与超额收益
  - ⚠️ 风险提示与操作建议
  - 🔍 市场特征分析
- **Markdown附件**: 完整报告可下载保存

### ⏰ 自动化运行
- **定时分析**: 每个交易日16:00自动执行盘后分析
- **自动发送**: 分析完成后立即发送邮件报告
- **多收件人**: 支持同时发送给多个邮箱

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/stock_analyzer.git
cd stock_analyzer
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置邮箱**

创建 `.env` 文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的邮箱配置：
```env
EMAIL_ADDRESS=your_email@qq.com
EMAIL_PASSWORD=your_auth_code
```

> 📝 如何获取QQ邮箱授权码？请查看 [email_config_template.txt](email_config_template.txt)

4. **运行程序**

**方式1: 手动分析**
```bash
python main.py --mode analysis
```

**方式2: 守护进程模式（自动定时运行）**
```bash
python main.py --mode daemon
```

**方式3: 发送最新报告邮件**
```bash
python send_detailed_report.py
```

## 📂 项目结构

```
stock_analyzer/
├── main.py                           # 主程序入口
├── send_detailed_report.py           # 详细邮件发送脚本
├── requirements.txt                  # Python依赖
├── .env                              # 邮箱配置（需自己创建）
├── .env.example                      # 配置示例
├── email_config_template.txt         # 邮箱配置说明
├── config/
│   └── config.py                     # 系统配置
├── src/
│   ├── data/
│   │   └── data_fetcher.py          # 数据获取模块
│   ├── analysis/
│   │   ├── stock_filter.py          # 股票筛选算法
│   │   ├── market_analyzer.py       # 市场分析模块
│   │   └── backtest.py              # 回测模块
│   ├── notification/
│   │   └── email_sender.py          # 邮件发送模块
│   └── scheduler/
│       └── task_scheduler.py        # 定时任务模块
└── logs/                             # 日志和分析结果

```

## 📊 筛选策略

### 筛选条件
| 指标 | 标准 | 说明 |
|------|------|------|
| PE市盈率 | 0 < PE ≤ 30 | 剔除亏损股和高估值股 |
| 成交量 | > 100万手 | 确保充足流动性 |
| 股价 | > 1元 | 排除ST等风险股 |
| 推荐数量 | 最多3只 | 精选优质标的 |

### 评分体系
- **涨跌幅权重**: 当日强势表现
- **PE估值权重**: 估值安全性
- **流动性权重**: 成交量充足度
- **动量指标**: 20日价格动量

## 📈 报告示例

### 分析概况
- ✅ 数据成功率: 100%
- 📊 筛选通过率: 根据市场情况动态变化
- 🎯 数据源: 腾讯财经实时API

### 精选股票示例
```
#1 国信证券 (002736)
收盘价: ¥14.26
涨跌幅: +5.94%
PE-TTM: 13.98倍
综合评分: 55分
超额收益: +6.20%
```

### 策略表现
- 📈 精选股票涨跌幅: +5.94%
- 📉 市场平均涨跌幅: -0.26%
- 🎯 超额收益: +6.20%
- ✅ 选股成功率: 100%

## ⚙️ 配置说明

### 股票筛选配置 (config/config.py)
```python
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 30,        # 最大PE比率
    'min_volume': 1000000,     # 最小成交量（手）
    'momentum_days': 20,       # 动量计算天数
    'min_price': 1.0,          # 最小股价
    'max_stocks': 3            # 最多推荐股票数
}
```

### 定时任务配置
```python
SCHEDULE_CONFIG = {
    'analysis_time': '16:00',      # 盘后分析时间
    'email_time': '16:30',         # 邮件发送时间
    'weekdays_only': True,         # 仅工作日运行
    'immediate_email': True        # 分析完成后立即发送
}
```

### 邮件配置
```python
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,
    'to_email': [
        'recipient1@qq.com',
        'recipient2@163.com'
    ]
}
```

## 🔧 使用技巧

### 1. 手动运行分析
适合盘后手动获取当天分析结果：
```bash
python main.py --mode analysis
```

### 2. 守护进程模式
适合服务器部署，自动定时运行：
```bash
# Windows
start_daemon.bat

# Linux/macOS
nohup python main.py --mode daemon &
```

### 3. 仅发送邮件
如果已有分析结果，只想发送邮件：
```bash
python send_detailed_report.py
```

### 4. 测试邮件功能
验证邮箱配置是否正确：
```bash
python main.py --mode test
```

## 📊 数据来源

- **股票数据**: AkShare (akshare.readthedocs.io)
- **实时PE数据**: 腾讯财经API
- **沪深300成分股**: 实时获取最新成分股列表

## ⚠️ 风险提示

1. **投资风险**: 本系统仅供参考，不构成投资建议
2. **数据延迟**: 数据可能存在延迟，请以实际交易价格为准
3. **市场风险**: 股市有风险，投资需谨慎
4. **策略局限**: 任何量化策略都有局限性，建议结合人工判断

## 🛠️ 技术栈

- **Python 3.8+**
- **AkShare**: 金融数据接口
- **Pandas/NumPy**: 数据分析
- **Schedule**: 定时任务
- **SMTP**: 邮件发送

## 📝 更新日志

### v2.0.0 (2025-10-11)
- ✨ 全新升级邮件报告，更详细、更精美
- 📊 新增全市场统计（5,000+只股票）
- 🎨 优化HTML设计，渐变色+数据卡片
- 💡 新增市场特征分析和操作建议
- ⚠️ 增强风险提示功能
- 🔧 修复邮件发送问题
- 📄 新增邮件配置说明文档

### v1.0.0 (2025-09-30)
- 🎉 初始版本发布
- 📊 基于沪深300的量化选股系统
- 📧 基础邮件报告功能
- ⏰ 定时任务调度

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 📧 Email: 1120311927@qq.com
- 💬 Issue: [GitHub Issues](https://github.com/yourusername/stock_analyzer/issues)

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**
