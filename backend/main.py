"""DCA calculator backend.

FastAPI + AKShare data endpoints for valuation, search, quote, K-line data and news.
All live data calls are wrapped with static/mainland-accessible fallback data.
"""
from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

import akshare as ak
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

# 导入数据模块
from data_modules import (
    GLOBAL_INDICES,
    GLOBAL_STOCKS,
    GLOBAL_ETF,
    MARKET_REGIONS,
    FUND_PREFIXES,
)

# 导入搜索模块
from search_module import (
    get_global_catalog,
    get_full_catalog,
    search_assets,
    get_suggestions,
    get_market_summary,
    resolve_symbol,
    get_hot_assets,
    get_region_assets,
    normalize_code as search_normalize_code,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="定投收益计算器 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_CANDIDATES = [
    Path(os.getenv("FRONTEND_DIR", "")) if os.getenv("FRONTEND_DIR") else None,
    BASE_DIR / "frontend",
    BASE_DIR.parent / "frontend",
]


def frontend_dir() -> Path | None:
    for candidate in FRONTEND_CANDIDATES:
        if candidate and (candidate / "index.html").exists():
            return candidate
    return None


# 兼容旧代码的配置
INDEX_CONFIG = GLOBAL_INDICES
INDEX_KLINE_CODES = {code for code in GLOBAL_INDICES if code.isdigit() and len(code) == 6}


def normalize_code(code: str) -> str:
    """标准化证券代码（兼容旧代码）。"""
    return search_normalize_code(code)


def first_col(columns: list[str], names: list[str], contains: list[str] | None = None) -> str | None:
    normalized = {str(c).lower().strip(): c for c in columns}
    for name in names:
        key = name.lower().strip()
        if key in normalized:
            return normalized[key]
    if contains:
        for col in columns:
            text = str(col).lower().strip()
            if any(key.lower() in text for key in contains):
                return col
    return None


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def base_catalog() -> list[dict[str, Any]]:
    """基础目录（兼容旧代码）。"""
    return list(get_global_catalog())


@lru_cache(maxsize=1)
def search_catalog() -> tuple[dict[str, Any], ...]:
    """搜索目录（兼容旧代码，使用新模块）。"""
    return get_full_catalog()


def resolve_security(code: str) -> dict[str, Any]:
    """解析证券信息（兼容旧代码，使用新模块）。"""
    result = resolve_symbol(code)
    if result:
        return result

    # 降级处理
    code = normalize_code(code)
    market = "A股" if code.isdigit() and len(code) == 6 else "海外"
    asset_type = "fund" if code.isdigit() and code.startswith(FUND_PREFIXES) else "stock"
    return {
        "code": code,
        "name": code,
        "market": market,
        "region": "其他",
        "country": "-",
        "currency": "-",
        "description": "自定义标的",
        "asset_type": asset_type,
        "default_pe": 16.0,
        "earnings_growth": 6.0,
        "source": "用户输入",
    }


