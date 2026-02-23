@echo off
echo ====================================
echo 配置Windows防火墙允许端口5000
echo ====================================
echo.

netsh advfirewall firewall add rule name="Allow Flask API Port 5000" dir=in action=allow protocol=TCP localport=5000

echo.
echo 防火墙规则添加成功!
echo 端口5000现在允许入站连接
echo.
pause
