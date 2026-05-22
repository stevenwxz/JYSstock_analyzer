# 邮件功能配置指南

## 配置步骤

### 1. 设置环境变量
编辑 `.env` 文件，填入您的邮箱信息：

```
EMAIL_ADDRESS=your_qq_email@qq.com
EMAIL_PASSWORD=your_smtp_auth_code
TO_EMAIL=your_receiver_email@example.com
```

### 2. 获取QQ邮箱SMTP授权码
1. 登录QQ邮箱
2. 点击右上角的"设置"
3. 选择"账户"选项卡
4. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
5. 开启"IMAP/SMTP服务"，获取授权码

**注意**: `EMAIL_PASSWORD` 填写的是SMTP授权码，不是您的邮箱登录密码！

### 3. 验证配置
运行测试脚本验证配置：

```bash
cd stock_analyzer
python test_email.py
```

如果收到测试邮件，说明配置成功。

## 使用方式

### 1. 手动发送邮件
```bash
python main.py --mode email
```

### 2. 定时发送邮件（守护进程模式）
```bash
python main.py --mode daemon
```

在守护进程模式下，系统将在每天16:30自动发送股票分析报告。

### 3. 测试邮件功能
```bash
python test_email.py
```

## 注意事项

1. **安全提醒**: .env 文件包含敏感信息，请不要将此文件上传到公开的代码仓库
2. **授权码安全**: SMTP授权码具有发送邮件的权限，请妥善保管
3. **收件人设置**: 可以设置多个收件人，用逗号分隔：`email1@example.com,email2@example.com`
4. **邮件内容**: 邮件将包含详细的股票分析报告，包含表格、图表和投资建议

## 常见问题

**Q: 邮件发送失败**
A: 请检查SMTP授权码是否正确，以及是否开启了IMAP/SMTP服务

**Q: 收不到邮件**
A: 请检查收件人邮箱地址是否正确，以及邮件是否被误判为垃圾邮件

**Q: 如何查看发送记录**
A: 发送日志保存在 `./logs/` 目录下