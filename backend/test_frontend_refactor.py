"""
测试重构后的前端功能：
1. 市场指数选择模块（三个标签页）
2. 搜索功能
"""
import requests
import json

API_BASE = "http://localhost:8000"


def test_market_indices():
    """测试各市场指数加载"""
    print("=== 测试市场指数加载 ===")

    markets = [
        ("亚洲市场", "asia"),
        ("欧洲市场", "europe"),
        ("美洲市场", "americas")
    ]

    for market_name, market_key in markets:
        print(f"\n测试 {market_name} 指数:")
        try:
            res = requests.get(
                f"{API_BASE}/api/search",
                params={
                    "region": market_name,
                    "asset_type": "index",
                    "limit": 30
                },
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                indices = [item for item in data.get("results", []) if item.get("asset_type") == "index"]
                print(f"  ✓ 找到 {len(indices)} 个指数")
                for idx in indices[:3]:  # 显示前3个
                    print(f"    - {idx['code']}: {idx['name']}")
            else:
                print(f"  ✗ API请求失败: {res.status_code}")
        except Exception as e:
            print(f"  ✗ 请求异常: {e}")


def test_search_suggestions():
    """测试搜索联想功能"""
    print("\n\n=== 测试搜索联想功能 ===")

    test_queries = [
        "000300",  # 沪深300
        "AAPL",    # 苹果
        "0700",    # 腾讯
        "S&P",     # 标普500
        "恒生",    # 恒生指数
        "科技",    # 科技相关
        "ETF",     # ETF
    ]

    for query in test_queries:
        print(f"\n搜索 '{query}':")
        try:
            res = requests.get(
                f"{API_BASE}/api/search",
                params={"q": query, "limit": 10},
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                print(f"  ✓ 找到 {len(results)} 个结果")
                for item in results[:3]:
                    hot_tag = " [热门]" if item.get("hot") else ""
                    print(f"    - {item['code']}: {item['name']} ({item['market']}){hot_tag}")
            else:
                print(f"  ✗ API请求失败: {res.status_code}")
        except Exception as e:
            print(f"  ✗ 请求异常: {e}")


def test_cross_market_search():
    """测试跨市场搜索"""
    print("\n\n=== 测试跨市场搜索 ===")

    test_cases = [
        ("特斯拉", ["美洲市场"]),
        ("腾讯", ["亚洲市场"]),
        ("大众", ["欧洲市场"]),
        ("指数", None),  # 应该返回所有市场的指数
    ]

    for query, expected_regions in test_cases:
        print(f"\n搜索 '{query}':")
        try:
            res = requests.get(
                f"{API_BASE}/api/search",
                params={"q": query, "limit": 15},
                timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                regions = set(item.get("region") for item in results)

                print(f"  ✓ 找到 {len(results)} 个结果")
                print(f"  ✓ 涉及市场: {', '.join(regions) if regions else '无'}")

                for item in results[:5]:
                    print(f"    - [{item.get('region', '未知')}] {item['code']}: {item['name']}")
            else:
                print(f"  ✗ API请求失败: {res.status_code}")
        except Exception as e:
            print(f"  ✗ 请求异常: {e}")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("前端重构功能测试")
    print("=" * 50)

    test_market_indices()
    test_search_suggestions()
    test_cross_market_search()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
