# 📁 项目结构说明

## 整体架构

```
jys/ (项目根目录)
├── 📱 miniprogram/                    # 微信小程序前端 (新增)
│   ├── pages/                         # 页面文件
│   │   ├── index/                     # 首页 - 今日推荐
│   │   │   ├── index.wxml             # 页面结构
│   │   │   ├── index.wxss             # 页面样式
│   │   │   ├── index.js               # 页面逻辑
│   │   │   └── index.json             # 页面配置
│   │   ├── detail/                    # 股票详情页
│   │   │   ├── detail.wxml
│   │   │   ├── detail.wxss
│   │   │   ├── detail.js
│   │   │   └── detail.json
│   │   └── history/                   # 历史记录页
│   │       ├── history.wxml
│   │       ├── history.wxss
│   │       ├── history.js
│   │       └── history.json
│   ├── images/                        # 图片资源 (需添加图标)
│   ├── utils/                         # 工具函数
│   ├── app.js                         # 小程序入口文件
│   ├── app.json                       # 小程序全局配置
│   ├── app.wxss                       # 小程序全局样式
│   ├── project.config.json            # 项目配置文件
│   └── sitemap.json                   # 站点地图配置
│
├── 🐍 stock_analyzer/                 # 后端Python服务
│   ├── 🆕 api_server.py               # Flask API服务器 (新增)
│   ├── 🆕 requirements_api.txt        # API服务依赖 (新增)
│   ├── main.py                        # 原有实盘分析入口
│   ├── run_backtest_optimized.py      # 回测入口
│   ├── update_csi300_stocks.py        # 更新股票列表
│   │
│   ├── config/                        # 配置文件
│   │   ├── config.py                  # 实盘配置
│   │   ├── backtest_config.py         # 回测配置
│   │   └── dividend_override.py       # 股息率修正
│   │
│   ├── src/                           # 核心源代码
│   │   ├── data/                      # 数据获取模块
│   │   │   ├── data_fetcher.py        # 股票数据获取
│   │   │   └── async_data_fetcher.py  # 异步数据获取
│   │   ├── analysis/                  # 分析模块
│   │   │   ├── stock_filter.py        # 股票筛选
│   │   │   ├── market_analyzer.py     # 市场分析
│   │   │   └── backtest.py            # 回测引擎
│   │   ├── notification/              # 通知模块
│   │   │   └── email_sender.py        # 邮件发送
│   │   └── scheduler/                 # 定时任务
│   │       └── task_scheduler.py      # 任务调度器
│   │
│   ├── data/                          # 数据文件
│   │   └── csi300_stocks.json         # 沪深300成分股
│   ├── cache/                         # 数据缓存
│   ├── logs/                          # 日志文件
│   │   └── analysis/                  # 分析结果日志
│   └── scripts/                       # 脚本工具
│       └── generate_md_report.py      # 报告生成
│
├── 📄 文档文件
│   ├── 🆕 MINIPROGRAM_GUIDE.md        # 小程序开发部署指南 (新增)
│   ├── 🆕 README_MINIPROGRAM.md       # 小程序快速开始 (新增)
│   ├── 🆕 PROJECT_STRUCTURE.md        # 项目结构说明 (新增)
│   └── IFLOW.md                       # 原项目开发指南
│
├── 🚀 启动脚本
│   ├── 🆕 start_api_server.bat        # 启动API服务 (新增)
│   ├── start.bat                      # 启动实盘分析
│   └── start_daemon.bat               # 启动守护进程
│
└── ⚙️ 配置文件
    ├── .env                           # 环境变量 (邮箱配置)
    ├── .env.example                   # 环境变量示例
    └── .gitignore                     # Git忽略文件
```

---

## 🔄 数据流向

```
┌─────────────────────────────────────────────────────────────┐
│                     微信小程序用户界面                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ 今日推荐  │  │ 股票详情  │  │ 历史记录  │                   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                   │
└───────┼─────────────┼─────────────┼─────────────────────────┘
        │             │             │
        │   HTTPS     │   HTTPS     │   HTTPS
        │             │             │
        ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│              Flask API Server (api_server.py)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /api/stocks/recommend    推荐股票接口               │   │
│  │  /api/stocks/detail/:code 股票详情接口               │   │
│  │  /api/market/overview     市场概览接口               │   │
│  │  /api/analysis/history    历史记录接口               │   │
│  └────────────────────┬─────────────────────────────────┘   │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ 调用
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   核心分析引擎 (src/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ MarketAnalyzer│ │ StockFilter  │ │ DataFetcher  │      │
│  │  市场分析     │ │  股票筛选     │ │  数据获取     │      │
│  └──────────────┘  └──────────────┘  └──────┬───────┘      │
└────────────────────────────────────────────┼───────────────┘
                                              │
                                              │ 请求数据
                                              ▼
                                    ┌──────────────────┐
                                    │  腾讯财经API      │
                                    │  (实时股票数据)   │
                                    └──────────────────┘
```

---

