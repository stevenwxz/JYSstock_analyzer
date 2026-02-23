# 📱 沪深300智能选股小程序

> 基于量化策略的A股智能选股系统 - 微信小程序版

## 🚀 快速开始

### 第一步: 启动后端API服务

```bash
# Windows用户双击运行
start_api_server.bat

# 或手动启动
cd stock_analyzer
python api_server.py
```

服务启动后访问: http://localhost:5000/api/health 验证

### 第二步: 运行微信小程序

1. 下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开微信开发者工具,选择"导入项目"
3. 项目目录选择: `miniprogram/`
4. AppID: 使用测试号或你的小程序AppID
5. 点击"编译"运行

**提示**: 首次运行需要在开发者工具中勾选"不校验合法域名"

## 📂 项目结构

```
jys/
├── stock_analyzer/              # 后端Python服务
│   ├── api_server.py            # ✨ Flask API服务器(新增)
│   ├── requirements_api.txt     # ✨ API依赖(新增)
│   ├── main.py                  # 原有实盘分析入口
│   ├── src/                     # 核心分析引擎
│   └── ...
├── miniprogram/                 # ✨ 微信小程序前端(新增)
│   ├── pages/
│   │   ├── index/               # 今日推荐页
│   │   ├── detail/              # 股票详情页
│   │   └── history/             # 历史记录页
│   ├── app.js                   # 小程序入口
│   ├── app.json                 # 小程序配置
│   └── ...
├── MINIPROGRAM_GUIDE.md         # ✨ 详细开发部署指南(新增)
└── start_api_server.bat         # ✨ 快速启动脚本(新增)
```

## 🎯 小程序功能

### 📊 今日推荐
- 显示当日量化筛选的强势股票
- 5维评分系统(技术面、估值、盈利、安全性、股息)
- 市场概览统计
- 支持下拉刷新

### 📈 股票详情
- 实时价格和涨跌幅
- 成交量、换手率
- PE、PB估值指标
- 一键刷新数据

### 📅 历史记录
- 查看过往30天分析记录
- 每日推荐股票数量统计

## 🔧 技术架构

### 后端
- **框架**: Flask 2.3.0
- **语言**: Python 3.8+
- **数据源**: 腾讯财经API

### 前端
- **平台**: 微信小程序
- **语言**: WXML, WXSS, JavaScript

## 📡 API接口

| 接口 | 说明 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/stocks/recommend` | 获取推荐股票 |
| `GET /api/stocks/detail/:code` | 股票详情 |
| `GET /api/market/overview` | 市场概览 |
| `GET /api/analysis/history` | 历史记录 |

## 📦 依赖安装

```bash
cd stock_analyzer
pip install -r requirements_api.txt
```

主要依赖:
- Flask (Web框架)
- flask-cors (跨域支持)
- requests (HTTP请求)
- gunicorn (生产部署)

## 🌐 生产环境部署

### 后端部署要点

1. **使用HTTPS** (微信小程序强制要求)
2. **域名备案** (国内服务器必需)
3. **配置Nginx反向代理**
4. **使用Gunicorn启动**

```bash
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### 小程序发布要点

1. 修改 `miniprogram/app.js` 中的API地址为生产环境
2. 在小程序后台配置服务器域名白名单
3. 上传代码并提交审核

**详细步骤请查看**: [MINIPROGRAM_GUIDE.md](./MINIPROGRAM_GUIDE.md)

## 🔍 开发调试

### 调试后端API

```bash
# 测试健康检查
curl http://localhost:5000/api/health

# 测试推荐股票接口
curl http://localhost:5000/api/stocks/recommend
```

### 调试小程序

1. 确保后端服务已启动
2. 在微信开发者工具中打开项目
3. 勾选"不校验合法域名"
4. 查看控制台日志

## 📖 详细文档

完整的开发和部署文档请查看:
- [MINIPROGRAM_GUIDE.md](./MINIPROGRAM_GUIDE.md) - 微信小程序完整开发指南
- [IFLOW.md](./IFLOW.md) - 原项目开发指南

## 🎨 截图预览

### 小程序界面
- **首页**: 今日推荐股票列表,5维评分展示
- **详情页**: 股票实时数据、估值指标
- **历史页**: 30天分析记录查询

## ⚙️ 配置说明

### API服务器配置

编辑 `stock_analyzer/api_server.py`:

```python
if __name__ == '__main__':
    # 开发环境
    app.run(host='0.0.0.0', port=5000, debug=True)

    # 生产环境(使用gunicorn)
    # gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

### 小程序API地址配置

编辑 `miniprogram/app.js`:

```javascript
globalData: {
  // 开发环境
  apiBaseUrl: 'http://localhost:5000/api',

  // 生产环境(必须HTTPS!)
  // apiBaseUrl: 'https://your-domain.com/api',
}
```

## 🐛 常见问题

### 1. 小程序无法请求数据
- 检查后端服务是否启动
- 开发阶段勾选"不校验合法域名"
- 生产环境配置服务器域名白名单

### 2. API返回500错误
- 查看后端日志
- 检查Python依赖是否安装完整
- 确认数据源API可访问

### 3. 真机调试无法访问localhost
- 使用局域网IP地址 (如 192.168.1.100)
- 或部署到云服务器使用公网地址

## 🚧 后续优化计划

- [ ] 添加用户收藏功能
- [ ] 实现价格提醒推送
- [ ] K线图可视化
- [ ] 自选股管理
- [ ] 策略回测展示
- [ ] 消息模板推送

## 📞 联系方式

- 邮箱: 1120311927@qq.com
- 问题反馈: [提交Issue]

## 📄 开源协议

MIT License

---

**祝你使用愉快! 如有问题请查看 [详细开发指南](./MINIPROGRAM_GUIDE.md) 📚**
