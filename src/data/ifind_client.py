import os
import sys
import logging
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

_IFIND_AVAILABLE = False
_IFIND_LOGGED_IN = False
_LOGIN_ERROR_CODE = None

try:
    from iFinDPy import (
        THS_iFinDLogin,
        THS_iFinDLogout,
        THS_BD,
        THS_HF,
        THS_RQ,
        THS_DP,
        THS_DR,
        THS_WC,
    )
    _IFIND_AVAILABLE = True
    logger.info("iFinDPy SDK 已加载")
except ImportError:
    logger.warning("iFinDPy SDK 未安装，将使用 akshare 作为数据源。安装说明见 README.md")
    _IFIND_AVAILABLE = False


def ifind_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _IFIND_AVAILABLE:
            logger.debug(f"iFinDPy 不可用，跳过 {func.__name__}")
            return None
        if not _IFIND_LOGGED_IN:
            if not IFinDClient.auto_login():
                return None
        return func(*args, **kwargs)
    return wrapper


class IFinDClient:
    _instance = None
    _login_lock = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def is_available() -> bool:
        return _IFIND_AVAILABLE

    @staticmethod
    def is_logged_in() -> bool:
        return _IFIND_LOGGED_IN

    @staticmethod
    def auto_login() -> bool:
        global _IFIND_LOGGED_IN, _LOGIN_ERROR_CODE

        if _IFIND_LOGGED_IN:
            return True
        if IFinDClient._login_lock:
            timeout = 10
            start = time.time()
            while IFinDClient._login_lock and time.time() - start < timeout:
                time.sleep(0.1)
            return _IFIND_LOGGED_IN

        IFinDClient._login_lock = True
        try:
            username = os.getenv("IFIND_USERNAME")
            password = os.getenv("IFIND_PASSWORD")

            if not username or not password:
                logger.warning("iFinD 账号未配置（IFIND_USERNAME/IFIND_PASSWORD），跳过自动登录")
                return False

            logger.info("正在登录同花顺 iFinD...")
            error_code = THS_iFinDLogin(username, password)

            if error_code in (0, -201):
                _IFIND_LOGGED_IN = True
                _LOGIN_ERROR_CODE = error_code
                msg = "登录成功" if error_code == 0 else "重复登录（已在线）"
                logger.info(f"iFinD {msg}（error_code={error_code}）")
                return True
            elif error_code == -2:
                logger.error(f"iFinD 登录失败：用户名或密码错误（error_code={error_code}）")
            else:
                logger.error(f"iFinD 登录失败（error_code={error_code}）")
            _LOGIN_ERROR_CODE = error_code
            return False
        except Exception as e:
            logger.error(f"iFinD 登录异常：{e}")
            return False
        finally:
            IFinDClient._login_lock = False

    @staticmethod
    def logout() -> bool:
        global _IFIND_LOGGED_IN, _LOGIN_ERROR_CODE
        if not _IFIND_AVAILABLE or not _IFIND_LOGGED_IN:
            return True
        try:
            code = THS_iFinDLogout()
            if code == 0:
                _IFIND_LOGGED_IN = False
                _LOGIN_ERROR_CODE = None
                logger.info("iFinD 已登出")
                return True
            logger.warning(f"iFinD 登出失败（error_code={code}）")
            return False
        except Exception as e:
            logger.error(f"iFinD 登出异常：{e}")
            return False

    @staticmethod
    def _format_codes(codes: List[str]) -> str:
        formatted = []
        for code in codes:
            code = code.strip()
            if code.startswith(("SH", "SZ", ".SH", ".SZ")):
                formatted.append(code.upper().lstrip("."))
                continue
            if code.startswith("6"):
                formatted.append(f"{code}.SH")
            else:
                formatted.append(f"{code}.SZ")
        return ",".join(formatted)

    @staticmethod
    def _normalize_code(ths_code: str) -> str:
        return ths_code.split(".")[0].zfill(6)

    @staticmethod
    @ifind_required
    def get_csi300_constituents(target_date: Optional[str] = None) -> Optional[List[Dict]]:
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")
        try:
            result = THS_DP(
                "block",
                f"{target_date};001005290",
                "date:Y,thscode:Y,security_name:Y",
            )
            if result.errorcode != 0:
                logger.warning(f"获取沪深300成分股失败：{result.errmsg}")
                return None
            df = result.data
            stocks = []
            for _, row in df.iterrows():
                code = IFinDClient._normalize_code(str(row.get("THSCODE", "")))
                name = str(row.get("SECURITY_NAME", ""))
                if code:
                    stocks.append({"code": code, "name": name})
            logger.info(f"iFinD 获取沪深300成分股：{len(stocks)}只（{target_date}）")
            return stocks
        except Exception as e:
            logger.error(f"获取沪深300成分股异常：{e}")
            return None

    @staticmethod
    @ifind_required
    def get_financial_map(
        codes: List[str],
        report_date: Optional[str] = None,
    ) -> Optional[Dict[str, Dict]]:
        if not codes:
            return {}
        if report_date is None:
            today = date.today()
            q = (today.month - 1) // 3
            report_dates = [
                f"{today.year - 1}1231",
                f"{today.year}{q * 3:02d}{[31,28,31,30,31,30,31,31,30,31,30,31][q*3+2]:02d}",
                f"{today.year - 1}0930",
            ]
        else:
            report_dates = [report_date]

        ths_codes = IFinDClient._format_codes(codes)
        result_map: Dict[str, Dict] = {}

        # 注意（2026/08实测）：
        #   THS_BD 免费版一次只能取 1 个指标（指标名拼分号会 errcode=-209），
        #   但单个指标可以一次传多只股票（逗号分隔，几十上百只都行）。
        # 所以这里：逐个报告期 → 逐个指标 → 批量股票，最后按 code 合并字段。
        INDICATORS = [
            # (iFinD指标名, 本项目输出key, 是否财报相关)
            ("roe",                     "roe",                  True),
            ("roa",                     "roa",                  True),
            ("pe",                      "pe_static",            True),
            ("pb",                      "pb_ratio",             True),
            ("pe_ttm",                  "pe_ttm",               True),
            ("ths_basic_eps_stock",     "eps",                  True),
            ("ths_current_ratio_stock", "current_ratio",        True),
            ("ths_pe_ttm_stock",        "pe_ttm_alt",           True),
            # 没有免费指标的字段，后续在调用方用其他数据池或默认值兜底（利润增长/扣非/毛利率等）
        ]

        for rpt_date in report_dates:
            fetched: Dict[str, Dict] = {}
            all_ok = True
            for ind_name, out_key, _ in INDICATORS:
                try:
                    result = THS_BD(ths_codes, ind_name, rpt_date)
                except Exception as e:
                    logger.warning(f"THS_BD 异常：指标={ind_name} 报告期={rpt_date} -> {e}")
                    all_ok = False
                    continue
                if result.errorcode != 0:
                    logger.warning(
                        f"THS_BD 指标 {ind_name}（{rpt_date}）失败：{result.errmsg}"
                    )
                    all_ok = False
                    continue
                df = result.data
                if df is None or df.empty:
                    continue
                for _, row in df.iterrows():
                    raw_code = str(row.get("THSCODE", row.get("thscode", "")))
                    code = IFinDClient._normalize_code(raw_code)
                    if not code:
                        continue
                    bucket = fetched.setdefault(code, {})
                    val = IFinDClient._safe_float(row.iloc[-1])
                    bucket[out_key] = val
                    # 顺便把 pe_ttm 的值覆盖到最终 pe_ratio / pe_ratio，财报 pe 和 pb 比行情版准
                    if out_key == "pe_ttm":
                        bucket["pe_ratio_fin"] = val
                    if out_key == "pb_ratio":
                        bucket["pb_ratio_fin"] = val

            if not fetched:
                continue

            for code, fields in fetched.items():
                # pe_ratio 优先用 pe_ttm（更常用）
                final_pe = fields.get("pe_ttm") or fields.get("pe_ttm_alt") or fields.get("pe_static")
                final_pb = fields.get("pb_ratio_fin") or fields.get("pb_ratio")
                entry = {
                    "roe": fields.get("roe"),
                    "roa": fields.get("roa"),
                    "profit_growth": None,
                    "profit_growth_deduct": None,
                    "pb_ratio": final_pb,
                    "pe_ratio": final_pe,
                    "pe_ttm": final_pe,
                    "gross_margin": None,
                    "dividend_yield": None,
                    "market_cap": None,
                    "eps": fields.get("eps"),
                    "current_ratio": fields.get("current_ratio"),
                    "debt_ratio": None,
                    "report_date": rpt_date,
                    "source": "ifind",
                }
                # 把 THS_RQ 算不到的 PE 也在这里一次性补好给调用方
                if result_map.get(code) is None or entry.get("pe_ratio"):
                    result_map[code] = entry

            logger.info(
                f"iFinD 财报数据（{rpt_date}）：覆盖 {len(result_map)}/{len(codes)} 只股票"
                + ("（部分指标失败，其他字段沿用 akshare 兜底）" if not all_ok else "")
            )
            if len(result_map) >= max(1, int(len(codes) * 0.7)):
                return result_map if result_map else None

        return result_map if result_map else None

    @staticmethod
    @ifind_required
    def get_industry_map(codes: List[str]) -> Optional[Dict[str, Dict]]:
        if not codes:
            return {}
        try:
            ths_codes = IFinDClient._format_codes(codes)
            result = THS_BD(
                ths_codes,
                "ths_industry_sw2021_stock;ths_industry_name_thscode;ths_concept_plate_stock",
                ";;",
            )
            if result.errorcode != 0:
                logger.debug(f"iFinD 行业分类取数失败（免费版可能不支持）：{result.errmsg}，将回退腾讯/本地数据源")
                return None

            df = result.data
            industry_map: Dict[str, Dict] = {}
            for _, row in df.iterrows():
                raw_code = str(row.get("THSCODE", ""))
                code = IFinDClient._normalize_code(raw_code)
                if not code:
                    continue
                industry_map[code] = {
                    "industry_sw": str(row.get("ths_industry_sw2021_stock", "") or ""),
                    "industry_ths": str(row.get("ths_industry_name_thscode", "") or ""),
                    "concept": str(row.get("ths_concept_plate_stock", "") or ""),
                }
            logger.info(f"iFinD 行业分类覆盖：{len(industry_map)}/{len(codes)} 只")
            return industry_map
        except Exception as e:
            logger.debug(f"iFinD 行业分类接口异常（免费版可能不支持）：{e}")
            return None

    @staticmethod
    @ifind_required
    def get_realtime_quotes(codes: List[str]) -> Optional[List[Dict]]:
        if not codes:
            return []
        try:
            ths_codes = IFinDClient._format_codes(codes)
            # 重要：指标名必须严格匹配 iFinD 免费版实际存在的字段（2026/08实测）
            # 返回列固定为：time, thscode, latest, change, open, high, low, preClose, volume, amount, pb
            indicators = "latest;change;open;high;low;preClose;volume;amount;pb"
            result = THS_RQ(ths_codes, indicators)
            if result.errorcode != 0:
                logger.warning(f"获取实时行情失败：{result.errmsg}")
                return None

            df = result.data
            quotes = []
            for _, row in df.iterrows():
                raw_code = str(row.get("THSCODE", row.get("thscode", "")))
                code = IFinDClient._normalize_code(raw_code)
                if not code:
                    continue
                latest = IFinDClient._safe_float(row.get("latest"))
                pre_close = IFinDClient._safe_float(row.get("preClose"))
                change_val = IFinDClient._safe_float(row.get("change"))
                change_pct = None
                if latest is not None and pre_close not in (None, 0):
                    change_pct = (latest - pre_close) / pre_close * 100
                quotes.append({
                    "code": code,
                    "name": str(row.get("SECURITY_NAME", row.get("security_name", ""))),
                    "price": latest,
                    "prev_close": pre_close,
                    "open": IFinDClient._safe_float(row.get("open")),
                    "high": IFinDClient._safe_float(row.get("high")),
                    "low": IFinDClient._safe_float(row.get("low")),
                    "change_pct": change_pct if change_pct is not None else (
                        (change_val / pre_close * 100) if change_val and pre_close not in (None, 0) else None
                    ),
                    "volume": IFinDClient._safe_float(row.get("volume")),
                    "turnover": IFinDClient._safe_float(row.get("amount")),
                    "turnover_rate": None,  # THS_RQ 免费版不返回换手率
                    "pe_ratio": None,       # THS_RQ 免费版不返回 PE，用财报 pe 字段兜底
                    "pb_ratio": IFinDClient._safe_float(row.get("pb")),
                    "market_cap": None,
                    "negotiable_mv": None,
                })
            logger.info(f"iFinD 实时行情：{len(quotes)}只")
            return quotes
        except Exception as e:
            logger.error(f"获取实时行情异常：{e}")
            return None

    @staticmethod
    @ifind_required
    def get_historical_kline(
        code: str,
        days: int = 60,
        end_date: Optional[str] = None,
    ) -> Optional["pd.DataFrame"]:
        try:
            import pandas as pd

            if end_date is None:
                end_date = date.today().strftime("%Y-%m-%d")
            start_ts = time.mktime(
                datetime.strptime(end_date, "%Y-%m-%d").timetuple()
            ) - days * 86400
            start_date = datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d")

            ths_code = IFinDClient._format_codes([code])
            indicators = "open;close;high;low;volume;amount"
            result = THS_HF(
                ths_code,
                indicators,
                "",
                f"{start_date} 09:30:00",
                f"{end_date} 15:00:00",
                "format:json",
            )
            if result.errorcode != 0:
                logger.warning(f"获取K线数据失败（{code}）：{result.errmsg}")
                return None

            raw = result.data
            tables = raw.get("tables", []) if isinstance(raw, dict) else []
            if not tables:
                return pd.DataFrame()

            rows = []
            for t in tables:
                time_arr = t.get("time", [])
                data = {k: v for k, v in t.items() if k != "time"}
                n = len(time_arr)
                for i in range(n):
                    row = {
                        "date": datetime.fromtimestamp(time_arr[i]).strftime("%Y-%m-%d")
                        if isinstance(time_arr[i], (int, float))
                        else str(time_arr[i]),
                    }
                    for k, v in data.items():
                        if isinstance(v, list) and i < len(v):
                            row[k] = v[i]
                    rows.append(row)

            df = pd.DataFrame(rows)
            if not df.empty:
                col_map = {
                    "open": "open",
                    "close": "close",
                    "high": "high",
                    "low": "low",
                    "volume": "volume",
                    "amount": "turnover",
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").reset_index(drop=True)
            logger.debug(f"iFinD K线（{code}）：{len(df)}条")
            return df
        except Exception as e:
            logger.error(f"获取K线数据异常（{code}）：{e}")
            return None

    @staticmethod
    @ifind_required
    def iwencai_query(query: str, query_type: str = "stock") -> Optional[List[Dict]]:
        try:
            result = THS_WC(query, query_type)
            if result.errorcode != 0:
                logger.warning(f"iWencai 查询失败：{result.errmsg}")
                return None
            df = result.data
            if df is None or df.empty:
                return []
            records = df.to_dict("records")
            logger.info(f"iWencai [{query}] 返回 {len(records)} 条")
            return records
        except Exception as e:
            logger.error(f"iWencai 查询异常：{e}")
            return None

    @staticmethod
    def _safe_float(val) -> Optional[float]:
        if val is None:
            return None
        try:
            import pandas as pd

            if isinstance(val, float) and pd.isna(val):
                return None
            f = float(val)
            if f == float("inf") or f == float("-inf"):
                return None
            return f
        except (ValueError, TypeError):
            return None
