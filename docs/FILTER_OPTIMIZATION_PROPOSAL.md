# 股票筛选机制优化方案

## 当前筛选机制分析

### 现有指标
1. **PE市盈率** (估值指标)
2. **涨跌幅** (短期动量)
3. **20日动量** (中期趋势)
4. **成交额/流动性** (市场活跃度)
5. **价格** (基本过滤)

### 主要不足
❌ **缺少盈利质量指标** - 没有ROE、净利润增长率等
❌ **缺少财务安全性指标** - 没有负债率、流动比率
❌ **缺少估值综合评估** - 仅用PE,没有PB、PS、PEG
❌ **缺少成长性指标** - 没有营收增长、利润增长
❌ **缺少分红指标** - 没有股息率
❌ **缺少行业对比** - 没有相对估值分析

---

## 优化方案

### 方案一: 增强基本面筛选 (推荐)

#### 新增指标类别

#### 1. **盈利质量指标** (ROE为核心)

| 指标 | 说明 | 优秀标准 | 数据来源 |
|------|------|----------|----------|
| **ROE (净资产收益率)** | 衡量股东权益回报率 | >15% | 腾讯财经/东方财富 |
| **ROA (总资产收益率)** | 衡量资产使用效率 | >5% | 腾讯财经 |
| **净利润增长率** | YoY同比增长 | >15% | 腾讯财经 |
| **营收增长率** | YoY同比增长 | >10% | 腾讯财经 |
| **毛利率** | 盈利能力 | >30% | 腾讯财经 |

**ROE筛选逻辑:**
```python
# 巴菲特标准: 连续3年ROE>15%
def filter_by_roe(stock):
    roe = stock.get('roe', 0)
    if roe > 20:  # 优秀
        return True, 30  # 得分30
    elif roe > 15:  # 良好
        return True, 20
    elif roe > 10:  # 及格
        return True, 10
    else:
        return False, 0
```

#### 2. **估值综合指标**

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| **PB (市净率)** | 市值/净资产 | 0.8-3.0 |
| **PS (市销率)** | 市值/营收 | <3 |
| **PEG** | PE/净利润增长率 | <1 |
| **EV/EBITDA** | 企业价值倍数 | <10 |

#### 3. **财务安全性指标**

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| **资产负债率** | 债务/资产 | <60% |
| **流动比率** | 流动资产/流动负债 | >1.5 |
| **速动比率** | (流动资产-存货)/流动负债 | >1.0 |

#### 4. **分红指标**

| 指标 | 说明 | 优秀标准 |
|------|------|----------|
| **股息率** | 年度分红/股价 | >3% |
| **分红率** | 分红/净利润 | 30-70% |

### 改进后的评分系统

#### 新的强势分数构成 (100分制)

