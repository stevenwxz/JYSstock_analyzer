#!/bin/bash
# 项目清理脚本

echo "========================================"
echo "    🧹 项目清理工具"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 统计信息
total_freed=0

echo -e "${YELLOW}1. 清理备份文件...${NC}"
# 删除 .backup 文件
find . -name "*.backup" -type f -print -delete | while read file; do
    size=$(du -h "$file" 2>/dev/null | cut -f1)
    echo "  删除: $file ($size)"
done

echo ""
echo -e "${YELLOW}2. 检查报告文件(保留所有报告)...${NC}"
# 只统计,不删除报告
report_count=$(find stock_analyzer/reports -name "*.md" -type f 2>/dev/null | wc -l)
oldest_report=$(find stock_analyzer/reports -name "*.md" -type f 2>/dev/null | head -1)
newest_report=$(find stock_analyzer/reports -name "*.md" -type f 2>/dev/null | tail -1)
echo "  报告总数: $report_count 个"
echo "  所有报告均已保留,不执行删除"

echo ""
echo -e "${YELLOW}3. 清理Python缓存...${NC}"
# 删除 __pycache__
find . -type d -name "__pycache__" -print | while read dir; do
    echo "  删除: $dir"
    rm -rf "$dir"
done

# 删除 .pyc 文件
find . -name "*.pyc" -type f -print -delete | while read file; do
    echo "  删除: $file"
done

echo ""
echo -e "${YELLOW}4. 清理日志文件(保留最新3个)...${NC}"
# 只保留最新的3个日志
cd stock_analyzer/logs 2>/dev/null
if [ -f stock_analyzer.log ]; then
    ls -t *.log 2>/dev/null | tail -n +4 | while read log; do
        size=$(du -h "$log" | cut -f1)
        echo "  删除: logs/$log ($size)"
        rm "$log"
    done
fi
cd - > /dev/null

echo ""
echo -e "${YELLOW}5. 清理分析结果JSON(保留最新10个)...${NC}"
cd stock_analyzer/logs/analysis 2>/dev/null
if [ $? -eq 0 ]; then
    ls -t *.json 2>/dev/null | tail -n +11 | while read json; do
        size=$(du -h "$json" | cut -f1)
        echo "  删除: logs/analysis/$json ($size)"
        rm "$json"
    done
fi
cd - > /dev/null

echo ""
echo -e "${YELLOW}6. 清理临时打包文件...${NC}"
# 删除打包文件(可选)
for file in stock_analyzer_mobile.tar.gz stock_analyzer_mobile.zip; do
    if [ -f "$file" ]; then
        read -p "  删除 $file? (y/n): " choice
        if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
            size=$(du -h "$file" | cut -f1)
            echo "  删除: $file ($size)"
            rm "$file"
        fi
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}清理完成!${NC}"
echo -e "${GREEN}========================================${NC}"

# 显示当前磁盘使用情况
echo ""
echo "当前项目大小:"
du -sh . 2>/dev/null
echo ""
echo "报告数量: $(find stock_analyzer/reports -name "*.md" 2>/dev/null | wc -l) 个"
echo "日志数量: $(find stock_analyzer/logs -name "*.log" 2>/dev/null | wc -l) 个"
