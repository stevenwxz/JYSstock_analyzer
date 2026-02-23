#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API接口测试脚本
用于验证API服务是否正常工作
"""

import requests
import json

API_BASE_URL = 'http://localhost:5000/api'

def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)

    try:
        response = requests.get(f'{API_BASE_URL}/health')
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        print("✅ 健康检查通过\n")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}\n")
        return False


def test_recommend_stocks():
    """测试推荐股票接口"""
    print("=" * 60)
    print("测试 2: 获取推荐股票")
    print("=" * 60)

    try:
        response = requests.get(f'{API_BASE_URL}/stocks/recommend')
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data['code'] == 200:
                stocks = data['data']['stocks']
                market = data['data']['marketSummary']

                print(f"推荐股票数量: {len(stocks)}")
                print(f"市场概览: 总{market['totalStocks']}只, "
                      f"涨{market['risingStocks']}只, "
                      f"跌{market['fallingStocks']}只")

                if stocks:
                    print("\n前3只推荐股票:")
                    for stock in stocks[:3]:
                        print(f"  {stock['rank']}. {stock['name']} ({stock['code']})")
                        print(f"     价格: ¥{stock['price']}, "
                              f"涨幅: {stock['changePct']:+.2f}%, "
                              f"评分: {stock['strengthScore']}")

                print("✅ 推荐股票接口正常\n")
                return True
            else:
                print(f"❌ 接口返回错误: {data['message']}\n")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}\n")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}\n")
        return False


def test_stock_detail():
    """测试股票详情接口"""
    print("=" * 60)
    print("测试 3: 获取股票详情")
    print("=" * 60)

    # 先获取推荐股票,取第一只的代码
    try:
        response = requests.get(f'{API_BASE_URL}/stocks/recommend')
        if response.status_code == 200:
            data = response.json()
            stocks = data['data']['stocks']
            if stocks:
                stock_code = stocks[0]['code']
                print(f"测试股票代码: {stock_code}")

                # 获取详情
                detail_response = requests.get(f'{API_BASE_URL}/stocks/detail/{stock_code}')
                print(f"状态码: {detail_response.status_code}")

                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data['code'] == 200:
                        stock = detail_data['data']
                        print(f"\n股票信息:")
                        print(f"  名称: {stock['name']}")
                        print(f"  代码: {stock['code']}")
                        print(f"  价格: ¥{stock['price']}")
                        print(f"  PE: {stock['peRatio']}")
                        print(f"  PB: {stock['pbRatio']}")
                        print("✅ 股票详情接口正常\n")
                        return True
                    else:
                        print(f"❌ 接口返回错误: {detail_data['message']}\n")
                        return False
            else:
                print("❌ 没有推荐股票,无法测试详情接口\n")
                return False

    except Exception as e:
        print(f"❌ 请求失败: {e}\n")
        return False


def test_market_overview():
    """测试市场概览接口"""
    print("=" * 60)
    print("测试 4: 获取市场概览")
    print("=" * 60)

    try:
        response = requests.get(f'{API_BASE_URL}/market/overview')
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data['code'] == 200:
                market = data['data']
                print(f"\n市场概览:")
                print(f"  总股票数: {market['totalStocks']}")
                print(f"  上涨股票: {market['risingStocks']}")
                print(f"  下跌股票: {market['fallingStocks']}")
                print(f"  平均涨幅: {market['avgChangePct']:+.2f}%")
                print("✅ 市场概览接口正常\n")
                return True
            else:
                print(f"❌ 接口返回错误: {data['message']}\n")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}\n")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}\n")
        return False


def test_analysis_history():
    """测试历史分析接口"""
    print("=" * 60)
    print("测试 5: 获取历史分析记录")
    print("=" * 60)

    try:
        response = requests.get(f'{API_BASE_URL}/analysis/history?days=7')
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data['code'] == 200:
                history = data['data']
                print(f"\n历史记录数量: {len(history)}")

                if history:
                    print("\n最近3条记录:")
                    for record in history[:3]:
                        print(f"  日期: {record['date']}, "
                              f"推荐{record['stockCount']}只, "
                              f"首推: {record['topStock']}")

                print("✅ 历史分析接口正常\n")
                return True
            else:
                print(f"❌ 接口返回错误: {data['message']}\n")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}\n")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}\n")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("           股票分析API服务测试")
    print("=" * 60)
    print(f"API地址: {API_BASE_URL}")
    print("=" * 60)
    print("\n⚠️  请确保API服务已启动 (python api_server.py)\n")

    # 运行所有测试
    results = []
    results.append(("健康检查", test_health()))
    results.append(("推荐股票", test_recommend_stocks()))
    results.append(("股票详情", test_stock_detail()))
    results.append(("市场概览", test_market_overview()))
    results.append(("历史分析", test_analysis_history()))

    # 总结
    print("=" * 60)
    print("           测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name:15s} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"总计: {len(results)}个测试, {passed}个通过, {failed}个失败")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 所有测试通过!API服务运行正常!")
    else:
        print(f"\n⚠️  有{failed}个测试失败,请检查API服务!")

    print("\n提示:")
    print("  - 如果所有测试都失败,请检查API服务是否启动")
    print("  - 如果部分测试失败,请检查对应功能的实现")
    print("  - 详细错误信息请查看API服务的日志输出")
    print()


if __name__ == '__main__':
    main()
