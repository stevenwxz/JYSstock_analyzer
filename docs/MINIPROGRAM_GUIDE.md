# 📱 微信小程序开发部署指南

## 项目概述

本项目已改造为**前后端分离架构**的微信小程序:

```
项目结构:
├── stock_analyzer/          # 后端服务(Python)
│   ├── api_server.py        # Flask API服务器
│   ├── src/                 # 核心分析引擎
│   └── ...
└── miniprogram/             # 微信小程序前端
    ├── pages/               # 页面文件
    ├── app.js               # 小程序入口
    └── ...
```

---

## 一、后端API服务部署

### 1.1 安装依赖

```bash
cd stock_analyzer
pip install -r requirements_api.txt
```

### 1.2 启动开发服务器

```bash
# 在 stock_analyzer 目录下
python api_server.py
```

服务将在 `http://localhost:5000` 启动

### 1.3 API接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/stocks/recommend` | GET | 获取推荐股票列表 |
| `/api/stocks/detail/:code` | GET | 获取股票详情 |
| `/api/market/overview` | GET | 获取市场概览 |
| `/api/analysis/history` | GET | 获取历史分析记录 |

### 1.4 生产环境部署

#### 使用 Gunicorn (推荐)

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务(4个worker进程)
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

#### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 配置HTTPS (必需!)

**重要**: 微信小程序要求后端API必须使用HTTPS协议!

