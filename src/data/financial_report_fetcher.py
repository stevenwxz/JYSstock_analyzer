import akshare as ak
import pandas as pd
import json
import os
import logging
from datetime import date
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_financial_cache: Optional[Dict[str, Dict]] = None
_cache_date: Optional[str] = None

CACHE_DIR = './cache/financial_reports'


def get_financial_data_map() -> Dict[str, Dict]:
    """
    获取全市场财报数据映射表。
    返回: {股票代码: {'roe': float|None, 'profit_growth': float|None}}
    """
    global _financial_cache, _cache_date
    today = date.today().isoformat()

    if _financial_cache is not None and _cache_date == today:
        return _financial_cache

    cache_file = os.path.join(CACHE_DIR, f'financial_{today}.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                _financial_cache = json.load(f)
                _cache_date = today
                logger.info(f"从文件缓存加载财报数据，共{len(_financial_cache)}条")
                return _financial_cache
        except Exception:
            pass

    _financial_cache = _fetch_from_akshare()
    _cache_date = today

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(_financial_cache, f, ensure_ascii=False)

    _cleanup_old_cache()
    return _financial_cache


def _fetch_from_akshare() -> Dict[str, Dict]:
    """从 akshare 获取 ROE（年报）和净利润增长率（最新季报），只保留沪深300"""
    target_codes = _load_csi300_codes()
    roe_map = _fetch_roe(target_codes)
    growth_map = _fetch_profit_growth(target_codes)

    result = {}
    for code in target_codes:
        roe = roe_map.get(code)
        growth = growth_map.get(code)
        if roe is not None or growth is not None:
            result[code] = {'roe': roe, 'profit_growth': growth}

    logger.info(f"财报数据: ROE覆盖{len(roe_map)}只, 增长率覆盖{len(growth_map)}只 (沪深300)")
    return result


def _load_csi300_codes() -> set:
    """加载沪深300成分股代码集合"""
    try:
        with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {s['code'] for s in data['stocks']}
    except Exception:
        return set()


def _fetch_roe(target_codes: set) -> Dict[str, float]:
    """获取年报ROE，回退: 20251231 -> 20250630"""
    for report_date in ['20251231', '20250630']:
        try:
            logger.info(f"正在获取{report_date}年报ROE...")
            df = ak.stock_yjbb_em(date=report_date)
            if df is not None and not df.empty:
                roe_map = {}
                for _, row in df.iterrows():
                    code = str(row['股票代码']).zfill(6)
                    if target_codes and code not in target_codes:
                        continue
                    roe_val = row.get('净资产收益率')
                    if pd.notna(roe_val) and -100 < float(roe_val) < 200:
                        roe_map[code] = float(roe_val)
                logger.info(f"成功获取{report_date} ROE: {len(roe_map)}只")
                return roe_map
        except Exception as e:
            logger.warning(f"获取{report_date}年报失败: {e}")
    return {}


def _fetch_profit_growth(target_codes: set) -> Dict[str, float]:
    """获取最新季报净利润增长率，回退: 20260331 -> 20251231 -> 20250930"""
    for report_date in ['20260331', '20251231', '20250930']:
        try:
            logger.info(f"正在获取{report_date}净利润增长率...")
            df = ak.stock_yjbb_em(date=report_date)
            if df is not None and not df.empty:
                growth_map = {}
                for _, row in df.iterrows():
                    code = str(row['股票代码']).zfill(6)
                    if target_codes and code not in target_codes:
                        continue
                    val = row.get('净利润-同比增长')
                    if pd.notna(val):
                        growth_map[code] = float(val)
                logger.info(f"成功获取{report_date}增长率: {len(growth_map)}只")
                return growth_map
        except Exception as e:
            logger.warning(f"获取{report_date}季报失败: {e}")
    return {}


def _cleanup_old_cache():
    """清理7天前的缓存文件"""
    if not os.path.exists(CACHE_DIR):
        return
    today = date.today()
    for f in os.listdir(CACHE_DIR):
        if not f.startswith('financial_') or not f.endswith('.json'):
            continue
        try:
            date_str = f.replace('financial_', '').replace('.json', '')
            file_date = date.fromisoformat(date_str)
            if (today - file_date).days > 7:
                os.remove(os.path.join(CACHE_DIR, f))
        except (ValueError, OSError):
            pass
