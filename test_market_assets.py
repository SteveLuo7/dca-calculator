#!/usr/bin/env python3
"""
测试市场资产API - 验证按地区和资产类型筛选股票和基金
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from search_module import search_assets


def test_market_stocks_and_funds():
    """测试各市场的股票和基金数据"""

    markets = [
        {"name": "亚洲市场", "region": "亚洲市场"},
        {"name": "欧洲市场", "region": "欧洲市场"},
        {"name": "美洲市场", "region": "美洲市场"},
    ]

    asset_types = ["stock", "fund"]

    print("=" * 80)
    print("测试市场资产API")
    print("=" * 80)

    for market in markets:
        print(f"\n{'=' * 80}")
        print(f"市场: {market['name']}")
        print(f"{'=' * 80}")

        for asset_type in asset_types:
            asset_name = "股票" if asset_type == "stock" else "基金"

            # 搜索该地区的股票或基金
            result = search_assets(
                region=market["region"],
                asset_type=asset_type,
                limit=20
            )

            print(f"\n{asset_name} (共{result['count']}个):")
            print("-" * 60)

            if result['count'] == 0:
                print(f"  暂无{asset_name}数据")
            else:
                for item in result['results'][:10]:  # 只显示前10个
                    print(f"  {item['code']:12} {item['name']:20} {item['market']:15}")

                if result['count'] > 10:
                    print(f"  ... 还有{result['count'] - 10}个")

    print(f"\n{'=' * 80}")
    print("测试完成!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    test_market_stocks_and_funds()
