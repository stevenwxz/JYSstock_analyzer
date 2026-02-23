#!/data/data/com.termux/files/usr/bin/bash
# 手机端股票分析快捷脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    📱 股票量化分析系统 (手机版)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: 未安装Python${NC}"
    echo "请运行: pkg install python"
    exit 1
fi

# 检查依赖
echo -e "${YELLOW}检查依赖包...${NC}"
python -c "import akshare, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}正在安装依赖包...${NC}"
    pip install akshare pandas numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

# 显示菜单
echo ""
echo "请选择操作:"
echo "1) 执行股票分析"
echo "2) 查看最新报告"
echo "3) 发送邮件报告"
echo "4) 清理旧报告"
echo "5) 退出"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo -e "${GREEN}开始执行股票分析...${NC}"
        python main.py --mode analysis

        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✓ 分析完成!${NC}"

            # 查找最新报告
            latest_report=$(ls -t reports/*.md 2>/dev/null | head -1)
            if [ -n "$latest_report" ]; then
                echo -e "${GREEN}报告已生成: $latest_report${NC}"

                # 询问是否打开
                read -p "是否打开报告? (y/n): " open_choice
                if [ "$open_choice" = "y" ] || [ "$open_choice" = "Y" ]; then
                    if command -v termux-open &> /dev/null; then
                        termux-open "$latest_report"
                    else
                        echo "提示: 安装Termux:API可以直接打开报告"
                        echo "报告位置: $latest_report"
                    fi
                fi

                # 询问是否分享
                read -p "是否分享报告到其他应用? (y/n): " share_choice
                if [ "$share_choice" = "y" ] || [ "$share_choice" = "Y" ]; then
                    if command -v termux-share &> /dev/null; then
                        termux-share -a send "$latest_report"
                    else
                        echo "提示: 安装Termux:API可以分享文件"
                    fi
                fi
            fi
        else
            echo -e "${RED}✗ 分析失败，请查看日志${NC}"
            tail -20 logs/stock_analyzer.log
        fi
        ;;

    2)
        echo -e "${GREEN}最近的报告:${NC}"
        ls -lth reports/*.md 2>/dev/null | head -5
        echo ""

        latest_report=$(ls -t reports/*.md 2>/dev/null | head -1)
        if [ -n "$latest_report" ]; then
            read -p "是否打开最新报告? (y/n): " open_choice
            if [ "$open_choice" = "y" ] || [ "$open_choice" = "Y" ]; then
                if command -v termux-open &> /dev/null; then
                    termux-open "$latest_report"
                else
                    cat "$latest_report" | less
                fi
            fi
        else
            echo "没有找到报告文件"
        fi
        ;;

    3)
        echo -e "${GREEN}发送邮件报告...${NC}"
        python main.py --mode email
        ;;

    4)
        echo -e "${YELLOW}清理30天前的旧报告...${NC}"
        find reports/ -name "*.md" -mtime +30 -delete
        echo -e "${GREEN}清理完成${NC}"
        ;;

    5)
        echo "再见!"
        exit 0
        ;;

    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}操作完成!${NC}"
