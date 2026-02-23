@echo off
chcp 65001 >nul
echo ========================================
echo    📱 打包股票分析系统 - 手机版
echo ========================================
echo.

cd /d "%~dp0"

:: 检查7z是否安装
where 7z >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 提示: 未检测到7z,将使用tar打包
    echo 建议安装7z获得更小的压缩包
    echo.
    goto :use_tar
)

:use_7z
echo 使用7z打包...
echo.

:: 创建临时目录
if exist temp_pack rmdir /s /q temp_pack
mkdir temp_pack
mkdir temp_pack\stock_analyzer

:: 复制必要文件
echo 复制文件...
xcopy stock_analyzer\*.py temp_pack\stock_analyzer\ /s /e /y >nul
xcopy stock_analyzer\config temp_pack\stock_analyzer\config\ /s /e /y >nul
xcopy stock_analyzer\src temp_pack\stock_analyzer\src\ /s /e /y >nul
xcopy stock_analyzer\data temp_pack\stock_analyzer\data\ /s /e /y >nul
copy stock_analyzer\run_mobile.sh temp_pack\stock_analyzer\ >nul
copy TERMUX_INSTALL.md temp_pack\ >nul

:: 创建目录
mkdir temp_pack\stock_analyzer\logs
mkdir temp_pack\stock_analyzer\reports

:: 打包
echo 正在压缩...
7z a -tzip stock_analyzer_mobile.zip temp_pack\* >nul

:: 清理
rmdir /s /q temp_pack

echo.
echo ✓ 打包完成: stock_analyzer_mobile.zip
echo.
goto :instructions

:use_tar
echo 使用tar打包...
echo.

:: 使用tar打包(需要Windows 10+)
tar -czf stock_analyzer_mobile.tar.gz ^
    stock_analyzer\*.py ^
    stock_analyzer\config ^
    stock_analyzer\src ^
    stock_analyzer\data ^
    stock_analyzer\run_mobile.sh ^
    TERMUX_INSTALL.md

echo.
echo ✓ 打包完成: stock_analyzer_mobile.tar.gz
echo.

:instructions
echo ========================================
echo    📲 手机端部署步骤
echo ========================================
echo.
echo 1. 将压缩包传输到手机
echo    方式1: 通过微信/QQ发送给自己
echo    方式2: 连接USB线传输
echo    方式3: 使用在线网盘(百度云/阿里云)
echo.
echo 2. 在手机上安装Termux
echo    - 从F-Droid下载: https://f-droid.org/packages/com.termux/
echo    - 不要从Google Play下载(版本过旧)
echo.
echo 3. 在Termux中执行:
echo    pkg update ^&^& pkg upgrade -y
echo    pkg install python git unzip -y
echo    termux-setup-storage
echo.
echo 4. 解压并运行:
echo    cd ~/storage/downloads
echo    unzip stock_analyzer_mobile.zip -d ~/
echo    cd ~/stock_analyzer
echo    chmod +x run_mobile.sh
echo    ./run_mobile.sh
echo.
echo 详细说明请查看: TERMUX_INSTALL.md
echo ========================================
echo.

pause
