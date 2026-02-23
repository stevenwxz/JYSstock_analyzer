# 📱 手机端快速开始指南

## ⚡ 5分钟快速部署

### 第一步: 打包代码(在电脑上)

双击运行: `pack_for_mobile.bat`

会生成: `stock_analyzer_mobile.zip`

---

### 第二步: 传输到手机

**推荐方式:**
1. 微信/QQ发送给自己(最简单)
2. USB线连接电脑传输
3. 百度网盘/阿里云盘

将文件保存到手机的"下载"文件夹

---

### 第三步: 安装Termux

1. 打开浏览器访问: https://f-droid.org/packages/com.termux/
2. 点击"Download APK"
3. 安装Termux

⚠️ **重要**: 不要从Google Play下载(版本过旧会有问题)

---

### 第四步: 在Termux中部署

打开Termux,复制粘贴以下命令:

```bash
# 1. 更新系统
pkg update && pkg upgrade -y

# 2. 安装必要工具
pkg install python git unzip -y

# 3. 授予存储权限
termux-setup-storage
```

点击"允许"授予权限

```bash
# 4. 解压项目
cd ~/storage/downloads
unzip stock_analyzer_mobile.zip -d ~/
cd ~/stock_analyzer

# 5. 安装Python依赖
pip install akshare pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 添加执行权限
chmod +x run_mobile.sh

# 7. 运行!
./run_mobile.sh
```

---

### 第五步: 使用

以后每次使用只需:

```bash
cd ~/stock_analyzer
./run_mobile.sh
```

选择"1"执行分析,等待完成即可!

---

## 🎯 创建桌面快捷方式(可选)

### 1. 安装Termux:Widget

从F-Droid下载安装: [Termux:Widget](https://f-droid.org/packages/com.termux.widget/)

### 2. 创建快捷方式

在Termux中执行:

```bash
# 创建快捷方式目录
mkdir -p ~/.shortcuts

# 创建快捷脚本
cat > ~/.shortcuts/股票分析 << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/stock_analyzer
./run_mobile.sh
EOF

# 添加执行权限
chmod +x ~/.shortcuts/股票分析
```

### 3. 添加到桌面

1. 长按手机桌面空白处
2. 选择"小部件/Widgets"
3. 找到"Termux:Widget"
4. 拖动到桌面
5. 点击"股票分析"快捷方式

---

## 📊 功能说明

### 菜单选项:

**1) 执行股票分析**
- 自动获取沪深300数据
- 运行量化分析
- 生成markdown报告
- 可选打开/分享报告

**2) 查看最新报告**
- 列出最近5份报告
- 可直接打开查看

**3) 发送邮件报告**
- 将报告发送到邮箱
- 需要先配置邮件

**4) 清理旧报告**
- 删除30天前的报告
- 释放存储空间

---

## 🔔 启用通知(可选)

### 安装Termux:API

1. 从F-Droid下载: [Termux:API](https://f-droid.org/packages/com.termux.api/)
2. 在Termux中安装API包:

```bash
pkg install termux-api -y
```

### 测试通知

```bash
termux-notification --title "测试" --content "通知功能正常"
```

启用后,分析完成会自动弹出通知!

---

## ⏰ 设置定时运行(可选)

### 安装cronie

```bash
pkg install cronie -y
crond
```

### 添加定时任务

```bash
crontab -e
```

添加以下内容(每个交易日16:30运行):

```cron
30 16 * * 1-5 cd ~/stock_analyzer && ./run_mobile.sh
```

保存退出: 按ESC,输入`:wq`,回车

---

## 💡 使用技巧

### 1. 后台运行

```bash
nohup ./run_mobile.sh > ~/analysis.log 2>&1 &
```

### 2. 查看日志

```bash
tail -f ~/stock_analyzer/logs/stock_analyzer.log
```

### 3. 分享报告

```bash
# 需要Termux:API
termux-share -a send ~/stock_analyzer/reports/最新报告.md
```

### 4. 快速清理

```bash
# 清理所有缓存和日志
cd ~/stock_analyzer
rm -rf logs/*.log
rm -rf reports/*.md
```

---

## ❓ 常见问题

### Q: pip安装慢/失败?

**A:** 使用国内镜像:

```bash
pip install akshare pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 内存不足?

**A:** 关闭其他应用,或修改配置:

```bash
# 编辑配置文件
nano ~/stock_analyzer/config/mobile_config.py

# 修改 max_concurrent 从5改为3
# 修改 history_days 从20改为10
```

### Q: 网络超时?

**A:** 检查网络,使用WiFi,或增加超时时间:

```bash
export REQUESTS_TIMEOUT=60
```

### Q: 怎么更新代码?

**A:** 重新打包传输,或使用git:

```bash
cd ~/stock_analyzer
git pull  # 如果是从git clone的
```

---

## 📈 性能优化建议

### 手机配置要求:
- **最低**: 2GB内存 + Android 7.0
- **推荐**: 4GB内存 + Android 10.0
- **最佳**: 6GB内存 + Android 12.0

### 优化建议:
1. 运行前关闭其他应用
2. 连接WiFi(数据量较大)
3. 保持手机电量>50%
4. 定期清理旧报告

---

## 🎉 完成!

现在你可以:
- ✅ 在手机上随时运行股票分析
- ✅ 查看精美的分析报告
- ✅ 分享结果到微信/QQ
- ✅ 设置定时自动分析

**祝投资顺利! 📈**

---

**更多帮助?**
- 详细文档: TERMUX_INSTALL.md
- 问题反馈: [GitHub Issues]