def fetch_a_index_pe(ak_symbol: str) -> dict[str, Any] | None:
    try:
        df = ak.index_value_hist_funddb(symbol=ak_symbol, indicator="市盈率")
        if df is None or df.empty:
            return None

        date_col = df.columns[0]
        value_col = next(col for col in df.columns if col != date_col)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        pe = safe_float(df.iloc[-1][value_col])
        if pe is None:
            return None

        pb = None
        try:
            pb_df = ak.index_value_hist_funddb(symbol=ak_symbol, indicator="市净率")
            if pb_df is not None and not pb_df.empty:
                pb_value_col = next(col for col in pb_df.columns if col != pb_df.columns[0])
                pb = safe_float(pb_df.iloc[-1][pb_value_col])
        except Exception as exc:
            logger.debug("PB fetch failed: %s", exc)

        recent = df.tail(2520)
        values = pd.to_numeric(recent[value_col], errors="coerce").dropna()
        percentile = round(float((values < pe).mean() * 100), 1) if not values.empty else None

        return {
            "pe": round(pe, 2),
            "pb": round(pb, 2) if pb is not None else None,
            "pe_percentile": percentile,
            "source": "AKShare · 天天基金（备份：静态估值）",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as exc:
        logger.warning("A-share index PE fetch failed for %s: %s", ak_symbol, exc)
        return None


def fetch_a_stock_pe(code: str) -> dict[str, Any] | None:
    if not (code.isdigit() and len(code) == 6):
        return None
    try:
        df = ak.stock_zh_a_spot_em()
        if df is None or df.empty:
            return None
        code_col = first_col(list(df.columns), ["代码", "code"], ["代码", "code"])
        if not code_col:
            return None
        row_df = df[df[code_col].astype(str).str.zfill(6) == code]
        if row_df.empty:
            return None
        row = row_df.iloc[0]
        pe_col = first_col(list(df.columns), ["市盈率-动态", "市盈率", "pe"], ["市盈率", "pe"])
        pb_col = first_col(list(df.columns), ["市净率", "pb"], ["市净率", "pb"])
        name_col = first_col(list(df.columns), ["名称", "name"], ["名称", "name"])
        pe = safe_float(row.get(pe_col)) if pe_col else None
        if pe is None or pe <= 0:
            return None
        return {
            "name": str(row.get(name_col, code)).strip() if name_col else code,
            "pe": round(pe, 2),
            "pb": round(safe_float(row.get(pb_col), 0) or 0, 2) if pb_col else None,
            "source": "AKShare · 东方财富行情（备份：默认估值）",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as exc:
        logger.warning("A-share stock PE fetch failed for %s: %s", code, exc)
        return None


def fetch_pe_history(ak_symbol: str, years: int = 10) -> list[dict[str, Any]]:
    try:
        df = ak.index_value_hist_funddb(symbol=ak_symbol, indicator="市盈率")
        if df is None or df.empty:
            return []

        date_col = df.columns[0]
        value_col = next(col for col in df.columns if col != date_col)
        df[date_col] = pd.to_datetime(df[date_col])
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
        cutoff = datetime.now() - timedelta(days=years * 365)
        df = df[df[date_col] >= cutoff].dropna(subset=[value_col])
        df = df.set_index(date_col).sort_index()
        monthly = df[value_col].resample("ME").last().dropna()
        return [{"date": str(date.date()), "pe": round(float(value), 2)} for date, value in monthly.items()]
    except Exception as exc:
        logger.warning("PE history fetch failed for %s: %s", ak_symbol, exc)
        return []


def normalize_kline_df(df: pd.DataFrame, limit: int | None = None, yearly: bool = False) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []

    date_col = first_col(list(df.columns), ["日期", "date"], ["日期", "date"])
    open_col = first_col(list(df.columns), ["开盘", "开盘价", "open"], ["open", "开盘"])
    close_col = first_col(list(df.columns), ["收盘", "收盘价", "close"], ["close", "收盘"])
    high_col = first_col(list(df.columns), ["最高", "最高价", "high"], ["high", "最高"])
    low_col = first_col(list(df.columns), ["最低", "最低价", "low"], ["low", "最低"])
    volume_col = first_col(list(df.columns), ["成交量", "volume"], ["volume", "成交量"])
    amount_col = first_col(list(df.columns), ["成交额", "amount"], ["amount", "成交额"])
    pct_col = first_col(list(df.columns), ["涨跌幅", "pct_chg"], ["涨跌幅", "pct"])

    required = [date_col, open_col, close_col, high_col, low_col]
    if any(col is None for col in required):
        logger.warning("K-line columns not found: %s", list(df.columns))
        return []

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    for col in [open_col, close_col, high_col, low_col, volume_col, amount_col, pct_col]:
        if col:
            work[col] = pd.to_numeric(work[col], errors="coerce")
    work = work.dropna(subset=[date_col, open_col, close_col, high_col, low_col]).sort_values(date_col)

    if yearly:
        work = work.set_index(date_col)
        agg: dict[str, Any] = {open_col: "first", high_col: "max", low_col: "min", close_col: "last"}
        if volume_col:
            agg[volume_col] = "sum"
        if amount_col:
            agg[amount_col] = "sum"
        work = work.resample("YE").agg(agg).dropna(subset=[open_col, close_col, high_col, low_col]).reset_index()
        pct_col = None

    if limit:
        work = work.tail(limit)

    rows: list[dict[str, Any]] = []
    for _, row in work.iterrows():
        rows.append(
            {
                "time": str(pd.to_datetime(row[date_col]).date()),
                "open": safe_float(row[open_col], 0) or 0,
                "high": safe_float(row[high_col], 0) or 0,
                "low": safe_float(row[low_col], 0) or 0,
                "close": safe_float(row[close_col], 0) or 0,
                "volume": safe_float(row[volume_col], 0) if volume_col else 0,
                "amount": safe_float(row[amount_col], 0) if amount_col else None,
                "pct_chg": safe_float(row[pct_col]) if pct_col else None,
            }
        )
    return rows


def fetch_kline_data(code: str, days: int = 250, period: str = "daily", range_: str = "compact") -> list[dict[str, Any]]:
    code = normalize_code(code)
    period = period if period in {"daily", "weekly", "monthly", "yearly"} else "daily"
    end_date = datetime.now().strftime("%Y%m%d")
    fetch_period = "monthly" if period == "yearly" else period
    start_date = "19900101" if range_ == "all" else (datetime.now() - timedelta(days=max(days * 2, 120))).strftime("%Y%m%d")

    try:
        df: pd.DataFrame | None = None
        # A股指数
        if code in INDEX_KLINE_CODES:
            df = ak.index_zh_a_hist(symbol=code, period=fetch_period, start_date=start_date, end_date=end_date)
        # A股基金
        elif code.isdigit() and len(code) == 6 and code.startswith(FUND_PREFIXES):
            try:
                df = ak.fund_etf_hist_em(symbol=code, period=fetch_period, start_date=start_date, end_date=end_date, adjust="")
            except Exception:
                df = ak.stock_zh_a_hist(symbol=code, period=fetch_period, start_date=start_date, end_date=end_date, adjust="")
        # A股股票
        elif code.isdigit() and len(code) == 6:
            df = ak.stock_zh_a_hist(symbol=code, period=fetch_period, start_date=start_date, end_date=end_date, adjust="")
        # 海外指数（美股、港股等）
        elif code in INDEX_CONFIG:
            try:
                df = ak.index_global_hist(symbol=code, period=fetch_period, start_date=start_date, end_date=end_date)
            except Exception as exc:
                logger.debug("Overseas index kline failed for %s: %s", code, exc)
                df = None
        # 海外股票（美股、港股等）
        else:
            # 尝试获取海外股票K线数据
            try:
                # 处理港股代码 (0700.HK -> 0700)
                hk_code = code.replace(".HK", "")
                if hk_code.isdigit() and len(hk_code) == 4:
                    df = ak.stock_hk_hist(symbol=hk_code, period=fetch_period, start_date=start_date, end_date=end_date, adjust="qfq")
                # 处理美股代码 (AAPL, MSFT等)
                elif code.isalpha() and len(code) <= 6 and not code.endswith((".HK", ".US")):
                    df = ak.stock_us_hist(symbol=code, period=fetch_period, start_date=start_date, end_date=end_date, adjust="")
            except Exception as exc:
                logger.debug("Overseas stock kline failed for %s: %s", code, exc)
                return []

        limit = None if range_ == "all" or period == "yearly" else days
        return normalize_kline_df(df, limit=limit, yearly=period == "yearly")
    except Exception as exc:
        logger.warning("K-line fetch failed for %s: %s", code, exc)
        return []


def fallback_quote(security: dict[str, Any]) -> dict[str, Any]:
    price = safe_float(security.get("fallback_price"))
    change_pct = safe_float(security.get("fallback_change_pct"), 0) or 0
    change = None
    prev = None
    if price is not None:
        prev = price / (1 + change_pct / 100) if change_pct != -100 else price
        change = price - prev
    return {
        "code": security["code"],
        "name": security.get("name", security["code"]),
        "market": security.get("market", "-"),
        "asset_type": security.get("asset_type", "stock"),
        "price": round(price, 4) if price is not None else None,
        "previous_close": round(prev, 4) if prev is not None else None,
        "change": round(change, 4) if change is not None else None,
        "change_pct": round(change_pct, 2) if price is not None else None,
        "source": "备份数据源 · 静态行情基准" if price is not None else "暂无实时行情（可继续估值/定投测算）",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def fetch_quote_data(code: str) -> dict[str, Any]:
    security = resolve_security(code)
    code = security["code"]
    
    # 尝试获取实时行情数据
    try:
        # A股行情
        if code.isdigit() and len(code) == 6:
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                code_col = first_col(list(df.columns), ["代码", "code"], ["代码", "code"])
                if code_col:
                    row_df = df[df[code_col].astype(str).str.zfill(6) == code]
                    if not row_df.empty:
                        row = row_df.iloc[0]
                        price_col = first_col(list(df.columns), ["最新价", "close", "price"], ["最新价", "收盘"])
                        name_col = first_col(list(df.columns), ["名称", "name"], ["名称", "name"])
                        change_col = first_col(list(df.columns), ["涨跌额", "change"], ["涨跌额", "change"])
                        pct_col = first_col(list(df.columns), ["涨跌幅", "pct_chg"], ["涨跌幅", "pct"])
                        price = safe_float(row.get(price_col)) if price_col else None
                        if price is not None and price > 0:
                            change = safe_float(row.get(change_col), 0) or 0 if change_col else 0
                            change_pct = safe_float(row.get(pct_col), 0) or 0 if pct_col else 0
                            return {
                                "code": code,
                                "name": str(row.get(name_col, code)).strip() if name_col else security.get("name", code),
                                "market": security.get("market", "-"),
                                "asset_type": security.get("asset_type", "stock"),
                                "price": round(price, 4),
                                "previous_close": round(price - change, 4) if change else None,
                                "change": round(change, 4),
                                "change_pct": round(change_pct, 2),
                                "source": "AKShare · 东方财富实时行情",
                                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            }
        # 海外指数行情
        elif code in INDEX_CONFIG:
            try:
                df = ak.index_global_spot()
                if df is not None and not df.empty:
                    name_col = first_col(list(df.columns), ["名称", "name"], ["名称", "name"])
                    price_col = first_col(list(df.columns), ["最新价", "close", "price"], ["最新价", "收盘"])
                    change_col = first_col(list(df.columns), ["涨跌额", "change"], ["涨跌额", "change"])
                    pct_col = first_col(list(df.columns), ["涨跌幅", "pct_chg"], ["涨跌幅", "pct"])
                    if name_col and price_col:
                        row_df = df[df[name_col].astype(str) == INDEX_CONFIG[code]["name"]]
                        if not row_df.empty:
                            row = row_df.iloc[0]
                            price = safe_float(row.get(price_col)) if price_col else None
                            if price is not None and price > 0:
                                change = safe_float(row.get(change_col), 0) or 0 if change_col else 0
                                change_pct = safe_float(row.get(pct_col), 0) or 0 if pct_col else 0
                                return {
                                    "code": code,
                                    "name": security.get("name", code),
                                    "market": security.get("market", "-"),
                                    "asset_type": security.get("asset_type", "stock"),
                                    "price": round(price, 4),
                                    "previous_close": round(price - change, 4) if change else None,
                                    "change": round(change, 4),
                                    "change_pct": round(change_pct, 2),
                                    "source": "AKShare · 全球指数实时行情",
                                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                }
            except Exception as exc:
                logger.debug("Overseas index quote failed for %s: %s", code, exc)
        # 港股行情
        elif code.endswith(".HK") or (len(code) == 4 and code.isdigit()):
            try:
                hk_code = code.replace(".HK", "")
                df = ak.stock_hk_spot_em()
                if df is not None and not df.empty:
                    code_col = first_col(list(df.columns), ["代码", "code"], ["代码", "code"])
                    name_col = first_col(list(df.columns), ["名称", "name"], ["名称", "name"])
                    price_col = first_col(list(df.columns), ["最新价", "close", "price"], ["最新价", "收盘"])
                    change_col = first_col(list(df.columns), ["涨跌额", "change"], ["涨跌额", "change"])
                    pct_col = first_col(list(df.columns), ["涨跌幅", "pct_chg"], ["涨跌幅", "pct"])
                    if code_col and price_col:
                        row_df = df[df[code_col].astype(str) == hk_code]
                        if not row_df.empty:
                            row = row_df.iloc[0]
                            price = safe_float(row.get(price_col)) if price_col else None
                            if price is not None and price > 0:
                                change = safe_float(row.get(change_col), 0) or 0 if change_col else 0
                                change_pct = safe_float(row.get(pct_col), 0) or 0 if pct_col else 0
                                return {
                                    "code": code,
                                    "name": str(row.get(name_col, code)).strip() if name_col else security.get("name", code),
                                    "market": "港股",
                                    "asset_type": security.get("asset_type", "stock"),
                                    "price": round(price, 4),
                                    "previous_close": round(price - change, 4) if change else None,
                                    "change": round(change, 4),
                                    "change_pct": round(change_pct, 2),
                                    "source": "AKShare · 港股实时行情",
                                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                }
            except Exception as exc:
                logger.debug("HK stock quote failed for %s: %s", code, exc)
        # 美股行情
        elif code.isalpha() and len(code) <= 6 and not code.endswith((".HK", ".US")):
            try:
                df = ak.stock_us_spot_em()
                if df is not None and not df.empty:
                    code_col = first_col(list(df.columns), ["代码", "code", "symbol"], ["代码", "code", "symbol"])
                    name_col = first_col(list(df.columns), ["名称", "name"], ["名称", "name"])
                    price_col = first_col(list(df.columns), ["最新价", "close", "price"], ["最新价", "收盘"])
                    change_col = first_col(list(df.columns), ["涨跌额", "change"], ["涨跌额", "change"])
                    pct_col = first_col(list(df.columns), ["涨跌幅", "pct_chg"], ["涨跌幅", "pct"])
                    if code_col and price_col:
                        row_df = df[df[code_col].astype(str) == code]
                        if not row_df.empty:
                            row = row_df.iloc[0]
                            price = safe_float(row.get(price_col)) if price_col else None
                            if price is not None and price > 0:
                                change = safe_float(row.get(change_col), 0) or 0 if change_col else 0
                                change_pct = safe_float(row.get(pct_col), 0) or 0 if pct_col else 0
                                return {
                                    "code": code,
                                    "name": str(row.get(name_col, code)).strip() if name_col else security.get("name", code),
                                    "market": "美股",
                                    "asset_type": security.get("asset_type", "stock"),
                                    "price": round(price, 4),
                                    "previous_close": round(price - change, 4) if change else None,
                                    "change": round(change, 4),
                                    "change_pct": round(change_pct, 2),
                                    "source": "AKShare · 美股实时行情",
                                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                }
            except Exception as exc:
                logger.debug("US stock quote failed for %s: %s", code, exc)
    except Exception as exc:
        logger.debug("Quote fetch failed for %s: %s", code, exc)

    # 如果实时行情获取失败，从K线数据获取最新价格
    rows = fetch_kline_data(code, days=8, period="daily")
    if len(rows) >= 1:
        latest = rows[-1]
        prev = rows[-2] if len(rows) > 1 else latest
        price = latest["close"]
        previous_close = prev["close"] or price
        change = price - previous_close
        change_pct = (change / previous_close * 100) if previous_close else 0
        return {
            "code": code,
            "name": security.get("name", code),
            "market": security.get("market", "-"),
            "asset_type": security.get("asset_type", "stock"),
            "price": round(price, 4),
            "previous_close": round(previous_close, 4),
            "change": round(change, 4),
            "change_pct": round(change_pct, 2),
            "source": "AKShare · K线最新价（实时行情暂不可用）",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    return fallback_quote(security)


def fetch_stock_news(code: str, limit: int = 12) -> list[dict[str, Any]]:
    code = normalize_code(code)
    articles: list[dict[str, Any]] = []

    if code.isdigit() and len(code) == 6:
        try:
            df = ak.stock_news_em(symbol=code)
            if df is not None and not df.empty:
                title_col = first_col(list(df.columns), ["新闻标题", "标题", "title"], ["标题", "title"])
                url_col = first_col(list(df.columns), ["新闻链接", "链接", "url"], ["链接", "url"])
                date_col = first_col(list(df.columns), ["发布时间", "时间", "日期", "date"], ["时间", "日期", "date"])
                source_col = first_col(list(df.columns), ["文章来源", "来源", "source"], ["来源", "source"])
                summary_col = first_col(list(df.columns), ["新闻内容", "内容", "摘要"], ["内容", "摘要"])

                for _, row in df.head(limit).iterrows():
                    title = str(row.get(title_col, "")).strip() if title_col else ""
                    if not title:
                        continue
                    articles.append(
                        {
                            "title": title,
                            "url": str(row.get(url_col, "")).strip() if url_col else "",
                            "source": str(row.get(source_col, "东方财富")).strip() if source_col else "东方财富",
                            "published_at": str(row.get(date_col, "")).strip() if date_col else "",
                            "summary": str(row.get(summary_col, "")).strip()[:180] if summary_col else "",
                        }
                    )
        except Exception as exc:
            logger.warning("News fetch failed for %s: %s", code, exc)

    if len(articles) < min(limit, 4):
        security = resolve_security(code)
        keyword = quote(f"{security.get('name', code)} {code}")
        fallback = [
            ("东方财富", f"东方财富：{security.get('name', code)} 最新资讯", f"https://so.eastmoney.com/news/s?keyword={keyword}"),
            ("新浪财经", f"新浪财经：{security.get('name', code)} 行情新闻", f"https://search.sina.com.cn/?q={keyword}&c=news"),
            ("腾讯新闻", f"腾讯新闻：{security.get('name', code)} 相关新闻", f"https://news.qq.com/search?query={keyword}"),
            ("财联社", f"财联社：{security.get('name', code)} 市场动态", f"https://www.cls.cn/searchPage?keyword={keyword}"),
        ]
        for source, title, url in fallback:
            if len(articles) >= limit:
                break
            articles.append({"title": title, "url": url, "source": source, "published_at": "实时入口", "summary": "备份新闻入口，面向大陆内地网络环境。"})

    return articles[:limit]


@app.get("/api/health")
def api_health() -> dict[str, str]:
    return {"message": "定投收益计算器 API 运行中", "version": "2.0.0"}


@app.get("/api/market/regions")
def get_market_regions() -> dict[str, Any]:
    """获取市场区域配置。"""
    return {
        "regions": [
            {"name": region, **config}
            for region, config in MARKET_REGIONS.items()
        ]
    }


@app.get("/api/market/summary")
def get_api_market_summary() -> dict[str, Any]:
    """获取市场概览统计。"""
    return get_market_summary()


@app.get("/api/market/hot")
def get_api_hot_assets(
    region: str = Query(default=""),
    limit: int = Query(default=10, ge=1, le=30),
) -> dict[str, Any]:
    """获取热门标的。"""
    assets = get_hot_assets(region=region, limit=limit)
    return {"region": region or "全部", "count": len(assets), "assets": assets}


@app.get("/api/market/region/{region_name}")
def get_api_region_assets(
    region_name: str,
    asset_type: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """获取指定区域的标的。"""
    assets = get_region_assets(region=region_name, asset_type=asset_type, limit=limit)
    return {
        "region": region_name,
        "asset_type": asset_type or "全部",
        "count": len(assets),
        "assets": assets,
    }


@app.get("/api/search/suggest")
def get_api_suggestions(
    q: str = Query(default="", max_length=50),
    limit: int = Query(default=10, ge=1, le=20),
) -> dict[str, Any]:
    """获取搜索联想建议。"""
    suggestions = get_suggestions(query=q, limit=limit)
    return {"query": q, "suggestions": suggestions, "count": len(suggestions)}


@app.get("/api/search")
def get_api_search(
    q: str = Query(default="", max_length=50),
    region: str = Query(default=""),
    country: str = Query(default=""),
    market: str = Query(default=""),
    asset_type: str = Query(default=""),
    hot_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """搜索全球证券（支持多种筛选）。"""
    return search_assets(
        query=q,
        region=region,
        country=country,
        market=market,
        asset_type=asset_type,
        hot_only=hot_only,
        limit=limit,
    )


@app.get("/")
def root() -> Any:
    fdir = frontend_dir()
    if fdir:
        return FileResponse(fdir / "index.html")
    return {"message": "定投收益计算器 API 运行中", "version": "1.2.0"}


@app.get("/api/indices")
def get_indices() -> list[dict[str, Any]]:
    return [
        {
            "code": code,
            "name": config["name"],
            "market": config["market"],
            "region": config.get("region", "其他"),
            "description": config["description"],
            "default_pe": config["default_pe"],
            "earnings_growth": config["earnings_growth"],
        }
        for code, config in INDEX_CONFIG.items()
    ]


@app.get("/api/market/indices")
def get_market_indices() -> dict[str, Any]:
    """获取按区域分组的指数列表。"""
    regions = ["亚洲市场", "欧洲市场", "美洲市场"]
    grouped: dict[str, list[dict[str, Any]]] = {region: [] for region in regions}

    for code, config in GLOBAL_INDICES.items():
        region = config.get("region", "其他")
        if region in grouped:
            grouped[region].append(
                {
                    "code": code,
                    "name": config["name"],
                    "market": config["market"],
                    "country": config["country"],
                    "currency": config["currency"],
                    "description": config["description"],
                    "default_pe": config["default_pe"],
                    "earnings_growth": config["earnings_growth"],
                    "hot": config.get("hot", False),
                }
            )

    return {
        "regions": [
            {"name": region, "items": grouped.get(region, [])}
            for region in regions
        ],
        "source": "内置数据库 + AKShare",
    }


@app.get("/api/search")
def search_assets(q: str = Query(default="", max_length=50), limit: int = Query(default=12, ge=1, le=30)) -> dict[str, Any]:
    query = normalize_code(q) if q.strip().isascii() else q.strip().lower()
    query_lower = q.strip().lower()
    rows = []
    for item in search_catalog():
        code = str(item.get("code", ""))
        name = str(item.get("name", ""))
        haystack = " ".join([code, name, str(item.get("market", "")), str(item.get("asset_type", "")), str(item.get("fund_type", "")), str(item.get("pinyin", ""))]).lower()
        if not query_lower or query.lower() in haystack or query_lower in haystack:
            rows.append(
                {
                    "code": code,
                    "name": name,
                    "market": item.get("market", "-"),
                    "asset_type": item.get("asset_type", "stock"),
                    "description": item.get("description") or item.get("fund_type") or item.get("asset_type", ""),
                    "default_pe": item.get("default_pe", 16.0),
                    "earnings_growth": item.get("earnings_growth", 6.0),
                }
            )
        if len(rows) >= limit:
            break
    return {"query": q, "results": rows, "count": len(rows), "source": "AKShare/东方财富，失败时使用内置主流市场备份清单"}


@app.get("/api/pe/{code}")
def get_pe(code: str) -> dict[str, Any]:
    code = normalize_code(code)
    security = resolve_security(code)
    result = {
        "code": code,
        "name": security.get("name", code),
        "market": security.get("market", "-"),
        "description": security.get("description", security.get("asset_type", "")),
        "asset_type": security.get("asset_type", "stock"),
        "earnings_growth": security.get("earnings_growth", 6.0),
        "pe": security.get("default_pe", 16.0),
        "pb": None,
        "pe_percentile": None,
        "source": "备份数据源 · 默认估值",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    if security.get("ak_symbol"):
        live = fetch_a_index_pe(security["ak_symbol"])
        if live:
            result.update(live)
    elif code.isdigit() and len(code) == 6 and security.get("asset_type") == "stock":
        live_stock = fetch_a_stock_pe(code)
        if live_stock:
            result.update(live_stock)

    return result


@app.get("/api/pe/{code}/history")
def get_pe_history(code: str, years: int = Query(default=10, ge=1, le=20)) -> dict[str, Any]:
    code = normalize_code(code)
    config = INDEX_CONFIG.get(code)
    if not config or not config.get("ak_symbol"):
        return {"code": code, "history": [], "message": "该标的暂无历史 PE 数据，前端将继续使用实时/默认估值"}

    return {"code": code, "name": config["name"], "history": fetch_pe_history(config["ak_symbol"], years)}


@app.get("/api/quote/{code}")
def get_quote(code: str) -> dict[str, Any]:
    return fetch_quote_data(code)


@app.get("/api/kline/{code}")
def get_kline(
    code: str,
    days: int = Query(default=250, ge=30, le=10000),
    period: str = Query(default="daily", pattern="^(daily|weekly|monthly|yearly)$"),
    range_: str = Query(default="compact", alias="range", pattern="^(compact|all)$"),
) -> dict[str, Any]:
    code = normalize_code(code)
    security = resolve_security(code)
    klines = fetch_kline_data(code, days=days, period=period, range_=range_)
    return {
        "code": code,
        "name": security.get("name", code),
        "period": period,
        "range": range_,
        "klines": klines,
        "count": len(klines),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "AKShare · 东方财富/新浪；备份为静态行情基准",
        "message": "" if klines else "暂无 K 线数据或数据源暂不可用",
    }


@app.get("/api/news/{code}")
def get_news(code: str, limit: int = Query(default=12, ge=1, le=30)) -> dict[str, Any]:
    code = normalize_code(code)
    security = resolve_security(code)
    articles = fetch_stock_news(code, limit)
    return {
        "code": code,
        "name": security.get("name", code),
        "articles": articles,
        "count": len(articles),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "东方财富实时新闻；备份为东方财富/新浪/腾讯/财联社搜索入口",
        "message": "" if articles else "暂无相关新闻或数据源暂不可用",
    }


@app.get("/api/export/excel")
def export_excel(
    code: str = Query(...),
    name: str = Query(...),
    pe: float = Query(...),
    monthly_amount: float = Query(...),
    freq: int = Query(default=12),
    bear_rate: float = Query(...),
    base_rate: float = Query(...),
    bull_rate: float = Query(...),
) -> StreamingResponse:
    freq_name = {12: "月", 52: "周", 250: "交易日"}.get(freq, "期")

    def calc_dca(annual_rate: float) -> list[dict[str, Any]]:
        periodic_rate = (1 + annual_rate) ** (1 / freq) - 1
        rows = []
        for year in range(1, 31):
            n = year * freq
            fv = monthly_amount * ((1 + periodic_rate) ** n - 1) / periodic_rate * (1 + periodic_rate)
            invested = monthly_amount * n
            gain = fv - invested
            rows.append(
                {
                    "年份": f"第{year}年",
                    "累计投入(元)": round(invested),
                    "组合价值(元)": round(fv),
                    "收益额(元)": round(gain),
                    "总收益率": f"{gain / invested:.1%}",
                    "年化回报率": f"{(fv / invested) ** (1 / year) - 1:.2%}",
                }
            )
        return rows

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        params = pd.DataFrame(
            [
                ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M")],
                ["基金/股票/指数", f"{name}（{code}）"],
                ["当前PE", pe],
                ["每期定投金额", f"¥{monthly_amount:,.0f}"],
                ["定投频率", f"每{freq_name}一次"],
                ["悲观年化回报", f"{bear_rate:.2%}"],
                ["基准年化回报", f"{base_rate:.2%}"],
                ["乐观年化回报", f"{bull_rate:.2%}"],
            ],
            columns=["参数", "值"],
        )
        params.to_excel(writer, sheet_name="参数设置", index=False)

        for sheet_name, rate in [("悲观情景", bear_rate), ("基准情景", base_rate), ("乐观情景", bull_rate)]:
            pd.DataFrame(calc_dca(rate)).to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    safe_name = quote(f"定投收益_{name}_{datetime.now().strftime('%Y%m%d')}.xlsx")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
    )


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str) -> Any:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    fdir = frontend_dir()
    if not fdir:
        raise HTTPException(status_code=404, detail="Frontend not found")
    target = fdir / full_path
    if target.is_file():
        return FileResponse(target)
    return FileResponse(fdir / "index.html")