```python
def calculate_enhanced_strength_score(stock_data: Dict) -> Dict:
    """增强版强势分数计算"""
    score_breakdown = {
        'technical': 0,    # 技术面 (30分)
        'valuation': 0,    # 估值 (25分)
        'profitability': 0,  # 盈利质量 (30分)
        'safety': 0,       # 安全性 (10分)
        'dividend': 0      # 分红 (5分)
    }

    # 1. 技术面得分 (30分)
    # 1.1 涨跌幅 (10分)
    change_pct = stock_data.get('change_pct', 0)
    if change_pct > 5:
        score_breakdown['technical'] += 10
    elif change_pct > 2:
        score_breakdown['technical'] += 7
    elif change_pct > 0:
        score_breakdown['technical'] += 4

    # 1.2 动量 (15分)
    momentum = stock_data.get('momentum_20d', 0)
    if momentum > 15:
        score_breakdown['technical'] += 15
    elif momentum > 10:
        score_breakdown['technical'] += 10
    elif momentum > 5:
        score_breakdown['technical'] += 5

    # 1.3 流动性 (5分)
    turnover = stock_data.get('turnover', 0)
    if turnover > 100000:  # 1亿
        score_breakdown['technical'] += 5
    elif turnover > 50000:
        score_breakdown['technical'] += 3

    # 2. 估值得分 (25分)
    # 2.1 PE (10分)
    pe = stock_data.get('pe_ratio', 0)
    if 0 < pe < 15:
        score_breakdown['valuation'] += 10
    elif 15 <= pe < 25:
        score_breakdown['valuation'] += 7
    elif 25 <= pe < 35:
        score_breakdown['valuation'] += 4

    # 2.2 PB (8分)
    pb = stock_data.get('pb_ratio', 0)
    if 0 < pb < 2:
        score_breakdown['valuation'] += 8
    elif 2 <= pb < 3:
        score_breakdown['valuation'] += 5

    # 2.3 PEG (7分)
    peg = stock_data.get('peg', 0)
    if 0 < peg < 1:
        score_breakdown['valuation'] += 7
    elif 1 <= peg < 1.5:
        score_breakdown['valuation'] += 4

    # 3. 盈利质量得分 (30分) - 核心
    # 3.1 ROE (15分)
    roe = stock_data.get('roe', 0)
    if roe > 20:
        score_breakdown['profitability'] += 15
    elif roe > 15:
        score_breakdown['profitability'] += 12
    elif roe > 10:
        score_breakdown['profitability'] += 8
    elif roe > 5:
        score_breakdown['profitability'] += 4

    # 3.2 净利润增长率 (10分)
    profit_growth = stock_data.get('profit_growth', 0)
    if profit_growth > 30:
        score_breakdown['profitability'] += 10
    elif profit_growth > 20:
        score_breakdown['profitability'] += 8
    elif profit_growth > 10:
        score_breakdown['profitability'] += 5

    # 3.3 毛利率 (5分)
    gross_margin = stock_data.get('gross_margin', 0)
    if gross_margin > 50:
        score_breakdown['profitability'] += 5
    elif gross_margin > 30:
        score_breakdown['profitability'] += 3

    # 4. 安全性得分 (10分)
    # 4.1 资产负债率 (6分)
    debt_ratio = stock_data.get('debt_ratio', 0)
    if debt_ratio < 30:
        score_breakdown['safety'] += 6
    elif debt_ratio < 50:
        score_breakdown['safety'] += 4
    elif debt_ratio < 70:
        score_breakdown['safety'] += 2

    # 4.2 流动比率 (4分)
    current_ratio = stock_data.get('current_ratio', 0)
    if current_ratio > 2:
        score_breakdown['safety'] += 4
    elif current_ratio > 1.5:
        score_breakdown['safety'] += 3
    elif current_ratio > 1:
        score_breakdown['safety'] += 1

    # 5. 分红得分 (5分)
    dividend_yield = stock_data.get('dividend_yield', 0)
    if dividend_yield > 5:
        score_breakdown['dividend'] += 5
    elif dividend_yield > 3:
        score_breakdown['dividend'] += 4
    elif dividend_yield > 2:
        score_breakdown['dividend'] += 2

    total_score = sum(score_breakdown.values())

    return {
        'total_score': total_score,
        'breakdown': score_breakdown,
        'grade': get_grade(total_score)
    }

def get_grade(score):
    """评级"""
    if score >= 85: return 'A+'
    elif score >= 75: return 'A'
    elif score >= 65: return 'B+'
    elif score >= 55: return 'B'
    elif score >= 45: return 'C'
    else: return 'D'
```

### 数据获取实现

#### 方案A: 使用腾讯财经API (推荐)

```python
def get_stock_fundamental_data(stock_code: str) -> Dict:
    """获取股票基本面数据 - 腾讯财经API"""
    import requests

    # 确定市场代码
    if stock_code.startswith('6'):
        symbol = f"sh{stock_code}"
    else:
        symbol = f"sz{stock_code}"

    # 1. 获取基础数据
    base_url = f"https://qt.gtimg.cn/q={symbol}"
    response = requests.get(base_url, timeout=10)

    # 解析基础数据...

    # 2. 获取财务指标数据
    finance_url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    # 腾讯提供的财务数据接口

    fundamental_data = {
        'roe': 0,  # 净资产收益率
        'roa': 0,  # 总资产收益率
        'pb_ratio': 0,  # 市净率
        'profit_growth': 0,  # 净利润增长率
        'revenue_growth': 0,  # 营收增长率
        'debt_ratio': 0,  # 资产负债率
        'current_ratio': 0,  # 流动比率
        'gross_margin': 0,  # 毛利率
        'dividend_yield': 0,  # 股息率
        'peg': 0  # PEG
    }

    return fundamental_data
```

#### 方案B: 使用akshare库

