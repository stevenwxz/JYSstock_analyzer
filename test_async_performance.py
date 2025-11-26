#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步数据获取器的性能
"""

import logging
import time
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.async_data_fetcher import batch_get_stock_data_sync

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_async_fetcher():
    """测试异步获取器性能"""

    # 测试股票代码 - 选择30只作为测试
    test_codes = [
        '601318', '600519', '600036', '601166', '600276',
        '600887', '601328', '600900', '601398', '601288',
        '600030', '601668', '600048', '601888', '601601',
        '600031', '601012', '600809', '600585', '600000',
        '601088', '601225', '601818', '601919', '601857',
        '600028', '600016', '601211', '601628', '600150'
    ]

    logger.info(f"=" * 60)
    logger.info(f"开始测试异步数据获取器性能")
    logger.info(f"测试股票数量: {len(test_codes)}")
    logger.info(f"=" * 60)

    # 测试1: 不计算动量,不获取基本面
    logger.info("\n【测试1】仅获取实时数据")
    start_time = time.time()
    result1 = batch_get_stock_data_sync(
        test_codes,
        calculate_momentum=False,
        include_fundamental=False,
        max_concurrent=20
    )
    elapsed1 = time.time() - start_time
    logger.info(f"成功获取: {len(result1)}/{len(test_codes)} 只")
    logger.info(f"用时: {elapsed1:.2f}秒")
    logger.info(f"平均速度: {len(result1)/elapsed1:.1f}只/秒")

    # 测试2: 包含基本面数据
    logger.info("\n【测试2】获取实时数据 + 基本面数据")
    start_time = time.time()
    result2 = batch_get_stock_data_sync(
        test_codes,
        calculate_momentum=False,
        include_fundamental=True,
        max_concurrent=20
    )
    elapsed2 = time.time() - start_time
    logger.info(f"成功获取: {len(result2)}/{len(test_codes)} 只")
    logger.info(f"用时: {elapsed2:.2f}秒")
    logger.info(f"平均速度: {len(result2)/elapsed2:.1f}只/秒")

    # 测试3: 完整数据(包含动量)
    logger.info("\n【测试3】获取完整数据(实时 + 基本面 + 动量)")
    start_time = time.time()
    result3 = batch_get_stock_data_sync(
        test_codes,
        calculate_momentum=True,
        include_fundamental=True,
        max_concurrent=20
    )
    elapsed3 = time.time() - start_time
    logger.info(f"成功获取: {len(result3)}/{len(test_codes)} 只")
    logger.info(f"用时: {elapsed3:.2f}秒")
    logger.info(f"平均速度: {len(result3)/elapsed3:.1f}只/秒")

    # 显示样例数据
    if result3:
        logger.info("\n【样例数据】")
        sample = result3[0]
        logger.info(f"股票代码: {sample.get('code')}")
        logger.info(f"股票名称: {sample.get('name')}")
        logger.info(f"当前价格: {sample.get('price')}")
        logger.info(f"涨跌幅: {sample.get('change_pct'):+.2f}%")
        logger.info(f"PE: {sample.get('pe_ratio')}")
        logger.info(f"PB: {sample.get('pb_ratio')}")
        logger.info(f"ROE: {sample.get('roe')}")
        logger.info(f"20日动量: {sample.get('momentum_20d'):.2f}%")

    # 性能总结
    logger.info("\n" + "=" * 60)
    logger.info("性能测试总结")
    logger.info("=" * 60)
    logger.info(f"测试1 (仅实时): {elapsed1:.2f}秒, {len(result1)/elapsed1:.1f}只/秒")
    logger.info(f"测试2 (实时+基本面): {elapsed2:.2f}秒, {len(result2)/elapsed2:.1f}只/秒")
    logger.info(f"测试3 (完整数据): {elapsed3:.2f}秒, {len(result3)/elapsed3:.1f}只/秒")

    # 估算沪深300全量分析时间
    estimated_time = (elapsed3 / len(test_codes)) * 300
    logger.info(f"\n估算沪深300全量分析时间: {estimated_time/60:.1f}分钟")
    logger.info(f"相比原来的20-40分钟,预计提升: {(30*60/estimated_time):.1f}倍")

if __name__ == '__main__':
    test_async_fetcher()
