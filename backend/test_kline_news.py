"""测试K线和新闻数据获取功能"""
import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_kline_and_news():
    """测试K线和新闻数据获取"""
    try:
        from main import fetch_kline_data, fetch_stock_news
        
        print("=" * 60)
        print("K线数据和新闻功能测试")
        print("=" * 60)
        
        # 测试用例
        test_cases = [
            ("000300", "沪深300指数"),
            ("AAPL", "苹果股票"),
            ("0700.HK", "腾讯控股"),
            ("SPX", "标普500"),
        ]
        
        for code, name in test_cases:
            print(f"\n{'='*60}")
            print(f"测试: {name} ({code})")
            print(f"{'='*60}")
            
            # 测试K线数据
            print(f"\n1. K线数据测试:")
            klines = fetch_kline_data(code, days=10, period="daily")
            if klines:
                print(f"   ✓ 成功获取 {len(klines)} 条K线数据")
                print(f"   ✓ 数据源: {klines[0].get('data_source', '未知')}")
                print(f"   ✓ 最新价格: {klines[-1].get('close', 'N/A')}")
                print(f"   ✓ 最新日期: {klines[-1].get('date', 'N/A')}")
            else:
                print(f"   ✗ 未获取到K线数据")
            
            # 测试新闻数据
            print(f"\n2. 新闻数据测试:")
            news = fetch_stock_news(code, limit=3)
            if news:
                print(f"   ✓ 成功获取 {len(news)} 条新闻")
                for i, article in enumerate(news[:3], 1):
                    print(f"   {i}. {article.get('title', 'N/A')[:50]}...")
                    print(f"      来源: {article.get('source', 'N/A')}")
            else:
                print(f"   ✗ 未获取到新闻数据")
        
        print(f"\n{'='*60}")
        print("测试完成！")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_kline_and_news()
