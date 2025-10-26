# 📖 使用说明

## 目录

- [快速开始](#快速开始)
- [实盘运行](#实盘运行)
- [历史回测](#历史回测)
- [配置调优](#配置调优)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置邮箱（可选）

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件
# EMAIL_ADDRESS=your_email@qq.com
# EMAIL_PASSWORD=your_smtp_password
```

### 3. 运行测试

```bash
# 单次运行，立即分析
python main.py
```

---

## 实盘运行

### 立即分析

```bash
python main.py
```

输出示例：

```
📊 开始分析沪深300股票...
✅ 获取到 300 只沪深300成分股
🔍 筛选配置：
   • PE上限: 30
   • 成交额: 5000万元
   • 强势分数: ≥50

🏆 推荐股票 (3只):
   #1 股票A (600xxx): ¥50.00, PE=15.5, 分数=85
       分项得分:
         - 技术面: 25分
         - 估值: 20分
         - 盈利能力: 25分
         - 安全性: 10分
         - 股息: 5分
       评级: A+
   #2 股票B (000xxx): ¥30.00, PE=20.2, 分数=78
       分项得分:
         - 技术面: 22分
         - 估值: 18分
         - 盈利能力: 22分
         - 安全性: 9分
         - 股息: 5分
       评级: A
   #3 股票C (002xxx): ¥25.00, PE=18.0, 分数=72
       分项得分:
         - 技术面: 20分
         - 估值: 17分
         - 盈利能力: 20分
         - 安全性: 8分
         - 股息: 5分
       评级: B+
```

### 定时任务

```bash
# 每日16:00自动分析
python main.py --schedule
```

定时任务会：

1. 每天16:00执行股票分析
2. 16:30自动发送邮件
3. 仅工作日运行（可配置）

---

## 历史回测

### 单日回测

```bash
python run_backtest_optimized.py
```

交互式输入：

```
请选择回测模式:
1. 单日回测
2. 多日回测

请输入选项: 1
请输入回测日期: 2025-04-07
请输入持有天数: 1
```

结果示例：

```
📅 回测日期: 2025-04-07 | 持有1天

🏆 筛选结果 (3只):
   #1 天坛生物 (600161): ¥21.77, PE=20.0, 分数=90
       分项得分:
         - 技术面: 28分
         - 估值: 22分
         - 盈利能力: 25分
         - 安全性: 10分
         - 股息: 5分
       评级: A+
       涨跌幅: +5.14% → ¥22.89 (+5.14%)
   #2 龙源电力 (001289): ¥17.55, PE=20.0, 分数=80
       分项得分:
         - 技术面: 25分
         - 估值: 20分
         - 盈利能力: 22分
         - 安全性: 9分
         - 股息: 4分
       评级: A
       涨跌幅: +1.82% → ¥17.87 (+1.82%)
   #3 东鹏饮料 (605499): ¥250.00, PE=20.0, 分数=65
       分项得分:
         - 技术面: 20分
         - 估值: 18分
         - 盈利能力: 19分
         - 安全性: 5分
         - 股息: 3分
       评级: B+
       涨跌幅: +0.40% → ¥251.00 (+0.40%)

📊 策略表现:
   • 平均收益: +2.46%
   • 收益区间: +0.40% ~ +5.14%
   • 胜率: 100.0% (3/3)
```

### 多日回测

用于统计一段时间的策略表现：

```bash
python run_backtest_optimized.py

# 选择模式 2
请输入开始日期: 2025-04-01
请输入结束日期: 2025-04-07
请输入持有天数: 1
```

---

## 配置调优

### 实盘配置 (`config/config.py`)

根据你的风险偏好调整参数：

#### 保守型配置

```python
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 20,          # PE更严格
    'min_turnover': 10000,   # 成交额1亿（超大盘股）
    'min_strength_score': 60,    # 更高的强势要求
    'max_stocks': 2              # 只推荐2只
}
```

#### 激进型配置

```python
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 50,          # PE更宽松
    'min_turnover': 3000,    # 成交额3000万
    'min_strength_score': 40,    # 降低门槛
    'max_stocks': 5              # 推荐5只
}
```

#### 平衡型配置（默认）

```python
STOCK_FILTER_CONFIG = {
    'max_pe_ratio': 30,
    'min_turnover': 5000,    # 5000万
    'min_strength_score': 50,
    'max_stocks': 3
}
```

### 回测配置 (`config/backtest_config.py`)

#### 加速回测（降低精度）

```python
BACKTEST_SAMPLE_CONFIG = {
    'sample_size': 100,          # 只采样100只
    'cache_expire_days': 30      # 缓存30天
}
```

#### 精确回测（默认）

```python
BACKTEST_SAMPLE_CONFIG = {
    'sample_size': 300,          # 全部300只
    'cache_expire_days': 7       # 缓存7天
}
```

---

## 常见问题

### Q1: 如何清除缓存？

```bash
# Linux/Mac
rm -rf cache/

# Windows
rmdir /s cache
```

### Q2: 为什么筛选不出股票？

可能原因：

1. **强势分数太高** - 降低 `min_strength_score` 到 40
2. **成交额门槛太高** - 降低 `min_turnover` 到 3000
3. **PE要求太严格** - 提高 `max_pe_ratio` 到 50
4. **当日市场行情差** - 换个日期测试

调整配置：

```python
# 临时降低要求
BACKTEST_FILTER_CONFIG = {
    'max_pe_ratio': 50,
    'min_turnover': 20000000,
    'min_strength_score': 30
}
```

### Q3: 邮件发送失败怎么办？

1. **检查.env配置**

   ```bash
   cat .env
   # 确认邮箱和密码正确
   ```
2. **QQ邮箱需要SMTP授权码**

   - 登录QQ邮箱网页版
   - 设置 -> 账户 -> POP3/IMAP/SMTP服务
   - 开启SMTP服务
   - 生成授权码（16位）
   - 将授权码填入 `.env` 的 `EMAIL_PASSWORD`
3. **网络问题**

   ```bash
   # 测试SMTP连接
   telnet smtp.qq.com 587
   ```

### Q4: 回测速度慢怎么办？

1. **启用缓存**（默认已启用）
2. **减少采样数量**
   ```python
   BACKTEST_SAMPLE_CONFIG = {
       'sample_size': 100  # 从300改为100
   }
   ```
3. **增加缓存有效期**
   ```python
   'cache_expire_days': 30  # 从7改为30
   ```

### Q5: 数据获取失败？

可能是网络波动或API限流：

1. **等待几秒后重试**
2. **检查网络连接**
3. **更新akshare版本**
   ```bash
   pip install --upgrade akshare
   ```

### Q6: 如何修改推荐数量？

```python
# config/config.py
STOCK_FILTER_CONFIG = {
    'max_stocks': 5  # 改为5只
}
```

### Q7: 如何只分析特定日期？

```bash
python run_backtest_optimized.py
# 选择模式1，输入具体日期
```

### Q8: 强势分数是如何计算的？

采用5维评分系统（满分100分）- v4.4优化版：

```
总分 = 技术面(30分) + 估值(25分) + 盈利能力(30分) + 安全性(10分) + 股息(5分)

示例（v4.4新标准）：
- 技术面：当日涨5% → 10分，20日涨12% → 15分，成交额>1.5亿 → 5分，合计30分
- 估值：PE=12 → 7分，PB=1.5 → 10分，PEG=0.8 → 5分，合计22分
- 盈利能力：ROE=20% → 15分，利润增长30% → 15分，合计30分
- 安全性：PB=1.5 → 1分，股息率=4% → 3分，换手率=2% → 4分，合计8分
- 股息：股息率=4% → 4分
总分 = 30 + 22 + 30 + 8 + 4 = 94分

详细评分标准：
【估值部分 - v4.4放宽】
- PE: <10→10分, <20→7分, <30→4分
- PB: <2→10分, <4→8分, <7→5分, <10→2分 (对成长股更友好)
- PEG: <1→5分, <1.5→3分

【安全性部分 - v4.4优化】
- PB安全边际: <1.0→3分, <1.5→2分, <2.5→1分 (明确安全边际概念)
- 股息率: >5%→3分, >3%→2分, >1%→1分
- 换手率: <2%→4分, <5%→3分, <10%→1分 (权重增加)
```

**评级标准**:
- A+: 90-100分
- A: 80-89分
- B+: 70-79分
- B: 60-69分
- C: 50-59分
- D: <50分

---

## 进阶用法

### 1. 批量回测

创建脚本 `batch_backtest.py`：

```python
from run_backtest_optimized import OptimizedBacktest

backtest = OptimizedBacktest()

dates = ['2025-04-01', '2025-04-02', '2025-04-03']
for date in dates:
    print(f"\n回测日期: {date}")
    result = backtest.backtest_single_day(date, hold_days=1)
```

### 2. 自定义筛选逻辑

编辑 `src/analysis/stock_filter.py` 中的 `calculate_strength_score` 方法。

### 3. 导出到Excel

```python
import pandas as pd
import json

# 读取回测结果
with open('backtest_opt_2025-04-07_1days.json', 'r') as f:
    data = json.load(f)

# 转为DataFrame
df = pd.DataFrame(data['performance'])
df.to_excel('回测结果.xlsx', index=False)
```

---

## 最佳实践

1. **先回测再实盘** - 用历史数据验证策略
2. **定期清理缓存** - 每周清理一次，保持数据新鲜
3. **分散投资** - 不要只买推荐的股票
4. **设置止损** - 亏损超过5%及时止损
5. **长期跟踪** - 记录每日推荐，统计实际胜率

---

## 获取帮助

遇到问题？

1. 查看[常见问题](#常见问题)
2. 提交Issue
3. 查看代码注释

---

⭐ 如果这个文档对你有帮助，欢迎给项目点个Star！
