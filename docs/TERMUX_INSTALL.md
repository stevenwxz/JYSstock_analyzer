# 📱 Termux 手机部署指南

## 1️⃣ 安装Termux

### 下载Termux
**重要**: 不要从Google Play下载(版本过旧),请从以下渠道下载:

- **推荐**: [F-Droid](https://f-droid.org/packages/com.termux/) (官方推荐)
- 备选: [GitHub Release](https://github.com/termux/termux-app/releases)

下载 `termux-app_vX.X.X+github-debug_arm64-v8a.apk` (根据手机CPU选择版本)

### 授予权限
安装后首次打开,需要授予存储权限:
```bash
termux-setup-storage
# 点击"允许"授予文件访问权限
```

---

## 2️⃣ 配置Termux环境

### 更新软件包
```bash
# 更新软件源
pkg update && pkg upgrade -y

# 安装基础工具
pkg install git python vim nano wget -y
```

### 配置Python环境
```bash
# 安装Python依赖
pip install --upgrade pip
pip install akshare pandas numpy requests

# 验证安装
python --version
pip list
```

---

## 3️⃣ 部署股票分析系统

### 方法A: 从GitHub克隆(如果有仓库)
```bash
# 克隆代码
git clone https://github.com/你的用户名/stock_analyzer.git
cd stock_analyzer
```

### 方法B: 手动上传代码
```bash
# 1. 在Termux中创建目录
mkdir -p ~/stock_analyzer
cd ~/stock_analyzer

# 2. 在电脑上将代码压缩成zip
# 3. 通过手机文件管理器将zip复制到 /storage/emulated/0/Download/
# 4. 在Termux中解压
cd ~
unzip ~/storage/downloads/stock_analyzer.zip -d ~/stock_analyzer/
```

### 方法C: 使用Python内置服务器传输(推荐)
**在电脑上(Windows):**
```bash
# 在stock_analyzer目录下运行
cd C:\Users\wxzfr\Desktop\jys\stock_analyzer
python -m http.server 8000
```

**在手机Termux上:**
```bash
# 获取电脑IP(假设是 192.168.1.100)
mkdir -p ~/stock_analyzer
cd ~/stock_analyzer

# 下载整个项目(需要逐个下载文件,或打包成tar)
# 建议先在电脑上打包:
# tar -czf stock_analyzer.tar.gz stock_analyzer/

# 然后在手机上下载:
wget http://192.168.1.100:8000/stock_analyzer.tar.gz
tar -xzf stock_analyzer.tar.gz
cd stock_analyzer
```

---

## 4️⃣ 运行分析

### 首次运行
```bash
cd ~/stock_analyzer

# 执行分析
python main.py --mode analysis
```

### 查看结果
```bash
# 查看生成的报告
ls reports/

# 用文本查看器打开最新报告
cat reports/$(ls -t reports/ | head -1)

# 或用手机浏览器查看
termux-open reports/$(ls -t reports/ | head -1)
```

---

## 5️⃣ 优化配置

### 创建快捷启动脚本
```bash
# 创建启动脚本
cat > ~/run_analysis.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

echo "开始股票分析..."
cd ~/stock_analyzer
python main.py --mode analysis

if [ $? -eq 0 ]; then
    echo ""
    echo "分析完成!"
    echo "报告位置: ~/stock_analyzer/reports/"

    # 自动打开最新报告
    latest_report=$(ls -t reports/*.md | head -1)
    echo "打开报告: $latest_report"
    termux-open "$latest_report"
else
    echo "分析失败,请查看日志"
fi
EOF

# 添加执行权限
chmod +x ~/run_analysis.sh
```

### 使用脚本运行
```bash
# 以后只需运行:
~/run_analysis.sh
```

### 创建桌面快捷方式(可选)
```bash
# 安装Termux:Widget(从F-Droid下载)
# 然后创建快捷方式:
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/股票分析 << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
~/run_analysis.sh
EOF

chmod +x ~/.shortcuts/股票分析
```

---

## 6️⃣ 定时自动运行(可选)

### 安装cronie(定时任务)
```bash
pkg install cronie -y

# 启动cron服务
crond

# 编辑定时任务
crontab -e
```

### 添加定时任务
在打开的编辑器中添加:
```cron
# 每个交易日16:30运行分析
30 16 * * 1-5 ~/run_analysis.sh

# 每天8:00运行(测试用)
0 8 * * * ~/run_analysis.sh
```

保存并退出(vim: 按ESC,输入:wq回车)

---

## 7️⃣ 常见问题

### Q1: pip安装依赖失败
```bash
# 换国内镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install akshare pandas numpy
```

### Q2: 没有存储权限
```bash
termux-setup-storage
# 重启Termux后重试
```

### Q3: akshare网络超时
```bash
# 设置更长的超时时间
export REQUESTS_TIMEOUT=30

# 或在代码中修改timeout参数
```

### Q4: 内存不足
```bash
# 清理缓存
pkg clean

# 限制并发数(修改配置文件)
# 在config.py中将max_concurrent从20改为5
```

### Q5: 后台运行
```bash
# 使用nohup后台运行
nohup ~/run_analysis.sh > ~/analysis.log 2>&1 &

# 查看日志
tail -f ~/analysis.log
```

---

## 8️⃣ 进阶功能

### 添加通知提醒
```bash
# 安装Termux:API(从F-Droid)
pkg install termux-api -y

# 在脚本末尾添加通知:
cat >> ~/run_analysis.sh << 'EOF'

# 发送通知
termux-notification --title "股票分析完成" \
    --content "今日推荐已生成,点击查看" \
    --button1 "查看报告" \
    --button1-action "termux-open ~/stock_analyzer/reports/$(ls -t ~/stock_analyzer/reports/*.md | head -1)"
EOF
```

### 分享报告到微信/QQ
```bash
# 使用termux-share命令
termux-share -a send ~/stock_analyzer/reports/$(ls -t ~/stock_analyzer/reports/*.md | head -1)
```

### 语音播报结果
```bash
# 安装termux-tts
pkg install termux-api -y

# 添加语音播报
termux-tts-speak "股票分析完成,共推荐10只股票"
```

---

## 9️⃣ 性能优化

### 减少内存占用
在 `main.py` 中添加:
```python
import gc

# 在分析完成后手动清理内存
gc.collect()
```

### 限制数据获取数量
修改配置文件,减少历史数据天数:
```python
# config.py
DATA_CONFIG = {
    'history_days': 20,  # 从60天改为20天
    'max_concurrent': 5   # 从20改为5
}
```

---

## 🎯 总结

**日常使用流程:**
1. 打开Termux
2. 运行 `~/run_analysis.sh`
3. 等待分析完成
4. 查看生成的报告

**优势:**
- ✅ 完全免费
- ✅ 数据本地存储,隐私安全
- ✅ 随时随地运行分析
- ✅ 可添加桌面快捷方式

**注意事项:**
- ⚠️ 运行时保持手机电量充足
- ⚠️ 首次运行会下载较多数据,建议使用WiFi
- ⚠️ 定期清理旧报告释放空间

---

**需要帮助?**
如遇到问题,可以查看日志文件:
```bash
cat ~/stock_analyzer/logs/stock_analyzer.log
```
