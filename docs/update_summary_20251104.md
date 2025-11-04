# 评分系统优化总结 (2025-11-04)

## 本次更新概述

本次更新解决了两个核心问题：
1. ✅ **股息率数据不准确** - 实现手动股息率覆盖功能
2. ✅ **流动性评分不公平** - 改用换手率替代成交额评分

---

## 问题1: 股息率数据不准确

### 问题描述

腾讯财经API返回的股息率数据存在严重偏差：

| 股票 | API股息率 | 实际股息率 | 差异 |
|------|----------|-----------|------|
| 中国人寿(601628) | 5.55% | 1.48% | 偏高275% |

导致股息评分不准确：
- **修正前**：股息率5.55% → 得5分（满分）
- **修正后**：股息率1.48% → 得1分（正确）

### 解决方案

实现**手动股息率配置**功能：

1. **新增配置文件** [`config/dividend_override.py`](../config/dividend_override.py)
   ```python
   DIVIDEND_OVERRIDE = {
       '601628': {  # 中国人寿
           'dividend_yield': 1.48,  # 实际股息率
           'dividend_per_share': 0.65,  # 每股股息
           'year': 2024,
           'note': '2024年派息0.65元/股'
       },
   }
   ```

2. **修改数据获取逻辑** [`src/data/data_fetcher.py`](../src/data/data_fetcher.py#L208-L215)
   - 优先使用手动配置的股息率
   - 如无配置则使用API数据

### 效果对比

#### 中国人寿评分变化

| 项目 | 修正前 | 修正后 |
|------|--------|--------|
| 股息率 | 5.55%❌ | 1.48%✅ |
| 股息得分 | 5分 | 1分 |
| 技术面 | 19分 | 19分 |
| 估值 | 23分 | 23分 |
| 盈利能力 | 27分 | 27分 |
| 安全性 | 6分 | 6分 |
| **总评分** | **82分(A级)** | **76分(A级)** |
| **排名** | **第1名** | **第4名** |

### 使用方法

编辑 [`config/dividend_override.py`](../config/dividend_override.py) 添加新股票：

```python
'股票代码': {
    'dividend_yield': 实际股息率(%),
    'dividend_per_share': 每股股息(元),
    'year': 年份,
    'note': '数据来源说明'
},
```

---

## 问题2: 流动性评分不公平

### 问题描述

原流动性评分使用**成交额绝对值**，存在以下问题：

#### 问题案例对比

| 股票类型 | 成交额 | 换手率 | 原评分 | 问题 |
|---------|--------|--------|--------|------|
| 大盘股 | 96,967万 | 1.38% | 5分✅ | 天然优势 |
| 小盘股 | 5,000万 | 2.5% | 0分❌ | 被歧视 |
| 妖股 | 50,000万 | 25% | 5分❌ | 错误高分 |

**核心问题**：
- ❌ 大市值股票天然成交额高，小盘股处于劣势
- ❌ 无法识别高换手的投机股风险
- ❌ 固定阈值(10000万)对不同市值股票意义不同

### 解决方案

改用**换手率**作为流动性评分指标：

```
换手率(%) = 成交额 / 流通市值 × 100
```

#### 新评分标准

| 换手率范围 | 评分 | 说明 |
|-----------|------|------|
| 1% - 3% | 5分 | ✅ 流动性最佳（适中活跃） |
| 3% - 5% | 4分 | ✅ 流动性良好 |
| 5% - 8% | 3分 | ⚠️ 流动性充足（略偏高） |
| 0.5% - 1% | 2分 | ⚠️ 流动性偏低 |
| > 8% | 1分 | ❌ 换手过高（投机性强） |
| < 0.5% | 0分 | ❌ 流动性不足 |

### 代码修改

**修改前** - 使用成交额：
```python
# 1.3 流动性 (5分)
turnover = stock_data.get('turnover', 0)
min_turnover = self.config.get('min_turnover', 10000)
if turnover > min_turnover * 3:
    score_breakdown['technical'] += 5
```

**修改后** - 使用换手率：
```python
# 1.3 流动性 (5分) - 基于换手率
turnover_rate = stock_data.get('turnover_rate', 0)
if turnover_rate and 1 <= turnover_rate < 3:  # 最佳流动性
    score_breakdown['technical'] += 5
elif turnover_rate and 3 <= turnover_rate < 5:  # 良好
    score_breakdown['technical'] += 4
elif turnover_rate and 5 <= turnover_rate < 8:  # 充足
    score_breakdown['technical'] += 3
elif turnover_rate and 0.5 <= turnover_rate < 1:  # 偏低
    score_breakdown['technical'] += 2
elif turnover_rate and turnover_rate >= 8:  # 过高
    score_breakdown['technical'] += 1
```

### 效果对比

#### 案例1: 大盘蓝筹（中国人寿）
- 成交额：96,967万
- 换手率：1.38%
- **修改前**：5分 ✅
- **修改后**：5分 ✅
- **结论**：评分一致

#### 案例2: 小盘活跃股
- 成交额：5,000万（低于阈值）
- 换手率：2.5%（活跃度适中）
- **修改前**：0分 ❌ 不公平！
- **修改后**：5分 ✅ 公平！
- **结论**：小盘股得到公平对待

#### 案例3: 高换手妖股
- 成交额：50,000万（高于阈值）
- 换手率：25%（投机严重）
- **修改前**：5分 ❌ 错误！
- **修改后**：1分 ✅ 正确识别风险！
- **结论**：能识别投机风险

---

## 测试验证

### 测试1: 股息率修正

运行测试脚本：
```bash
python test_dividend_fix.py
```

**测试结果**：
```
[SUCCESS] 测试通过！股息率已成功修正为1.48%，评分为1分
```

### 测试2: 换手率评分

运行测试脚本：
```bash
python test_turnover_rate_scoring.py
```

**测试结果**：
```
测试结果: 5个通过, 0个失败
[SUCCESS] 所有测试用例通过!
```

测试覆盖场景：
- ✅ 大盘蓝筹（换手率1.38%）
- ✅ 小盘活跃股（换手率2.5%）
- ✅ 高换手妖股（换手率25%）
- ✅ 流动性不足（换手率0.3%）
- ✅ 换手率良好（换手率4.0%）

---

## 核心优势

### 优势1: 数据准确性提升

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 股息率数据源 | 仅API | API + 手动配置 |
| 数据准确性 | 存在偏差 | ✅ 可人工纠正 |
| 可维护性 | 无法修正 | ✅ 配置文件管理 |

### 优势2: 评分公平性提升

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 流动性指标 | 成交额绝对值 | 换手率相对值 |
| 小盘股评分 | ❌ 被歧视 | ✅ 公平对待 |
| 风险识别 | ❌ 无法识别妖股 | ✅ 识别投机风险 |
| 评分一致性 | ❌ 依赖市值 | ✅ 统一标准 |

### 优势3: 系统科学性提升

1. **换手率是相对指标**
   - 消除市值规模影响
   - 大小盘统一标准

2. **换手率有经济意义**
   - 反映交易活跃度
   - 识别投机行为

3. **数据可直接获取**
   - API直接提供换手率
   - 无需额外计算

---

## 相关文件

### 新增文件

1. **配置文件**
   - [`config/dividend_override.py`](../config/dividend_override.py) - 股息率手动配置

2. **文档**
   - [`docs/dividend_override_guide.md`](dividend_override_guide.md) - 股息率修正使用指南
   - [`docs/turnover_rate_scoring_design.md`](turnover_rate_scoring_design.md) - 换手率评分设计文档
   - [`docs/update_summary_20251031.md`](update_summary_20251031.md) - 本文档

3. **测试脚本**
   - [`test_dividend_fix.py`](../test_dividend_fix.py) - 股息率修正测试
   - [`test_dividend_601628.py`](../test_dividend_601628.py) - API数据查看
   - [`test_turnover_rate_scoring.py`](../test_turnover_rate_scoring.py) - 换手率评分测试

### 修改文件

1. **核心代码**
   - [`src/data/data_fetcher.py`](../src/data/data_fetcher.py#L208-L215) - 应用手动股息率
   - [`src/analysis/stock_filter.py`](../src/analysis/stock_filter.py#L48-L61) - 换手率评分逻辑

---

## 后续建议

### 1. 股息率维护

- **定期更新**：每季度财报发布后更新配置
- **数据来源**：以公司公告为准
- **验证机制**：添加后运行测试脚本验证

### 2. 换手率阈值优化

根据市场实际情况，可以调整换手率评分区间：

```python
# 可在 stock_filter.py 中调整阈值
if 1 <= turnover_rate < 3:  # 可调整为 0.8-2.5
    score += 5
```

### 3. 其他指标优化

可以考虑类似的改进：
- 成交量 → 量比
- 市值 → 市值分档评分
- 价格 → 价格相对位置

---

## 版本信息

- **更新日期**: 2025-11-04
- **版本**: v4.5
- **维护者**: Claude
- **测试状态**: ✅ 全部通过

---

## 快速开始

### 添加手动股息率

1. 编辑 `config/dividend_override.py`
2. 添加股票配置
3. 运行 `python test_dividend_fix.py` 验证

### 查看换手率评分

运行测试查看不同换手率的评分：
```bash
python test_turnover_rate_scoring.py
```

### 运行主程序

```bash
python main.py
```

新的评分逻辑将自动生效！
