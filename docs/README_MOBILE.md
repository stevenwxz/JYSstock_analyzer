# 📱 股票量化分析系统 - 手机版部署指南

## ✅ 已完成准备工作

你现在有以下文件:

- ✅ `stock_analyzer_mobile.tar.gz` - 打包好的项目(53KB)
- ✅ `MOBILE_QUICKSTART.md` - 5分钟快速开始指南
- ✅ `TERMUX_INSTALL.md` - 详细安装教程
- ✅ `stock_analyzer/run_mobile.sh` - 手机端运行脚本
- ✅ `stock_analyzer/config/mobile_config.py` - 手机优化配置

---

## 🚀 快速部署(3步搞定)

### 1️⃣ 传输文件到手机

**方式1: 微信发送(最简单)**
```
将 stock_analyzer_mobile.tar.gz 通过微信发给自己
在手机上下载保存
```

**方式2: USB传输**
```
连接手机USB线
复制到手机/Download文件夹
```

---

### 2️⃣ 在手机上安装Termux

1. 浏览器打开: https://f-droid.org/packages/com.termux/
2. 下载并安装Termux
3. ⚠️ 不要从Google Play下载(版本过旧)

---

### 3️⃣ 在Termux中运行

复制粘贴以下命令(一次性执行):

```bash
# 安装工具
pkg update && pkg upgrade -y && pkg install python unzip -y

# 授予权限
termux-setup-storage

# 解压项目
cd ~/storage/downloads
tar -xzf stock_analyzer_mobile.tar.gz -C ~/
cd ~/stock_analyzer

# 安装依赖
pip install akshare pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行分析
chmod +x run_mobile.sh
./run_mobile.sh
```

选择"1"开始分析!

---

## 📊 功能特性

✅ **完全免费** - 无需云服务器
✅ **数据本地** - 隐私安全
✅ **随时运行** - 不受时间限制
✅ **智能推荐** - Top 10股票精选
✅ **多维评分** - 技术面+估值+盈利+安全+股息
✅ **自动通知** - 分析完成提醒(需Termux:API)
✅ **报告分享** - 一键分享到微信/QQ

---

## 🎯 日常使用

每次使用只需2步:

```bash
# 1. 打开Termux
# 2. 运行脚本
cd ~/stock_analyzer
./run_mobile.sh
```

或添加桌面快捷方式,一键启动!

---

## 📚 文档说明

| 文档 | 说明 |
|------|------|
| **MOBILE_QUICKSTART.md** | ⚡ 5分钟快速开始(推荐新手) |
| **TERMUX_INSTALL.md** | 📖 详细安装配置教程 |
| **run_mobile.sh** | 🎮 交互式运行脚本 |
| **mobile_config.py** | ⚙️ 手机优化配置 |

---

## 💡 高级功能

### 🔔 开启通知

```bash
# 1. 安装Termux:API (从F-Droid)
# 2. 安装API包
pkg install termux-api -y

# 3. 测试通知
termux-notification --title "测试" --content "通知正常"
```

### ⏰ 定时自动运行

```bash
# 安装定时任务
pkg install cronie -y
crond

# 编辑定时任务
crontab -e

# 添加:每个交易日16:30运行
30 16 * * 1-5 cd ~/stock_analyzer && ./run_mobile.sh
```

### 🎨 桌面快捷方式

```bash
# 1. 安装Termux:Widget (从F-Droid)
# 2. 创建快捷方式
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/股票分析 << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/stock_analyzer && ./run_mobile.sh
EOF
chmod +x ~/.shortcuts/股票分析

# 3. 长按桌面 -> 小部件 -> Termux:Widget
```

---

## 🔧 性能优化

### 手机配置要求

| 配置等级 | 内存 | Android版本 | 运行速度 |
|---------|------|-------------|----------|
| 最低 | 2GB | 7.0+ | ~5分钟 |
| 推荐 | 4GB | 10.0+ | ~3分钟 |
| 最佳 | 6GB+ | 12.0+ | ~2分钟 |

### 优化建议

✅ 运行前关闭其他应用
✅ 连接WiFi(数据量~20MB)
✅ 保持电量>50%
✅ 定期清理旧报告(30天)

---

## ❓ 常见问题

### Q: 安装依赖失败?
```bash
# 使用国内镜像
pip install akshare pandas numpy -i https://mirrors.aliyun.com/pypi/simple/
```

### Q: 内存不足?
```bash
# 减少并发数和历史数据
nano ~/stock_analyzer/config/mobile_config.py
# max_concurrent: 5 → 3
# history_days: 20 → 10
```

### Q: 网络超时?
```bash
# 增加超时时间
export REQUESTS_TIMEOUT=60
```

### Q: 如何更新?
```bash
# 重新下载新的tar.gz
# 解压覆盖
cd ~/storage/downloads
tar -xzf stock_analyzer_mobile.tar.gz -C ~/ --overwrite
```

---

## 📈 数据说明

### 分析内容
- 沪深300成分股(300只)
- 多维度评分系统
- 技术面分析(20日动量)
- 估值分析(PE/PB)
- 盈利能力(ROE)
- 安全性评估
- 股息率分析

### 推荐标准
- PE ≤ 30
- 成交额 ≥ 5000万
- 强势评分 ≥ 40
- Top 10精选

---

## 🎉 开始使用

1. ✅ 文件已打包: `stock_analyzer_mobile.tar.gz`
2. ✅ 查看快速开始: `MOBILE_QUICKSTART.md`
3. ✅ 传输到手机并安装Termux
4. ✅ 运行命令开始分析!

**祝你投资顺利! 📊📈**

---

## 📞 技术支持

遇到问题?

1. 查看详细文档: `TERMUX_INSTALL.md`
2. 查看日志: `~/stock_analyzer/logs/stock_analyzer.log`
3. 检查配置: `~/stock_analyzer/config/`

---

**版本**: v3.0 (移动端优化版)
**更新**: 2025-12-13
**平台**: Termux (Android 7.0+)
