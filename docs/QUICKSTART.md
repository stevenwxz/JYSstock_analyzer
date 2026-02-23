# 🚀 快速开始 - 5分钟运行小程序

## ⚡ 一键启动 (最快)

### Windows用户

1. **启动后端API服务**
   ```bash
   双击运行: start_api_server.bat
   ```

2. **打开微信开发者工具**
   - 导入项目目录: `miniprogram/`
   - AppID: 使用测试号
   - 勾选"不校验合法域名"
   - 点击"编译"

**搞定!** 🎉 小程序已经在运行了!

---

## 📋 详细步骤

### 第一步: 安装依赖

```bash
cd stock_analyzer
pip install -r requirements_api.txt
```

**所需依赖**:
- Flask (Web框架)
- flask-cors (跨域)
- requests (HTTP请求)

### 第二步: 启动后端服务

**方法1: 使用脚本 (推荐)**
```bash
双击: start_api_server.bat
```

**方法2: 手动启动**
```bash
cd stock_analyzer
python api_server.py
```

**验证服务**:
浏览器访问: http://localhost:5000/api/health

应该看到:
```json
{
  "status": "ok",
  "timestamp": "2024-12-02T...",
  "service": "股票分析API服务"
}
```

### 第三步: 测试API (可选)

```bash
cd stock_analyzer
python test_api.py
```

应该看到所有测试通过 ✅

### 第四步: 运行小程序

1. **下载微信开发者工具**
   - https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html

2. **导入项目**
   - 打开微信开发者工具
   - 点击"导入项目"
   - 项目目录: `c:\Users\wxzfr\Desktop\jys\miniprogram`
   - AppID: 使用测试号 (或你的AppID)

3. **配置开发环境**
   - 点击右上角"详情"
   - 勾选"不校验合法域名、web-view、TLS版本以及HTTPS证书"

4. **运行**
   - 点击"编译"
   - 小程序界面出现!

---

## 📱 功能演示

### 1️⃣ 今日推荐页
- 查看推荐股票列表
- 5维评分系统
- 市场概览统计
- 下拉刷新数据

### 2️⃣ 股票详情页
- 点击任一股票
- 查看实时价格
- PE/PB估值指标
- 成交量和换手率

### 3️⃣ 历史记录页
- 切换到"历史记录"标签
- 查看30天分析记录

---

## 🔧 常见问题

### Q: 小程序显示"网络错误"

**解决方案**:
1. 检查后端服务是否启动
   ```bash
   # 浏览器访问
   http://localhost:5000/api/health
   ```

2. 检查是否勾选"不校验合法域名"
   - 开发者工具 -> 详情 -> 本地设置

3. 查看控制台错误信息

### Q: API返回空数据

**原因**: 可能是市场未开盘或数据获取失败

**解决方案**:
1. 查看后端日志输出
2. 检查网络连接
3. 确认数据源API可访问

### Q: 找不到图标

**解决方案**:
```bash
cd miniprogram/images
python create_icons.py
```

### Q: 真机调试无法访问

**解决方案**:
- 开发阶段: 使用电脑局域网IP (如 192.168.1.100)
- 修改 `miniprogram/app.js` 中的 `apiBaseUrl`
- 或部署到云服务器

---

## 📂 项目文件说明

```
jys/
├── start_api_server.bat          # 👈 双击启动API服务
├── miniprogram/                  # 👈 微信开发者工具导入此目录
│   ├── pages/                    # 小程序页面
│   ├── app.js                    # 入口文件
│   └── ...
└── stock_analyzer/
    ├── api_server.py             # Flask API服务器
    ├── test_api.py               # API测试脚本
    └── ...
```

---

## 📖 下一步

### 开发阶段
- [x] 启动本地服务 ✅
- [x] 运行小程序 ✅
- [ ] 修改页面样式
- [ ] 添加新功能
- [ ] 测试真机调试

### 上线准备
- [ ] 部署到云服务器
- [ ] 配置HTTPS域名
- [ ] 配置服务器域名白名单
- [ ] 提交小程序审核

**详细文档**: [MINIPROGRAM_GUIDE.md](./MINIPROGRAM_GUIDE.md)

---

## 🎯 API接口速查

| 接口 | 功能 |
|------|------|
| `GET /api/health` | 健康检查 |
| `GET /api/stocks/recommend` | 推荐股票 |
| `GET /api/stocks/detail/:code` | 股票详情 |
| `GET /api/market/overview` | 市场概览 |
| `GET /api/analysis/history` | 历史记录 |

**测试地址**: http://localhost:5000/api/

---

## 💡 提示

1. **开发阶段**: 确保后端服务一直运行
2. **真机调试**: 需要手机和电脑在同一WiFi
3. **数据更新**: 工作日16:00后数据最新
4. **性能优化**: 使用缓存减少请求

---

## 📞 获取帮助

- **详细开发指南**: [MINIPROGRAM_GUIDE.md](./MINIPROGRAM_GUIDE.md)
- **项目结构说明**: [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)
- **原项目文档**: [IFLOW.md](./IFLOW.md)
- **邮箱**: 1120311927@qq.com

---

**预祝开发顺利! 🚀**

有问题随时查看文档或联系我!
