import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    # 尝试导入模块
    from src.data.data_fetcher import StockDataFetcher
    print("模块导入成功")
except SyntaxError as e:
    print(f"语法错误: {e}")
    print(f"错误行号: {e.lineno}")
    # 读取文件并显示错误行附近的内容
    with open('src/data/data_fetcher.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        start = max(0, e.lineno - 5)
        end = min(len(lines), e.lineno + 5)
        print(f"\n错误行附近的内容 (行 {start+1}-{end}):")
        for i in range(start, end):
            print(f"{i+1:4d}: {lines[i].rstrip()}")
except Exception as e:
    print(f"其他错误: {e}")