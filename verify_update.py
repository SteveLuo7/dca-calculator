"""快速验证数据源更新

简单测试新闻和K线数据源是否正确配置
"""

import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from main import fetch_stock_news, fetch_kline_data

    print("=" * 60)
    print("  数据源更新验证")
    print("=" * 60)

    # 测试1: A股新闻
    print("\n[1] 测试A股新闻 (000300)...")
    try:
        articles = fetch_stock_news("000300", limit=3)
        print(f"✓ 获取到 {len(articles)} 条新闻")
        if articles:
            source = articles[0].get("source", "未知")
            print(f"✓ 首条新闻来源: {source}")
            has_direct_url = "http" in articles[0].get("url", "") and "search" not in articles[0].get("url", "").lower()
            if has_direct_url:
                print("✓ 包含直接新闻链接")
            else:
                print("⚠ 可能是搜索入口")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 测试2: 海外市场新闻
    print("\n[2] 测试海外市场新闻 (AAPL)...")
    try:
        articles = fetch_stock_news("AAPL", limit=3)
        print(f"✓ 获取到 {len(articles)} 条新闻")
        if articles:
            sources = [a.get("source", "未知") for a in articles]
            print(f"✓ 新闻来源: {', '.join(sources[:3])}")
            has_google = any("Google" in s for s in sources)
            if not has_google:
                print("✓ 未使用Google搜索（已替换为百度）")
            else:
                print("⚠ 仍在使用Google搜索")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 测试3: A股K线
    print("\n[3] 测试A股K线 (000300)...")
    try:
        klines = fetch_kline_data("000300", days=3, period="daily")
        if klines:
            print(f"✓ 获取到 {len(klines)} 条K线数据")
            source = klines[0].get("data_source", "未知")
            print(f"✓ 数据源: {source}")
            if "AKShare" in source:
                print("✓ 使用AKShare数据源")
            else:
                print(f"⚠ 使用其他数据源: {source}")
        else:
            print("⚠ 未获取到K线数据")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    # 测试4: 海外市场K线
    print("\n[4] 测试海外市场K线 (^GSPC)...")
    try:
        klines = fetch_kline_data("^GSPC", days=3, period="daily")
        if klines:
            print(f"✓ 获取到 {len(klines)} 条K线数据")
            source = klines[0].get("data_source", "未知")
            print(f"✓ 数据源: {source}")
            if "AKShare" in source or "Yahoo" in source:
                print("✓ 使用预期数据源（AKShare或Yahoo）")
            else:
                print(f"⚠ 使用其他数据源: {source}")
        else:
            print("⚠ 未获取到K线数据")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

    print("\n" + "=" * 60)
    print("  验证完成")
    print("=" * 60)
    print("\n请检查上述输出，确认数据源配置正确。")
    print("\n如需详细测试，请运行：")
    print("  cd backend")
    print("  python test_news_kline_update.py")

except ImportError as e:
    print(f"✗ 导入失败，请确保在项目根目录运行: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
