"""本地启动脚本 - 用于测试修复后的代码"""
import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # 测试导入
    print("正在测试模块导入...")
    from data_modules import GLOBAL_INDICES, GLOBAL_STOCKS, GLOBAL_ETF
    from search_module import get_global_catalog, search_assets
    print(f"✓ 成功导入 data_modules")
    print(f"✓ 成功导入 search_module")
    print(f"✓ 全球指数数量: {len(GLOBAL_INDICES)}")
    print(f"✓ 全球股票数量: {len(GLOBAL_STOCKS)}")
    print(f"✓ 全球ETF数量: {len(GLOBAL_ETF)}")
    
    # 测试搜索功能
    print("\n正在测试搜索功能...")
    result = search_assets(query="AAPL", limit=5)
    print(f"✓ 搜索 'AAPL' 找到 {len(result['results'])} 个结果")
    
    # 测试市场概览
    from search_module import get_market_summary
    summary = get_market_summary()
    print(f"✓ 市场概览: {summary}")
    
    # 测试K线数据获取
    print("\n正在测试K线数据获取...")
    from main import fetch_kline_data
    
    # 测试A股指数
    klines_000300 = fetch_kline_data("000300", days=10, period="daily")
    print(f"✓ 沪深300 K线数据: {len(klines_000300)} 条")
    if klines_000300:
        print(f"  数据源: {klines_000300[0].get('data_source', '未知')}")
    
    # 测试美股股票
    klines_aapl = fetch_kline_data("AAPL", days=10, period="daily")
    print(f"✓ 苹果(AAPL) K线数据: {len(klines_aapl)} 条")
    if klines_aapl:
        print(f"  数据源: {klines_aapl[0].get('data_source', '未知')}")
        
    # 测试港股
    klines_hk = fetch_kline_data("0700.HK", days=10, period="daily")
    print(f"✓ 腾讯(0700.HK) K线数据: {len(klines_hk)} 条")
    if klines_hk:
        print(f"  数据源: {klines_hk[0].get('data_source', '未知')}")
    
    # 测试新闻获取
    print("\n正在测试新闻获取...")
    from main import fetch_stock_news
    
    # 测试A股新闻
    news_000300 = fetch_stock_news("000300", limit=5)
    print(f"✓ 沪深300 新闻: {len(news_000300)} 条")
    
    # 测试美股新闻
    news_aapl = fetch_stock_news("AAPL", limit=5)
    print(f"✓ 苹果(AAPL) 新闻: {len(news_aapl)} 条")
    
    print("\n✅ 所有测试通过！可以启动服务器了。")
    print("\n启动命令:")
    print("  uvicorn main:app --reload --port 8000")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    print("请确保 data_modules.py 和 search_module.py 在当前目录下")
    sys.exit(1)
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
