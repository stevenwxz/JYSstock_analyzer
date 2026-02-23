@echo off
chcp 65001
echo ====================================
echo 启动股票分析API服务器
echo ====================================
echo.

cd stock_analyzer

echo 正在启动Flask API服务...
echo 访问地址: http://localhost:5000
echo API文档:
echo   - GET  /api/health              健康检查
echo   - GET  /api/stocks/recommend    获取推荐股票
echo   - GET  /api/stocks/detail/:code 获取股票详情
echo   - GET  /api/market/overview     获取市场概览
echo   - GET  /api/analysis/history    获取历史分析
echo.
echo 按 Ctrl+C 停止服务
echo ====================================
echo.

python api_server.py

pause