```python
import akshare as ak

def get_fundamental_data_akshare(stock_code: str) -> Dict:
    """使用akshare获取基本面数据"""
    try:
        # 1. 财务指标
        financial_data = ak.stock_financial_abstract(symbol=stock_code)

        # 2. ROE数据
        roe_data = ak.stock_roe_ttm(symbol=stock_code)

        # 3. 估值数据
        valuation = ak.stock_a_lg_indicator(symbol=stock_code)

        return {
            'roe': roe_data[-1] if len(roe_data) > 0 else 0,
            'pb_ratio': valuation['市净率'][-1],
            # ... 其他指标
        }
    except Exception as e:
        logger.error(f"获取基本面数据失败: {e}")
        return {}
```

---

## 实施步骤

### Phase 1: 基础实现 (1-2天)
1. ✅ 添加ROE数据获取接口
2. ✅ 修改评分系统,加入ROE权重
3. ✅ 更新筛选逻辑
4. ✅ 测试基本功能

### Phase 2: 完善指标 (2-3天)
1. ✅ 添加PB、PEG等估值指标
2. ✅ 添加负债率、流动比率
3. ✅ 添加利润增长率
4. ✅ 完善评分算法

### Phase 3: 优化展示 (1天)
1. ✅ 更新报告模板,展示新指标
2. ✅ 添加详细的评分说明
3. ✅ 可视化得分分布

### Phase 4: 验证回测 (2-3天)
1. ✅ 历史数据回测
2. ✅ 对比新旧策略收益
3. ✅ 调整权重参数

---

## 预期效果

### 筛选质量提升
- **更科学**: 从单纯技术面 → 技术+基本面结合
- **更全面**: PE → PE+PB+PEG+ROE+成长性
- **更安全**: 加入财务安全性检查
- **更稳定**: 盈利质量好的公司长期表现更佳

### 示例对比

#### 优化前筛选结果:
```
#1 特变电工 (600089)
   PE: 22.72, 涨跌: +2.01%, 动量: 34.37%
   强势分数: 90.0
```

#### 优化后筛选结果:
```
#1 特变电工 (600089)
   PE: 22.72, PB: 2.1, PEG: 0.8
   涨跌: +2.01%, 动量: 34.37%
   ROE: 18.5%, 净利润增长: 28%
   负债率: 45%, 股息率: 2.5%

   综合评分: 82/100 (A级)
   ├─ 技术面: 28/30
   ├─ 估值: 20/25
   ├─ 盈利质量: 25/30 ⭐
   ├─ 安全性: 7/10
   └─ 分红: 2/5

   推荐理由: 技术面强势,估值合理,ROE优秀,
           成长性良好,财务稳健
```

---

## 配置示例

```yaml
# config/filter_config.yaml

# 基本面指标权重
fundamental_weights:
  roe: 0.15          # ROE权重 15%
  profit_growth: 0.10 # 利润增长 10%
  debt_ratio: 0.06    # 负债率 6%
  pb_ratio: 0.08      # PB 8%
  dividend: 0.05      # 分红 5%

# 筛选标准
filter_criteria:
  roe:
    min: 10           # 最低ROE 10%
    excellent: 20     # 优秀标准 20%

  pb_ratio:
    min: 0.5
    max: 5

  debt_ratio:
    max: 70           # 最大负债率 70%

  profit_growth:
    min: 10           # 最低增长 10%

  dividend_yield:
    prefer: 3         # 偏好股息率 3%以上

# 评分系统
scoring:
  min_score: 60       # 最低综合分 60分
  grade_a_min: 75     # A级最低分
  prefer_grades: ['A+', 'A', 'B+']
```

---

## API数据源对比

| 指标 | 腾讯财经 | 新浪财经 | 东方财富 | akshare |
|------|---------|---------|---------|---------|
| ROE | ✅ | ✅ | ✅ | ✅ |
| PB | ✅ | ✅ | ✅ | ✅ |
| 负债率 | ✅ | ❌ | ✅ | ✅ |
| 利润增长 | ✅ | ❌ | ✅ | ✅ |
| 股息率 | ✅ | ✅ | ✅ | ✅ |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

**推荐**: 优先使用腾讯财经API + akshare作为补充

---

## 总结

通过增加ROE等基本面指标,可以:
1. **提高选股质量** - 选出真正有价值的好公司
2. **降低风险** - 避开财务风险高的公司
3. **长期收益更好** - 基本面好的公司长期表现优异
4. **更符合价值投资理念** - 技术+基本面双重保障

建议**优先实现ROE、PB、利润增长率、负债率**这4个核心指标,效果会有显著提升!
