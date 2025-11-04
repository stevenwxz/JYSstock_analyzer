# 股息率手动修正功能说明

## 问题背景

腾讯财经API返回的股息率数据存在不准确的情况。例如：

- **中国人寿 (601628)**
  - API返回的股息率：5.55%
  - 实际股息率：1.48%（2024年派息0.65元/股，股价44元）
  - 差异原因：API数据可能是累计历史数据或计算错误

这导致股息评分不准确，中国人寿原本应该得1分，却得到了5分。

## 解决方案

实现了**手动股息率覆盖**功能，可以在配置文件中为特定股票设置准确的股息率数据。

## 使用方法

### 1. 添加手动配置

编辑文件 `config/dividend_override.py`，在 `DIVIDEND_OVERRIDE` 字典中添加股票：

```python
DIVIDEND_OVERRIDE = {
    '601628': {  # 股票代码
        'dividend_yield': 1.48,  # 实际股息率(%)
        'dividend_per_share': 0.65,  # 每股股息(元)
        'year': 2024,  # 年份
        'note': '2024年派息：中期+末期共0.65元/股'  # 备注
    },

    # 添加更多股票...
    '600000': {
        'dividend_yield': 3.2,
        'dividend_per_share': 0.28,
        'year': 2024,
        'note': '2024年派息数据'
    },
}
```

### 2. 数据来源

手动配置的股息率数据可以从以下渠道获取：

1. **公司公告** - 最权威的数据来源
2. **东方财富网** - https://www.eastmoney.com/
3. **同花顺** - http://www.10jqka.com.cn/
4. **公司财报** - 年报、半年报中的分红方案
5. **交易所公告** - 上交所、深交所官网

### 3. 计算股息率

```
股息率(%) = (每股股息 / 当前股价) × 100
```

例如：
- 每股股息：0.65元
- 当前股价：44元
- 股息率 = (0.65 / 44) × 100 = 1.48%

## 功能实现

### 工作流程

1. **数据获取时** (`data_fetcher.py`)
   - 首先检查是否有手动配置的股息率
   - 如果有，使用手动配置的值
   - 如果没有，使用API返回的值

2. **评分计算时** (`stock_filter.py`)
   - 直接使用 `stock_data` 中的 `dividend_yield` 字段
   - 无需修改评分逻辑

### 代码修改

**修改1：** `src/data/data_fetcher.py`

```python
# 导入手动配置
from config.dividend_override import get_manual_dividend_yield, has_manual_override

# 获取股息率时优先使用手动配置
manual_dividend = get_manual_dividend_yield(stock_code)
if manual_dividend is not None:
    dividend_yield = manual_dividend
    logger.debug(f"{stock_code} 使用手动配置的股息率: {dividend_yield}%")
elif data_parts[52]:
    # 使用API数据
    dividend_yield = float(data_parts[52])
```

## 股息评分规则

当前的股息评分逻辑（满分5分）：

| 股息率范围 | 得分 |
|-----------|------|
| > 5%      | 5分  |
| > 3%      | 4分  |
| > 2%      | 2分  |
| > 0%      | 1分  |
| = 0%      | 0分  |

## 修正效果

### 修正前（中国人寿）
- 股息率：5.55%（API错误数据）
- 股息得分：**5分**
- 总评分：82分

### 修正后（中国人寿）
- 股息率：1.48%（手动配置）
- 股息得分：**1分**
- 总评分：约78分（更准确）

## 测试

运行测试脚本验证修正是否生效：

```bash
python test_dividend_fix.py
```

期望输出：
```
[SUCCESS] 测试通过！股息率已成功修正为1.48%，评分为1分
```

## 维护建议

1. **定期更新** - 每个财报季后检查并更新股息率数据
2. **关注公告** - 留意上市公司的分红公告
3. **验证数据** - 添加新配置后运行测试验证
4. **记录来源** - 在 `note` 字段中记录数据来源和时间

## 其他注意事项

1. **优先级**：手动配置 > API数据
2. **适用范围**：仅当API数据明显错误时才使用手动配置
3. **数据时效**：注意配置的股息率对应的时间周期
4. **除权除息**：股价发生除权除息时需要重新计算股息率

## 相关文件

- `config/dividend_override.py` - 股息率配置文件
- `src/data/data_fetcher.py` - 数据获取（应用手动配置）
- `src/analysis/stock_filter.py` - 评分计算
- `test_dividend_fix.py` - 功能测试脚本
- `test_dividend_601628.py` - API数据查看脚本

---

**更新时间：** 2025-10-31
**版本：** v1.0