1. 申请SSL证书(推荐免费证书: Let's Encrypt, 阿里云, 腾讯云)
2. 配置Nginx SSL:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 二、微信小程序前端开发

### 2.1 开发环境准备

1. **下载微信开发者工具**
   - 访问: https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
   - 下载并安装微信开发者工具

2. **注册小程序账号**
   - 访问: https://mp.weixin.qq.com
   - 注册小程序账号,获取 AppID

### 2.2 导入项目

1. 打开微信开发者工具
2. 点击 "导入项目"
3. 选择项目目录: `miniprogram/`
4. 填入你的 AppID (测试可以使用测试号)
5. 项目名称: 智能选股助手

### 2.3 配置API地址

编辑 `miniprogram/app.js` 文件:

```javascript
App({
  globalData: {
    // 开发环境 - 本地调试
    // apiBaseUrl: 'http://localhost:5000/api',

    // 生产环境 - 修改为你的服务器地址(必须HTTPS!)
    apiBaseUrl: 'https://your-domain.com/api',
  }
})
```

### 2.4 配置服务器域名白名单

在微信公众平台 (mp.weixin.qq.com):

1. 登录小程序后台
2. 开发 -> 开发管理 -> 开发设置
3. 服务器域名 -> request合法域名
4. 添加你的API服务器域名: `https://your-domain.com`

**注意**:
- 必须是HTTPS域名
- 域名需要备案
- 开发阶段可以在开发者工具中勾选"不校验合法域名"

### 2.5 本地调试

1. 在微信开发者工具中打开项目
2. 点击右上角"详情" -> "本地设置"
3. 勾选 "不校验合法域名、web-view(业务域名)、TLS版本以及HTTPS证书"
4. 确保后端API服务已启动 (`python api_server.py`)
5. 点击"编译"运行小程序

---

## 三、小程序页面说明

### 3.1 首页 - 今日推荐 (pages/index)

**功能**:
- 显示当日推荐的强势股票
- 市场概览统计
- 股票综合评分和分项得分
- 点击查看股票详情

**数据来源**: `GET /api/stocks/recommend`

### 3.2 股票详情页 (pages/detail)

**功能**:
- 显示股票实时价格
- 成交量、换手率等交易数据
- PE、PB等估值指标
- 刷新数据功能

**数据来源**: `GET /api/stocks/detail/:code`

### 3.3 历史记录页 (pages/history)

**功能**:
- 查看过往30天的分析记录
- 每日推荐股票数量
- 首推股票名称

**数据来源**: `GET /api/analysis/history`

---

## 四、开发流程

### 4.1 日常开发

```bash
# 1. 启动后端API服务
cd stock_analyzer
python api_server.py

# 2. 打开微信开发者工具
# 导入 miniprogram 目录
# 开始开发和调试
```

### 4.2 添加新功能

1. **后端**: 在 `api_server.py` 添加新的API接口
2. **前端**:
   - 在 `pages/` 目录创建新页面
   - 在 `app.json` 中注册页面路径
   - 使用 `app.request()` 调用API

### 4.3 代码提交

```bash
git add .
git commit -m "feat: 添加xxx功能"
git push
```

---

## 五、发布上线

### 5.1 后端部署检查清单

- [ ] 部署到云服务器(阿里云、腾讯云等)
- [ ] 配置域名和DNS解析
- [ ] 配置HTTPS证书(必需!)
- [ ] 使用 Gunicorn + Nginx 部署
- [ ] 配置防火墙和安全组
- [ ] 设置定时任务(每日16:00执行分析)
- [ ] 配置日志轮转

### 5.2 小程序发布流程

1. **代码审核前准备**
   - 修改 `app.js` 中的 `apiBaseUrl` 为生产环境地址
   - 在小程序后台配置服务器域名白名单
   - 准备小程序icon图标(建议找设计师设计)

2. **上传代码**
   - 在微信开发者工具中点击"上传"
   - 填写版本号和项目备注
   - 上传成功后代码进入"开发管理"

3. **提交审核**
   - 登录小程序后台 mp.weixin.qq.com
   - 版本管理 -> 开发版本 -> 提交审核
   - 填写审核信息(功能介绍、测试账号等)

4. **发布上线**
   - 审核通过后,点击"发布"
   - 小程序正式上线,用户可搜索使用

---

## 六、运维监控

### 6.1 日志管理

后端日志位置:
- API访问日志: 使用 `logging` 模块记录
- 分析结果日志: `stock_analyzer/logs/analysis/`

### 6.2 性能监控

```bash
# 查看API服务状态
ps aux | grep api_server

# 查看端口占用
netstat -tuln | grep 5000

# 查看日志
tail -f /path/to/log/file
```

### 6.3 定时任务

使用 crontab 设置每日16:00执行分析:

```bash
crontab -e

# 添加以下内容
0 16 * * 1-5 cd /path/to/stock_analyzer && python main.py --mode analysis
```

---

## 七、常见问题

### Q1: 小程序无法请求API,提示"不在以下request合法域名列表中"

**解决方案**:
- 开发阶段: 开发者工具勾选"不校验合法域名"
- 生产环境: 在小程序后台配置服务器域名白名单

### Q2: API请求返回错误

**检查步骤**:
1. 确认后端服务是否启动
2. 检查网络连接
3. 查看浏览器/控制台错误信息
4. 检查API地址是否正确

### Q3: 小程序真机调试无法访问localhost

**解决方案**:
- 使用同一局域网内的电脑IP地址,如 `http://192.168.1.100:5000/api`
- 或部署到云服务器使用公网地址

### Q4: 数据加载慢

**优化建议**:
- 启用缓存机制
- 优化API响应时间
- 使用CDN加速
- 减少不必要的数据字段

---

## 八、技术栈

### 后端
- Python 3.8+
- Flask 2.3.0 (Web框架)
- flask-cors (跨域支持)
- Gunicorn (生产服务器)

### 前端
- 微信小程序原生框架
- WXML + WXSS + JavaScript

### 数据源
- 腾讯财经API (实时股票数据)

---

## 九、下一步优化方向

- [ ] 添加用户收藏功能
- [ ] 实现股票价格提醒
- [ ] 添加K线图展示
- [ ] 支持自选股管理
- [ ] 添加策略回测结果展示
- [ ] 接入更多数据源
- [ ] 添加用户反馈系统
- [ ] 实现消息推送(模板消息)

---

## 十、联系方式

如有问题请联系:
- 邮箱: 1120311927@qq.com
- 项目地址: [GitHub仓库地址]

---

**祝你开发顺利! 🚀**
