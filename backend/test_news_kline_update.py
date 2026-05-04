"""测试新闻源和K线数据源更新

验证：
1. A股新闻是否来自东方财富直接新闻
2. 海外市场新闻是否优先使用大陆可访问的源
3. K线数据是否优先使用AKShare
4. 数据源标注是否正确
"""

import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from main import fetch_stock_news, fetch_kline_data, fetch_quote_data


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_a_share_news():
    """测试A股新闻"""
    print_section("1. A股新闻测试 (000300 - 沪深300)")
    
    articles = fetch_stock_news("000300", limit=8)
    
    print(f"✓ 获取到 {len(articles)} 条新闻")
    
    # 检查前几条新闻来源
    print("\n新闻来源分析:")
    sources_count = {}
    for i, article in enumerate(articles[:5], 1):
        source = article.get("source", "未知")
        sources_count[source] = sources_count.get(source, 0) + 1
        title = article.get("title", "")
        print(f"  {i}. [{source}] {title[:50]}...")
    
    print("\n来源统计:")
    for source, count in sources_count.items():
        print(f"  - {source}: {count} 条")
    
    # 检查是否包含东方财富直接新闻
    has_eastmoney_direct = any("东方财富" in s and "搜索" not in s for s in sources_count.keys())
    if has_eastmoney_direct:
        print("\n✓ 包含东方财富直接新闻（符合预期）")
    else:
        print("\n⚠ 未找到东方财富直接新闻，可能需要检查")
    
    # 检查是否包含真实新闻链接
    real_news_count = sum(1 for a in articles if "http" in a.get("url", "") and "search" not in a.get("url", "").lower())
    print(f"✓ 包含 {real_news_count} 条真实新闻链接")
    
    return articles


def test_overseas_news():
    """测试海外市场新闻"""
    print_section("2. 海外市场新闻测试 (AAPL - 苹果)")
    
    articles = fetch_stock_news("AAPL", limit=6)
    
    print(f"✓ 获取到 {len(articles)} 条新闻")
    
    # 检查新闻来源
    print("\n新闻来源:")
    sources = set()
    for i, article in enumerate(articles[:5], 1):
        source = article.get("source", "未知")
        sources.add(source)
        title = article.get("title", "")
        print(f"  {i}. [{source}] {title[:50]}...")
    
    # 检查是否使用大陆可访问的源
    mainland_sources = ["财联社", "同花顺", "新浪财经", "百度"]
    has_mainland = any(s in mainland_sources for s in sources)
    
    if has_mainland:
        print("\n✓ 包含大陆可访问的新闻源（符合预期）")
    else:
        print("\n⚠ 未找到大陆可访问的新闻源")
    
    # 检查是否有Google搜索（应该已被替换）
    has_google = any("Google" in s for s in sources)
    if has_google:
        print("\n⚠ 发现Google搜索（应已被百度搜索替换）")
    else:
        print("\n✓ 未使用Google搜索（已替换为百度搜索）")
    
    return articles


def test_a_share_kline():
    """测试A股K线数据"""
    print_section("3. A股K线数据测试 (000300 - 沪深300)")
    
    klines = fetch_kline_data("000300", days=5, period="daily")
    
    if not klines:
        print("✗ 未获取到K线数据")
        return []
    
    print(f"✓ 获取到 {len(klines)} 条K线数据")
    
    # 检查数据源
    data_source = klines[0].get("data_source", "未知")
    print(f"✓ 数据源: {data_source}")
    
    if "AKShare" in data_source:
        print("✓ 使用AKShare数据源（符合预期）")
    elif "Yahoo" in data_source:
        print("⚠ 使用Yahoo Finance（AKShare可能失败）")
    else:
        print(f"⚠ 使用其他数据源: {data_source}")
    
    # 显示最近几天数据
    print("\n最近5天数据:")
    for kline in klines[-5:]:
        print(f"  {kline['time']}: 开盘={kline['open']:.2f}, "
              f"收盘={kline['close']:.2f}, "
              f"涨跌={kline.get('pct_chg', 0):.2f}%")
    
    return klines


def test_overseas_kline():
    """测试海外市场K线数据"""
    print_section("4. 海外市场K线数据测试 (^GSPC - 标普500)")
    
    klines = fetch_kline_data("^GSPC", days=5, period="daily")
    
    if not klines:
        print("✗ 未获取到K线数据")
        return []
    
    print(f"✓ 获取到 {len(klines)} 条K线数据")
    
    # 检查数据源
    data_source = klines[0].get("data_source", "未知")
    print(f"✓ 数据源: {data_source}")
    
    if "AKShare" in data_source:
        print("✓ 使用AKShare数据源（符合预期）")
    elif "Yahoo" in data_source:
        print("✓ 使用Yahoo Finance作为辅助（符合预期）")
    else:
        print(f"⚠ 使用其他数据源: {data_source}")
    
    # 显示最近几天数据
    print("\n最近5天数据:")
    for kline in klines[-5:]:
        print(f"  {kline['time']}: 开盘={kline['open']:.2f}, "
              f"收盘={kline['close']:.2f}, "
              f"涨跌={kline.get('pct_chg', 0):.2f}%")
    
    return klines


def test_hk_stock():
    """测试港股"""
    print_section("5. 港股测试 (0700.HK - 腾讯)")
    
    # 测试新闻
    print("\n新闻测试:")
    articles = fetch_stock_news("0700", limit=3)
    print(f"✓ 获取到 {len(articles)} 条新闻")
    for i, article in enumerate(articles[:3], 1):
        print(f"  {i}. [{article.get('source', '未知')}] {article.get('title', '')[:40]}...")
    
    # 测试K线
    print("\nK线测试:")
    klines = fetch_kline_data("0700", days=3, period="daily")
    if klines:
        print(f"✓ 获取到 {len(klines)} 条K线数据")
        print(f"✓ 数据源: {klines[0].get('data_source', '未知')}")
    else:
        print("✗ 未获取到K线数据")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("  新闻源和K线数据源更新测试")
    print("=" * 60)
    
    try:
        # 运行各项测试
        test_a_share_news()
        test_overseas_news()
        test_a_share_kline()
        test_overseas_kline()
        test_hk_stock()
        
        print_section("测试完成")
        print("\n✓ 所有测试已执行")
        print("\n请检查上述输出，确认：")
        print("  1. A股新闻优先使用东方财富直接新闻")
        print("  2. 海外市场新闻使用大陆可访问的源（财联社、同花顺等）")
        print("  3. K线数据优先使用AKShare，Yahoo Finance作为辅助")
        print("  4. 数据源标注正确")
        
    except Exception as e:
        print(f"\n✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
