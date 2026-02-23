#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新沪深300成分股列表
该脚本用于定期更新沪深300成分股列表，确保分析系统使用最新的股票池
"""
import akshare as ak
import json
import os
import sys
import logging
from datetime import datetime
import pandas as pd
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_csi300_stocks():
    """更新沪深300成分股列表"""
    logger.info("开始更新沪深300成分股列表...")
    
    # 尝试多种方法获取成分股
    stocks = []
    stock_name_cache = {}

    # 方法1: 使用akshare获取（可能失败）
    try:
        logger.info("正在获取沪深300成分股列表（方法1：akshare）...")
        csi300 = ak.index_stock_cons(symbol="000300")
        stocks = csi300['品种代码'].tolist()

        # 同时获取股票名称
        logger.info("正在获取股票名称...")
        for i, code in enumerate(stocks):
            name = csi300[csi300['品种代码'] == code]['品种名称'].values
            if len(name) > 0:
                stock_name_cache[code] = str(name[0])
            if (i + 1) % 50 == 0:
                logger.info(f"  名称获取进度: {i+1}/{len(stocks)}")

        logger.info(f"✅ 方法1成功获取 {len(stocks)} 只沪深300成分股及名称")
    except Exception as e:
        logger.warning(f"⚠️ 方法1失败: {e}")

        # 方法2: 使用备用接口
        try:
            logger.info("正在尝试方法2：备用接口...")
            time.sleep(2)
            csi300 = ak.index_stock_cons_csindex(symbol="000300")
            stocks = csi300['成分券代码'].tolist()
            
            # 获取股票名称
            for i, code in enumerate(stocks):
                name = csi300[csi300['成分券代码'] == code]['成分券名称'].values
                if len(name) > 0:
                    stock_name_cache[code] = str(name[0])
                    
            logger.info(f"✅ 方法2成功获取 {len(stocks)} 只沪深300成分股及名称")
        except Exception as e2:
            logger.error(f"❌ 方法2也失败: {e2}")
            return False

    if not stocks:
        logger.error("❌ 无法获取沪深300成分股列表，所有方法均失败")
        return False

    # 去重处理
    seen_codes = set()
    unique_stocks = []
    for stock in stocks:
        if stock not in seen_codes:
            seen_codes.add(stock)
            name = stock_name_cache.get(stock, f'股票{stock}')
            unique_stocks.append({
                'code': stock,
                'name': name
            })

    # 构建股票数据结构
    logger.info(f"去重前: {len(stocks)} 只，去重后: {len(unique_stocks)} 只")

    # 保存到本地文件
    local_file = './data/csi300_stocks.json'
    os.makedirs('./data', exist_ok=True)
    
    save_data = {
        'update_date': datetime.now().strftime('%Y-%m-%d'),
        'note': '沪深300成分股列表 - 自动生成',
        'stocks': unique_stocks
    }
    
    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 已成功更新沪深300成分股列表到: {local_file}")
    logger.info(f"📊 共更新 {len(unique_stocks)} 只沪深300成分股")
    
    return True

def main():
    """主函数"""
    logger.info("沪深300成分股列表更新工具")
    logger.info("="*50)
    
    success = update_csi300_stocks()
    
    if success:
        logger.info("✅ 沪深300成分股列表更新成功！")
        # 验证更新结果
        local_file = './data/csi300_stocks.json'
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"📊 当前沪深300成分股总数: {len(data['stocks'])} 只")
                logger.info(f"📅 更新日期: {data['update_date']}")
                
                # 再次检查是否有重复
                codes = [s['code'] for s in data['stocks']]
                unique_codes = set(codes)
                if len(codes) == len(unique_codes):
                    logger.info("✅ 无重复股票代码")
                else:
                    logger.warning(f"⚠️ 发现重复: 总数{len(codes)}, 唯一{len(unique_codes)}")
    else:
        logger.error("❌ 沪深300成分股列表更新失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())