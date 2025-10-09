@echo off
chcp 65001
echo =======================================
echo    股票量化分析系统
echo =======================================
echo.
echo 请选择运行模式：
echo 1. 守护进程模式（自动运行）
echo 2. 手动分析模式
echo 3. 发送邮件模式
echo 4. 测试模式
echo 5. 退出
echo.
set /p choice=请输入选择 (1-5):

if "%choice%"=="1" (
    echo 启动守护进程模式...
    python main.py --mode daemon
) else if "%choice%"=="2" (
    echo 执行手动分析...
    python main.py --mode analysis
    pause
) else if "%choice%"=="3" (
    echo 发送邮件...
    python main.py --mode email
    pause
) else if "%choice%"=="4" (
    echo 运行测试...
    python main.py --mode test
    pause
) else if "%choice%"=="5" (
    echo 退出程序
    exit
) else (
    echo 无效选择，请重新运行
    pause
)

goto :eof