## 📱 小程序页面功能

### 1. 今日推荐页 (index)

**路径**: `miniprogram/pages/index/`

**功能**:
- ✅ 显示市场概览 (总股票数、上涨、下跌、平均涨幅)
- ✅ 展示推荐股票列表
- ✅ 5维评分系统可视化
- ✅ 点击跳转详情页
- ✅ 下拉刷新

**API**: `GET /api/stocks/recommend`

---

### 2. 股票详情页 (detail)

**路径**: `miniprogram/pages/detail/`

**功能**:
- ✅ 实时价格、涨跌幅
- ✅ 今开、昨收、最高、最低
- ✅ 成交量、成交额、换手率
- ✅ PE、PB估值指标
- ✅ 刷新按钮

**API**: `GET /api/stocks/detail/:code`

---

### 3. 历史记录页 (history)

**路径**: `miniprogram/pages/history/`

**功能**:
- ✅ 显示30天分析记录
- ✅ 每日推荐股票数量
- ✅ 首推股票名称
- ✅ 下拉刷新

**API**: `GET /api/analysis/history`

---

## 🔧 后端API接口

### 接口列表

| 接口路径 | 方法 | 功能 | 返回数据 |
|---------|------|------|---------|
| `/api/health` | GET | 健康检查 | 服务状态 |
| `/api/stocks/recommend` | GET | 获取推荐股票 | 股票列表 + 市场概览 |
| `/api/stocks/detail/:code` | GET | 获取股票详情 | 单只股票详细数据 |
| `/api/market/overview` | GET | 获取市场概览 | 市场统计数据 |
| `/api/analysis/history?days=N` | GET | 获取历史分析 | N天历史记录 |

---

## 🗂️ 核心文件说明

### 新增文件 (微信小程序)

| 文件 | 说明 |
|------|------|
| `miniprogram/app.js` | 小程序入口,全局配置和HTTP请求封装 |
| `miniprogram/app.json` | 页面路由、导航栏、TabBar配置 |
| `miniprogram/app.wxss` | 全局样式(卡片、按钮、颜色等) |
| `miniprogram/pages/index/*` | 首页 - 今日推荐(4个文件) |
| `miniprogram/pages/detail/*` | 详情页 - 股票详情(4个文件) |
| `miniprogram/pages/history/*` | 历史页 - 分析记录(4个文件) |
| `miniprogram/project.config.json` | 微信开发者工具配置 |
| `stock_analyzer/api_server.py` | Flask API服务器 |
| `stock_analyzer/requirements_api.txt` | API服务依赖包 |
| `start_api_server.bat` | 快速启动API服务脚本 |

### 原有文件 (保持不变)

| 文件 | 说明 |
|------|------|
| `stock_analyzer/main.py` | 实盘分析主程序 |
| `stock_analyzer/src/analysis/market_analyzer.py` | 市场分析核心逻辑 |
| `stock_analyzer/src/data/data_fetcher.py` | 股票数据获取 |
| `stock_analyzer/config/config.py` | 系统配置 |

---

## 🎯 开发模式

### 模式1: 原有实盘分析 (不受影响)

```bash
# 守护进程模式 - 定时分析
python main.py --mode daemon

# 手动分析模式
python main.py --mode analysis

# 邮件发送模式
python main.py --mode email
```

### 模式2: 小程序API服务 (新增)

```bash
# 启动API服务器
python api_server.py

# 或使用脚本
start_api_server.bat

# 生产环境
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

**两种模式可以同时运行,互不干扰!**

---

## 📊 数据存储

### 缓存数据

- **位置**: `stock_analyzer/cache/`
- **内容**: 市场数据缓存,减少API请求
- **格式**: JSON

### 分析日志

- **位置**: `stock_analyzer/logs/analysis/`
- **命名**: `analysis_YYYYMMDD_HHMMSS.json`
- **内容**: 每日分析结果完整记录

### 成分股数据

- **位置**: `stock_analyzer/data/csi300_stocks.json`
- **内容**: 沪深300成分股列表
- **更新**: 手动运行 `update_csi300_stocks.py`

---

## 🔐 安全性说明

### 环境变量

- `.env` 文件存储敏感信息 (邮箱密码)
- **不要**提交到Git仓库
- 使用 `.env.example` 作为模板

### API安全

- 生产环境必须使用HTTPS
- 建议添加请求频率限制
- 考虑添加API密钥验证

---

## 📈 下一步扩展

### 功能扩展

- [ ] 用户登录和个人中心
- [ ] 自选股收藏功能
- [ ] 价格提醒推送
- [ ] K线图可视化
- [ ] 分享到朋友圈
- [ ] 订阅消息推送

### 技术优化

- [ ] Redis缓存加速
- [ ] 数据库持久化
- [ ] WebSocket实时推送
- [ ] CDN静态资源加速
- [ ] 接口限流和防刷

---

**详细开发指南**: [MINIPROGRAM_GUIDE.md](./MINIPROGRAM_GUIDE.md)
