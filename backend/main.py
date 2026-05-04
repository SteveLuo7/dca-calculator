"""DCA calculator backend.

FastAPI + AKShare data endpoints for valuation, K-line data and stock news.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta
from typing import Any

import akshare as ak
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="定投收益计算器 API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INDEX_CONFIG: dict[str, dict[str, Any]] = {
    "000300": {
        "name": "沪深300",
        "ak_symbol": "沪深300指数",
        "market": "A股",
        "description": "A股蓝筹代表",
        "default_pe": 13.0,
        "earnings_growth": 6.0,
        "asset_type": "index",
    },
    "000016": {
        "name": "上证50",
        "ak_symbol": "上证50",
        "market": "A股",
        "description": "超大盘蓝筹",
        "default_pe": 11.0,
        "earnings_growth": 5.0,
        "asset_type": "index",
    },
    "000905": {
        "name": "中证500",
        "ak_symbol": "中证500指数",
        "market": "A股",
        "description": "中盘成长",
        "default_pe": 20.0,
        "earnings_growth": 7.0,
        "asset_type": "index",
    },
    "000852": {
        "name": "中证1000",
        "ak_symbol": "中证1000指数",
        "market": "A股",
        "description": "小盘活跃",
        "default_pe": 25.0,
        "earnings_growth": 8.0,
        "asset_type": "index",
    },
    "399006": {
        "name": "创业板指",
        "ak_symbol": "创业板指数",
        "market": "A股",
        "description": "成长科技",
        "default_pe": 30.0,
        "earnings_growth": 10.0,
        "asset_type": "index",
    },
    "000001": {
        "name": "上证综指",
        "ak_symbol": "上证综合指数",
        "market": "A股",
        "description": "A股全市场",
        "default_pe": 14.0,
        "earnings_growth": 6.0,
        "asset_type": "index",
    },
    "HSI": {
        "name": "恒生指数",
        "ak_symbol": None,
        "market": "港股",
        "description": "港股蓝筹",
        "default_pe": 10.0,
        "earnings_growth": 5.0,
        "asset_type": "index",
    },
    "SPX": {
        "name": "标普500",
        "ak_symbol": None,
        "market": "美股",
        "description": "美股大盘",
        "default_pe": 22.0,
        "earnings_growth": 7.0,
        "asset_type": "index",
    },
    "NDX": {
        "name": "纳斯达克100",
        "ak_symbol": None,
        "market": "美股",
        "description": "科技成长",
        "default_pe": 28.0,
        "earnings_growth": 10.0,
        "asset_type": "index",
    },
}

INDEX_KLINE_CODES = {"000300", "000016", "000905", "000852", "399006", "399001", "000001"}


def normalize_code(code: str) -> str:
    code = code.upper().strip()
    return code.zfill(6) if code.isdigit() and len(code) < 6 else code


def get_config(code: str) -> dict[str, Any] | None:
    code = normalize_code(code)
    return INDEX_CONFIG.get(code)


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
            "source": "AKShare · 天天基金",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as exc:
        logger.warning("A-share index PE fetch failed for %s: %s", ak_symbol, exc)
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


def fetch_kline_data(code: str, days: int = 250) -> list[dict[str, Any]]:
    code = normalize_code(code)
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=max(days * 2, 90))).strftime("%Y%m%d")

    try:
        if code in INDEX_KLINE_CODES:
            df = ak.index_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date)
        elif code.isdigit() and len(code) == 6:
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="")
        else:
            return []

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
            logger.warning("K-line columns not found for %s: %s", code, list(df.columns))
            return []

        df = df.tail(days).copy()
        rows: list[dict[str, Any]] = []
        for _, row in df.iterrows():
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
    except Exception as exc:
        logger.warning("K-line fetch failed for %s: %s", code, exc)
        return []


def fetch_stock_news(code: str, limit: int = 12) -> list[dict[str, Any]]:
    code = normalize_code(code)
    articles: list[dict[str, Any]] = []

    if not (code.isdigit() and len(code) == 6):
        return articles

    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return articles

        title_col = first_col(list(df.columns), ["新闻标题", "标题", "title"], ["标题", "title"])
        url_col = first_col(list(df.columns), ["新闻链接", "链接", "url"], ["链接", "url"])
        date_col = first_col(list(df.columns), ["发布时间", "时间", "日期", "date"], ["时间", "日期", "date"])
        source_col = first_col(list(df.columns), ["文章来源", "来源", "source"], ["来源", "source"])
        summary_col = first_col(list(df.columns), ["新闻内容", "内容", "摘要"], ["内容", "摘要"])

        for _, row in df.head(limit).iterrows():
            title = str(row.get(title_col, "")).strip() if title_col else ""
            if not title:
                continue
            publish_time = str(row.get(date_col, "")).strip() if date_col else ""
            articles.append(
                {
                    "title": title,
                    "url": str(row.get(url_col, "")).strip() if url_col else "",
                    "source": str(row.get(source_col, "东方财富")).strip() if source_col else "东方财富",
                    "published_at": publish_time,
                    "summary": str(row.get(summary_col, "")).strip()[:180] if summary_col else "",
                }
            )
    except Exception as exc:
        logger.warning("News fetch failed for %s: %s", code, exc)

    return articles


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "定投收益计算器 API 运行中", "version": "1.1.0"}


@app.get("/api/indices")
def get_indices() -> list[dict[str, Any]]:
    return [
        {
            "code": code,
            "name": config["name"],
            "market": config["market"],
            "description": config["description"],
            "default_pe": config["default_pe"],
            "earnings_growth": config["earnings_growth"],
        }
        for code, config in INDEX_CONFIG.items()
    ]


@app.get("/api/pe/{code}")
def get_pe(code: str) -> dict[str, Any]:
    code = normalize_code(code)
    config = get_config(code)
    if not config:
        raise HTTPException(status_code=404, detail=f"暂不支持该代码的 PE 自动查询: {code}")

    result = {
        "code": code,
        "name": config["name"],
        "market": config["market"],
        "description": config["description"],
        "earnings_growth": config["earnings_growth"],
        "pe": config["default_pe"],
        "pb": None,
        "pe_percentile": None,
        "source": "默认值",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    if config.get("ak_symbol"):
        live = fetch_a_index_pe(config["ak_symbol"])
        if live:
            result.update(live)

    return result


@app.get("/api/pe/{code}/history")
def get_pe_history(code: str, years: int = Query(default=10, ge=1, le=20)) -> dict[str, Any]:
    code = normalize_code(code)
    config = get_config(code)
    if not config or not config.get("ak_symbol"):
        return {"code": code, "history": [], "message": "该标的暂无历史 PE 数据"}

    return {"code": code, "name": config["name"], "history": fetch_pe_history(config["ak_symbol"], years)}


@app.get("/api/kline/{code}")
def get_kline(code: str, days: int = Query(default=250, ge=30, le=1000)) -> dict[str, Any]:
    code = normalize_code(code)
    config = get_config(code)
    klines = fetch_kline_data(code, days)
    return {
        "code": code,
        "name": config["name"] if config else code,
        "klines": klines,
        "count": len(klines),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "message": "" if klines else "暂无 K 线数据或数据源暂不可用",
    }


@app.get("/api/news/{code}")
def get_news(code: str, limit: int = Query(default=12, ge=1, le=30)) -> dict[str, Any]:
    code = normalize_code(code)
    config = get_config(code)
    articles = fetch_stock_news(code, limit)
    return {
        "code": code,
        "name": config["name"] if config else code,
        "articles": articles,
        "count": len(articles),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                ["基金/指数", f"{name}（{code}）"],
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
    from urllib.parse import quote

    safe_name = quote(f"定投收益_{name}_{datetime.now().strftime('%Y%m%d')}.xlsx")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
    )
