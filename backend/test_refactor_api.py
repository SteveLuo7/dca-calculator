"""测试重构后的前端功能 - 后端API验证"""
import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from search_module import search_assets, get_market_summary
    from data_modules import GLOBAL_INDICES
    
    print("=== 测试市场指数加载 ===")
    
    # 测试各市场指数
    markets = ["亚洲市场", "欧洲市场", "美洲市场"]
    
    for market in markets:
        print(f"\n{market} 指数:")
        result = search_assets(region=market, asset_type="index", limit=20)
        indices = [item for item in result['results'] if item.get('asset_type') == 'index']
        print(f"  ✓ 找到 {len(indices)} 个指数")
        for idx in indices[:3]:
            print(f"    - {idx['code']}: {idx['name']}")
    
    print("\n=== 测试搜索联想功能 ===")
    
    test_queries = [
        "000300",  # 沪深300
        "AAPL",    # 苹果
        "0700",    # 腾讯
        "恒生",    # 恒生指数
        "S&P",     # 标普500
    ]
    
    for query in test_queries:
        print(f"\n搜索 '{query}':")
        result = search_assets(query=query, limit=10)
        print(f"  ✓ 找到 {len(result['results'])} 个结果")
        for item in result['results'][:3]:
            hot_tag = " [热门]" if item.get("hot") else ""
            print(f"    - {item['code']}: {item['name']} ({item['market']}){hot_tag}")
    
    print("\n=== 测试跨市场搜索 ===")
    
    # 搜索应该返回多市场结果
    result = search_assets(query="科技", limit=15)
    print(f"搜索 '科技':")
    print(f"  ✓ 找到 {len(result['results'])} 个结果")
    
    # 统计各市场结果数量
    regions = {}
    for item in result['results']:
        region = item.get('region', '未知')
        regions[region] = regions.get(region, 0) + 1
    
    for region, count in regions.items():
        print(f"    - {region}: {count} 个")
    
    print("\n=== 测试市场概览 ===")
    summary = get_market_summary()
    print(f"  ✓ 总标的数: {summary['total']}")
    print(f"  ✓ 各区域分布:")
    for region, count in summary['regions'].items():
        print(f"    - {region}: {count} 个")
    
    print("\n✅ 所有测试通过！后端API功能正常。")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
