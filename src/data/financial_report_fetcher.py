import akshare as ak
import pandas as pd
import json
import os
import sys
import logging
from datetime import date
from typing import Dict, Optional, List

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.config import IFIND_CONFIG

logger = logging.getLogger(__name__)

_financial_cache: Optional[Dict[str, Dict]] = None
_cache_date: Optional[str] = None
_last_source: Optional[str] = None

CACHE_DIR = './cache/financial_reports'


def get_financial_data_map() -> Dict[str, Dict]:
    """
    获取全市场财报数据映射表（iFinD 优先 + akshare 兜底）。
    返回: {股票代码: {'roe': float|None, 'profit_growth': float|None, 'source': str, ...}}
    """
    global _financial_cache, _cache_date, _last_source
    today = date.today().isoformat()

    if _financial_cache is not None and _cache_date == today:
        return _financial_cache

    cache_file = os.path.join(CACHE_DIR, f'financial_{today}.json')
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                if isinstance(cached, dict) and 'data' in cached:
                    _financial_cache = cached['data']
                    _last_source = cached.get('source', 'cache')
                else:
                    _financial_cache = cached
                    _last_source = 'cache'
                _cache_date = today
                logger.info(f"从文件缓存加载财报数据，共{len(_financial_cache)}条（来源：{_last_source}）")
                return _financial_cache
        except Exception:
            pass

    target_codes = _load_csi300_codes()

    data_source = 'akshare'
    if IFIND_CONFIG.get('enabled') and IFIND_CONFIG.get('prefer_ifind'):
        ifind_data = _fetch_from_ifind(target_codes)
        if ifind_data:
            _financial_cache = ifind_data
            data_source = 'ifind'
            logger.info(f"财报数据使用同花顺 iFinD：覆盖 {len(ifind_data)}/{len(target_codes)} 只")
        else:
            logger.warning("iFinD 财报数据获取失败，回退到 akshare")
            _financial_cache = _fetch_from_akshare(target_codes)
    else:
        _financial_cache = _fetch_from_akshare(target_codes)
        if not _financial_cache and IFIND_CONFIG.get('enabled'):
            logger.info("akshare 财报为空，尝试 iFinD")
            ifind_data = _fetch_from_ifind(target_codes)
            if ifind_data:
                _financial_cache = ifind_data
                data_source = 'ifind'

    _cache_date = today
    _last_source = data_source

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_payload = {
        'date': today,
        'source': data_source,
        'count': len(_financial_cache),
        'data': _financial_cache,
    }
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_payload, f, ensure_ascii=False)

    _cleanup_old_cache()
    logger.info(f"财报数据最终来源：{data_source}，覆盖 {len(_financial_cache)} 只股票")
    return _financial_cache


def get_last_source() -> Optional[str]:
    return _last_source


def _fetch_from_ifind(target_codes: set) -> Optional[Dict[str, Dict]]:
    """通过同花顺 iFinD SDK 获取财报数据（ROE + 利润增长 + 更多指标）"""
    try:
        from src.data.ifind_client import IFinDClient

        if not IFinDClient.is_available():
            logger.debug("iFinD SDK 不可用")
            return None
        if not IFinDClient.auto_login():
            return None

        code_list = sorted(list(target_codes))
        raw = IFinDClient.get_financial_map(code_list)
        if not raw:
            return None

        result: Dict[str, Dict] = {}
        for code, fin in raw.items():
            if code not in target_codes:
                continue
            entry = {
                'roe': fin.get('roe'),
                'profit_growth': fin.get('profit_growth_deduct') or fin.get('profit_growth'),
                'pb_ratio': fin.get('pb_ratio'),
                'pe_ttm': fin.get('pe_ttm'),
                'gross_margin': fin.get('gross_margin'),
                'dividend_yield': fin.get('dividend_yield'),
                'market_cap': fin.get('market_cap'),
                'current_ratio': fin.get('current_ratio'),
                'debt_ratio': fin.get('debt_ratio'),
                'report_date': fin.get('report_date'),
                'source': 'ifind',
            }
            if entry['roe'] is not None or entry['profit_growth'] is not None:
                result[code] = entry

        return result if result else None
    except Exception as e:
        logger.warning(f"iFinD 财报数据获取异常：{e}")
        return None


def _fetch_from_akshare(target_codes: set) -> Dict[str, Dict]:
    """从 akshare 获取 ROE（年报）和净利润增长率（最新季报），只保留沪深300"""
    roe_map = _fetch_roe(target_codes)
    growth_map = _fetch_profit_growth(target_codes)

    result = {}
    for code in target_codes:
        roe = roe_map.get(code)
        growth = growth_map.get(code)
        if roe is not None or growth is not None:
            result[code] = {
                'roe': roe,
                'profit_growth': growth,
                'source': 'akshare',
            }

    logger.info(f"akshare 财报数据: ROE覆盖{len(roe_map)}只, 增长率覆盖{len(growth_map)}只 (沪深300)")
    return result


def _load_csi300_codes() -> set:
    """加载沪深300成分股代码集合，优先使用 iFinD 获取最新成分股"""
    if IFIND_CONFIG.get('enabled') and IFIND_CONFIG.get('prefer_ifind'):
        try:
            from src.data.ifind_client import IFinDClient

            if IFinDClient.is_available() and IFinDClient.auto_login():
                constituents = IFinDClient.get_csi300_constituents()
                if constituents:
                    codes = {s['code'] for s in constituents}
                    if len(codes) >= 290:
                        logger.info(f"使用 iFinD 沪深300成分股：{len(codes)}只")
                        _update_csi300_cache(constituents)
                        return codes
        except Exception as e:
            logger.debug(f"iFinD 获取沪深300成分股失败：{e}")

    try:
        with open('./data/csi300_stocks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {s['code'] for s in data['stocks']}
    except Exception:
        return set()


def _update_csi300_cache(constituents: List[Dict]) -> None:
    """将 iFinD 返回的最新成分股写入本地缓存文件"""
    try:
        payload = {
            'update_date': date.today().isoformat(),
            'source': 'ifind',
            'count': len(constituents),
            'stocks': constituents,
        }
        os.makedirs('./data', exist_ok=True)
        with open('./data/csi300_stocks.json', 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.debug(f"沪深300成分股缓存已更新：{len(constituents)}只")
    except Exception as e:
        logger.warning(f"沪深300成分股缓存写入失败：{e}")


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
