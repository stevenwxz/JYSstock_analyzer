#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess

def check_python_version():
    """检查Python版本"""
    print("📋 检查Python版本...")
    version = sys.version_info
    print(f"   当前版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python版本过低，需要3.8或更高版本")
        return False
    else:
        print("   ✅ Python版本符合要求")
        return True

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")

    required_packages = [
        'yfinance', 'akshare', 'pandas', 'numpy',
        'requests', 'schedule', 'python-dotenv',
        'openpyxl', 'matplotlib', 'seaborn'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (未安装)")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n需要安装的包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    else:
        print("   ✅ 所有依赖包已安装")
        return True

def check_config():
    """检查配置文件"""
    print("\n⚙️ 检查配置文件...")

    # 检查.env文件
    if os.path.exists('.env'):
        print("   ✅ .env 配置文件存在")

        # 检查关键配置项
        try:
            from dotenv import load_dotenv
            load_dotenv()

            email = os.getenv('EMAIL_ADDRESS')
            password = os.getenv('EMAIL_PASSWORD')

            if email and password:
                print("   ✅ 邮箱配置已设置")
                return True
            else:
                print("   ❌ 邮箱配置不完整")
                print("   请在.env文件中设置EMAIL_ADDRESS和EMAIL_PASSWORD")
                return False

        except Exception as e:
            print(f"   ❌ 配置文件读取错误: {e}")
            return False
    else:
        print("   ❌ .env 配置文件不存在")
        print("   请复制.env.example为.env并填入配置")
        return False

def check_directories():
    """检查目录结构"""
    print("\n📁 检查目录结构...")

    required_dirs = ['src', 'config', 'logs', 'tests']

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ (不存在)")
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"   ✅ {dir_name}/ (已创建)")
            except Exception as e:
                print(f"   ❌ 创建 {dir_name}/ 失败: {e}")
                return False

    return True

def test_data_connection():
    """测试数据连接"""
    print("\n🌐 测试数据连接...")

    try:
        import akshare as ak
        # 尝试获取简单的市场数据
        data = ak.tool_trade_date_hist_sina()
        if not data.empty:
            print("   ✅ akshare数据连接正常")
            return True
        else:
            print("   ❌ akshare数据获取失败")
            return False
    except Exception as e:
        print(f"   ❌ 数据连接测试失败: {e}")
        return False

def main():
    """主检查函数"""
    print("=" * 50)
    print("   股票量化分析系统 - 安装检查")
    print("=" * 50)

    checks = [
        check_python_version(),
        check_dependencies(),
        check_config(),
        check_directories(),
        test_data_connection()
    ]

    print("\n" + "=" * 50)
    print("📊 检查结果汇总")
    print("=" * 50)

    passed = sum(checks)
    total = len(checks)

    if passed == total:
        print("🎉 所有检查通过！系统可以正常运行")
        print("\n🚀 可以运行以下命令启动系统:")
        print("   python main.py --mode daemon    # 守护进程模式")
        print("   python main.py --mode test      # 测试模式")
        print("   python start.bat                # Windows快速启动")
    else:
        print(f"❌ {total - passed} 项检查未通过，请解决后重新检查")

    print("\n如需帮助，请查看 使用说明.md 文件")

if __name__ == '__main__':
    main()