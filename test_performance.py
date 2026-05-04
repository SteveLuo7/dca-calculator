"""测试性能优化效果"""
import time
import requests

BASE_URL = "http://localhost:8000"

test_codes = [
    "000300",  # 沪深300
    "SPX",     # 标普500
    "HSI",     # 恒生指数
]

def test_endpoint_performance(endpoint, code, description):
    """测试单个接口的性能"""
    print(f"\n{description} ({code})")

    # 首次请求
    start = time.time()
    response = requests.get(f"{BASE_URL}{endpoint}{code}")
    first_time = time.time() - start
    print(f"  首次加载: {first_time:.3f}秒")

    # 缓存命中请求
    start = time.time()
    response = requests.get(f"{BASE_URL}{endpoint}{code}")
    cached_time = time.time() - start
    print(f"  缓存加载: {cached_time:.3f}秒")

    improvement = ((first_time - cached_time) / first_time) * 100
    print(f"  性能提升: {improvement:.1f}%")

    return response.json()

def test_combined_scenario():
    """测试综合场景"""
    print("\n" + "="*60)
    print("综合场景测试：模拟用户实际使用流程")
    print("="*60)

    code = "000300"

    # 1. 总览数据加载
    print("\n[1] 加载总览数据")
    quote_data = test_endpoint_performance("/api/quote/", code, "总览")

    # 2. K线图加载（首次）
    print("\n[2] 加载K线图（首次）")
    kline_data = test_endpoint_performance("/api/kline/", code, "K线图")

    # 3. PE数据加载
    print("\n[3] 加载PE数据")
    pe_data = test_endpoint_performance("/api/pe/", code, "PE估值")

    # 4. 重复加载K线（应该命中缓存）
    print("\n[4] 重复加载K线图（测试缓存）")
    kline_data_cached = test_endpoint_performance("/api/kline/", code, "K线图（缓存）")

    # 5. 再次加载总览（应该使用K线缓存）
    print("\n[5] 再次加载总览（测试K线缓存）")
    quote_data_cached = test_endpoint_performance("/api/quote/", code, "总览（缓存）")

def main():
    print("\n" + "="*60)
    print("性能优化测试")
    print("="*60)

    # 测试各个接口
    for code in test_codes:
        print("\n" + "-"*60)
        print(f"测试标的: {code}")
        print("-"*60)

        try:
            test_endpoint_performance("/api/quote/", code, "总览")
            test_endpoint_performance("/api/kline/", code, "K线图")
            test_endpoint_performance("/api/pe/", code, "PE估值")
        except Exception as e:
            print(f"  错误: {e}")

    # 综合场景测试
    test_combined_scenario()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()
