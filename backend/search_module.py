"""搜索模块：全球股票、指数、基金搜索联想功能。

支持多种搜索方式：
1. 代码搜索（精确匹配）
2. 名称搜索（模糊匹配）
3. 拼音搜索（中文支持）
4. 英文符号搜索（股票代码、Yahoo符号、TradingView符号）
5. 市场筛选（按区域、国家）
6. 类型筛选（股票、指数、基金）

数据源：
- AKShare（主要）
- Yahoo Finance（备用）
- TradingView（参考）
- Investing.com（补充）
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

import akshare as ak

from data_modules import GLOBAL_INDICES, GLOBAL_STOCKS, GLOBAL_ETF

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_global_catalog() -> tuple[dict[str, Any], ...]:
    """获取全球证券目录（索引、股票、ETF）。"""
    catalog: list[dict[str, Any]] = []

    # 添加全球指数
    for code, config in GLOBAL_INDICES.items():
        catalog.append({
            "code": code,
            "name": config["name"],
            "market": config["market"],
            "region": config["region"],
            "country": config["country"],
            "currency": config["currency"],
            "description": config["description"],
            "default_pe": config["default_pe"],
            "earnings_growth": config["earnings_growth"],
            "asset_type": config["asset_type"],
            "hot": config.get("hot", False),
            "yahoo_symbol": config.get("yahoo_symbol"),
            "tv_symbol": config.get("tv_symbol"),
            "source": "内置数据库",
        })

    # 添加全球股票
    for stock in GLOBAL_STOCKS:
        catalog.append({
            "code": stock["code"],
            "name": stock["name"],
            "market": stock["market"],
            "region": stock["region"],
            "country": stock["country"],
            "currency": stock["currency"],
            "description": stock["description"],
            "default_pe": stock["default_pe"],
            "earnings_growth": stock["earnings_growth"],
            "asset_type": stock["asset_type"],
            "hot": stock.get("hot", False),
            "yahoo_symbol": stock.get("yahoo_symbol"),
            "tv_symbol": stock.get("tv_symbol"),
            "source": "内置数据库",
        })

    # 添加全球ETF
    for etf in GLOBAL_ETF:
        catalog.append({
            "code": etf["code"],
            "name": etf["name"],
            "market": etf["market"],
            "region": etf["region"],
            "country": etf["country"],
            "currency": etf["currency"],
            "description": etf["description"],
            "default_pe": etf["default_pe"],
            "earnings_growth": etf["earnings_growth"],
            "asset_type": etf["asset_type"],
            "hot": etf.get("hot", False),
            "yahoo_symbol": etf.get("yahoo_symbol"),
            "tv_symbol": etf.get("tv_symbol"),
            "source": "内置数据库",
        })

    return tuple(catalog)


@lru_cache(maxsize=1)
def get_full_catalog() -> tuple[dict[str, Any], ...]:
    """获取完整目录（内置+AKShare动态数据）。"""
    global_catalog = list(get_global_catalog())
    seen = {item["code"] for item in global_catalog}

    # 添加A股股票
    try:
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            # 智能识别列名
            code_col = None
            name_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if "代码" in col_lower or "code" in col_lower:
                    code_col = col
                elif "名称" in col_lower or "name" in col_lower:
                    name_col = col

            if code_col and name_col:
                for _, row in df.iterrows():
                    code = str(row.get(code_col, "")).strip().zfill(6)
                    if code and code not in seen and len(code) == 6:
                        name = str(row.get(name_col, "")).strip()
                        global_catalog.append({
                            "code": code,
                            "name": name,
                            "market": "A股",
                            "region": "亚洲市场",
                            "country": "中国",
                            "currency": "CNY",
                            "description": "A股股票",
                            "default_pe": 16.0,
                            "earnings_growth": 6.0,
                            "asset_type": "stock",
                            "hot": False,
                            "source": "AKShare · 东方财富",
                        })
                        seen.add(code)
    except Exception as exc:
        logger.warning("A股股票目录加载失败: %s", exc)

    # 添加A股基金
    try:
        df = ak.fund_name_em()
        if df is not None and not df.empty:
            code_col = None
            name_col = None
            type_col = None
            py_col = None

            for col in df.columns:
                col_lower = str(col).lower()
                if "代码" in col_lower or "code" in col_lower:
                    code_col = col
                elif "名称" in col_lower or "name" in col_lower or "简称" in col_lower:
                    name_col = col
                elif "类型" in col_lower or "type" in col_lower:
                    type_col = col
                elif "拼音" in col_lower or "pinyin" in col_lower:
                    py_col = col

            if code_col and name_col:
                for _, row in df.iterrows():
                    code = str(row.get(code_col, "")).strip()
                    if code and code not in seen and len(code) == 6:
                        name = str(row.get(name_col, "")).strip()
                        fund_type = str(row.get(type_col, "基金")).strip() if type_col else "基金"
                        pinyin = str(row.get(py_col, "")).strip() if py_col else ""
                        global_catalog.append({
                            "code": code,
                            "name": name,
                            "market": "基金",
                            "region": "亚洲市场",
                            "country": "中国",
                            "currency": "CNY",
                            "description": fund_type,
                            "default_pe": 16.0,
                            "earnings_growth": 6.0,
                            "asset_type": "fund",
                            "fund_type": fund_type,
                            "pinyin": pinyin,
                            "hot": False,
                            "source": "AKShare · 东方财富基金",
                        })
                        seen.add(code)
    except Exception as exc:
        logger.warning("A股基金目录加载失败: %s", exc)

    return tuple(global_catalog)


def normalize_code(code: str) -> str:
    """标准化证券代码。"""
    code = str(code or "").upper().strip()
    if code.endswith((".HK", ".US", ".SH", ".SZ")):
        return code
    if code.isdigit() and len(code) < 6:
        return code.zfill(6)
    return code


def search_assets(
    query: str = "",
    region: str = "",
    country: str = "",
    market: str = "",
    asset_type: str = "",
    hot_only: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    """
    搜索全球证券。

    Args:
        query: 搜索关键词（代码、名称、拼音等）
        region: 市场区域（美洲市场、欧洲市场、亚洲市场）
        country: 国家（美国、中国、日本等）
        market: 市场（A股、美股、港股等）
        asset_type: 资产类型（stock、index、fund）
        hot_only: 是否仅显示热门标的
        limit: 返回数量限制

    Returns:
        搜索结果字典
    """
    query = query.strip().lower()
    region = region.strip()
    country = country.strip()
    market = market.strip()
    asset_type = asset_type.strip()

    results: list[dict[str, Any]] = []

    for item in get_full_catalog():
        # 热门筛选
        if hot_only and not item.get("hot", False):
            continue

        # 区域筛选
        if region and item.get("region") != region:
            continue

        # 国家筛选
        if country and item.get("country") != country:
            continue

        # 市场筛选
        if market and item.get("market") != market:
            continue

        # 资产类型筛选
        if asset_type and item.get("asset_type") != asset_type:
            continue

        # 关键词搜索
        if query:
            code = str(item.get("code", "")).lower()
            name = str(item.get("name", "")).lower()
            description = str(item.get("description", "")).lower()
            market_str = str(item.get("market", "")).lower()
            country_str = str(item.get("country", "")).lower()
            pinyin = str(item.get("pinyin", "")).lower()
            yahoo_symbol = str(item.get("yahoo_symbol", "")).lower()
            tv_symbol = str(item.get("tv_symbol", "")).lower()

            haystack = " ".join([
                code, name, description, market_str, country_str,
                pinyin, yahoo_symbol, tv_symbol
            ])

            # 精确匹配代码
            if query == code:
                results.insert(0, item)  # 精确匹配优先
                continue

            # 模糊匹配
            if query in haystack:
                results.append(item)
                continue
        else:
            # 无查询时返回所有符合条件的
            results.append(item)

    # 限制返回数量
    results = results[:limit]

    return {
        "query": query,
        "results": results,
        "count": len(results),
        "filters": {
            "region": region,
            "country": country,
            "market": market,
            "asset_type": asset_type,
            "hot_only": hot_only,
        },
        "source": "内置数据库 + AKShare",
    }


def get_suggestions(
    query: str = "",
    limit: int = 10,
    include_hot: bool = True,
) -> list[dict[str, Any]]:
    """
    获取搜索联想建议。

    Args:
        query: 搜索关键词
        limit: 返回数量
        include_hot: 是否包含热门推荐

    Returns:
        建议列表
    """
    query = query.strip().lower()
    suggestions: list[dict[str, Any]] = []

    # 如果有查询词，进行模糊搜索
    if query:
        search_result = search_assets(query=query, limit=limit)
        suggestions.extend(search_result["results"])

    # 如果查询词为空且需要热门推荐，返回热门标的
    if not query and include_hot:
        hot_result = search_assets(hot_only=True, limit=limit)
        suggestions.extend(hot_result["results"])

    return suggestions


def get_market_summary() -> dict[str, Any]:
    """获取市场概览（各区域标的数量）。"""
    catalog = get_full_catalog()

    summary = {
        "total": len(catalog),
        "regions": {},
        "countries": {},
        "markets": {},
        "asset_types": {},
    }

    for item in catalog:
        # 统计区域
        region = item.get("region", "其他")
        summary["regions"][region] = summary["regions"].get(region, 0) + 1

        # 统计国家
        country = item.get("country", "其他")
        summary["countries"][country] = summary["countries"].get(country, 0) + 1

        # 统计市场
        market = item.get("market", "其他")
        summary["markets"][market] = summary["markets"].get(market, 0) + 1

        # 统计资产类型
        asset_type = item.get("asset_type", "其他")
        summary["asset_types"][asset_type] = summary["asset_types"].get(asset_type, 0) + 1

    return summary


def resolve_symbol(code: str) -> dict[str, Any] | None:
    """
    根据代码解析证券信息。

    Args:
        code: 证券代码

    Returns:
        证券信息字典，未找到返回None
    """
    code = normalize_code(code)
    catalog = get_full_catalog()

    for item in catalog:
        if item.get("code") == code:
            return dict(item)

    # 未找到时返回基本信息
    return {
        "code": code,
        "name": code,
        "market": "自定义",
        "region": "其他",
        "country": "-",
        "currency": "-",
        "description": "自定义标的",
        "default_pe": 16.0,
        "earnings_growth": 6.0,
        "asset_type": "stock",
        "source": "用户输入",
    }


def get_hot_assets(region: str = "", limit: int = 10) -> list[dict[str, Any]]:
    """
    获取热门标的。

    Args:
        region: 市场区域过滤
        limit: 返回数量

    Returns:
        热门标的列表
    """
    search_result = search_assets(region=region, hot_only=True, limit=limit)
    return search_result["results"]


def get_region_assets(region: str, asset_type: str = "", limit: int = 20) -> list[dict[str, Any]]:
    """
    获取指定区域的所有标的。

    Args:
        region: 市场区域
        asset_type: 资产类型过滤
        limit: 返回数量限制

    Returns:
        标的列表
    """
    search_result = search_assets(
        region=region,
        asset_type=asset_type,
        limit=limit
    )
    return search_result["results"]
