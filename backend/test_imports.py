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
    
    print("\n所有测试通过！可以启动服务器了。")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    print("请确保 data_modules.py 和 search_module.py 在当前目录下")
    sys.exit(1)
except Exception as e:
    print(f"✗ 测试失败: {e}")
    sys.exit(1)
