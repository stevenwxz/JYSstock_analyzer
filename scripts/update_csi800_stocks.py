#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新中证800成分股列表
该脚本用于定期更新中证800成分股列表，确保分析系统使用最新的股票池
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

def _fetch_index_cons(symbol, name):
    """获取单个指数的成分股，返回 {code: name} 字典，两种接口都试"""
    result = {}

    # 方法1: index_stock_cons
    try:
        df = ak.index_stock_cons(symbol=symbol)
        for _, row in df.iterrows():
            result[row['品种代码']] = row['品种名称']
        logger.info(f"  {name}: akshare获取 {len(result)} 只")
    except Exception as e:
        logger.warning(f"  {name} akshare失败: {e}")

    # 方法2: index_stock_cons_csindex 补全
    try:
        time.sleep(1)
        df2 = ak.index_stock_cons_csindex(symbol=symbol)
        added = 0
        for _, row in df2.iterrows():
            code = row['成分券代码']
            if code not in result:
                result[code] = row['成分券名称']
                added += 1
        if added:
            logger.info(f"  {name}: csindex补全 {added} 只，合计 {len(result)} 只")
    except Exception as e2:
        logger.debug(f"  {name} csindex补全失败: {e2}")

    return result


def _fetch_from_eastmoney():
    """从东方财富拉取中证800成分股（沪深300 TYPE=1 + 中证500 TYPE=3），数据最完整"""
    from urllib.request import Request, ProxyHandler, build_opener
    from urllib.parse import urlencode

    opener = build_opener(ProxyHandler({}))
    stocks = {}

    for t, label in [('1', '沪深300'), ('3', '中证500')]:
        page = 1
        while True:
            params = urlencode({
                'reportName': 'RPT_INDEX_TS_COMPONENT',
                'columns': 'SECURITY_CODE,SECURITY_NAME_ABBR',
                'filter': f'(TYPE="{t}")',
                'pageNumber': page, 'pageSize': 500,
                'sortColumns': 'SECURITY_CODE', 'sortTypes': 1,
            })
            url = f'https://datacenter-web.eastmoney.com/api/data/v1/get?{params}'
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with opener.open(req, timeout=15) as resp:
                data = json.loads(resp.read())
            result = data.get('result')
            if not result:
                break
            rows = result.get('data') or []
            if not rows:
                break
            for r in rows:
                stocks[r['SECURITY_CODE']] = r['SECURITY_NAME_ABBR']
            if len(rows) < 500:
                break
            page += 1
        logger.info(f"  东财 {label}(TYPE={t}): 累计 {len(stocks)} 只")

    return stocks


def update_csi800_stocks():
    """更新中证800成分股列表，优先东财接口（完整），akshare做fallback"""
    logger.info("开始更新中证800成分股列表...")

    merged = {}

    # 优先: 东方财富接口（数据完整）
    try:
        logger.info("方法1: 东方财富接口...")
        merged = _fetch_from_eastmoney()
    except Exception as e:
        logger.warning(f"东财接口失败: {e}")

    # fallback: akshare 沪深300+中证500
    if len(merged) < 700:
        logger.info("方法2: akshare 沪深300+中证500 补全...")
        csi300 = _fetch_index_cons("000300", "沪深300")
        time.sleep(1)
        csi500 = _fetch_index_cons("000905", "中证500")
        for code, name in {**csi500, **csi300}.items():
            merged.setdefault(code, name)

    if not merged:
        logger.error("❌ 所有方法均失败")
        return False

    unique_stocks = [{'code': code, 'name': name} for code, name in merged.items()]
    logger.info(f"最终: {len(unique_stocks)} 只中证800成分股")

    local_file = './data/csi800_stocks.json'
    os.makedirs('./data', exist_ok=True)

    save_data = {
        'update_date': datetime.now().strftime('%Y-%m-%d'),
        'note': '中证800成分股列表(东财+akshare) - 自动生成',
        'count': len(unique_stocks),
        'stocks': unique_stocks
    }

    with open(local_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 已保存到: {local_file}")
    return True

def main():
    """主函数"""
    logger.info("中证800成分股列表更新工具")
    logger.info("="*50)

    success = update_csi800_stocks()

    if success:
        logger.info("✅ 中证800成分股列表更新成功！")
        local_file = './data/csi800_stocks.json'
        if os.path.exists(local_file):
            with open(local_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"📊 当前中证800成分股总数: {len(data['stocks'])} 只")
                logger.info(f"📅 更新日期: {data['update_date']}")

                codes = [s['code'] for s in data['stocks']]
                unique_codes = set(codes)
                if len(codes) == len(unique_codes):
                    logger.info("✅ 无重复股票代码")
                else:
                    logger.warning(f"⚠️ 发现重复: 总数{len(codes)}, 唯一{len(unique_codes)}")
    else:
        logger.error("❌ 中证800成分股列表更新失败！")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())