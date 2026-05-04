#!/usr/bin/env python3
"""
测试美股和海外市场的数据获取功能
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    import akshare as ak
    import pandas as pd
    from backend.main import (
        fetch_quote_data,
        fetch_kline_data,
        resolve_security,
        INDEX_CONFIG,
    )
    from datetime import datetime
except ImportError as e:
    print(f"导入错误: {e}")
    print("请先安装依赖: pip install -r backend/requirements.txt")
    sys.exit(1)


def test_akshare_version():
    """测试AKShare版本"""
    print(f"\n{'='*60}")
    print("测试AKShare版本")
    print(f"{'='*60}")
    print(f"AKShare版本: {ak.__version__}")
    
    # 检查可用的海外市场函数
    overseas_funcs = [
        "index_global_hist",
        "stock_us_hist", 
        "stock_hk_hist",
        "index_global_spot",
        "stock_us_spot_em",
        "stock_hk_spot_em",
    ]
    
    print("\n海外市场API函数检查:")
    for func in overseas_funcs:
        status = "✓" if hasattr(ak, func) else "✗"
        print(f"  {status} ak.{func}")


def test_resolve_security():
    """测试证券解析"""
    print(f"\n{'='*60}")
    print("测试证券解析功能")
    print(f"{'='*60}")
    
    test_cases = [
        ("SPX", "标普500"),
        ("AAPL", "苹果"),
        ("0700.HK", "腾讯控股"),
        ("000300", "沪深300"),
    ]
    
    for code, expected_name in test_cases:
        security = resolve_security(code)
        print(f"\n代码: {code}")
        print(f"  名称: {security.get('name', 'N/A')}")
        print(f"  市场: {security.get('market', 'N/A')}")
        print(f"  类型: {security.get('asset_type', 'N/A')}")


def test_quote_data():
    """测试实时行情数据获取"""
    print(f"\n{'='*60}")
    print("测试实时行情数据获取")
    print(f"{'='*60}")
    
    test_codes = [
        "SPX",      # 美股指数
        "AAPL",     # 美股股票
        "NDX",      # 美股指数
        "0700.HK",  # 港股
        "000300",   # A股指数
    ]
    
    for code in test_codes:
        print(f"\n测试代码: {code}")
        try:
            quote = fetch_quote_data(code)
            print(f"  名称: {quote.get('name', 'N/A')}")
            print(f"  价格: {quote.get('price', 'N/A')}")
            print(f"  涨跌额: {quote.get('change', 'N/A')}")
            print(f"  涨跌幅: {quote.get('change_pct', 'N/A')}%")
            print(f"  数据源: {quote.get('source', 'N/A')}")
            print(f"  更新时间: {quote.get('updated_at', 'N/A')}")
        except Exception as e:
            print(f"  ✗ 获取失败: {e}")


def test_kline_data():
    """测试K线数据获取"""
    print(f"\n{'='*60}")
    print("测试K线数据获取")
    print(f"{'='*60}")
    
    test_cases = [
        ("SPX", "daily", "compact"),
        ("AAPL", "weekly", "all"),
        ("NDX", "monthly", "compact"),
        ("0700.HK", "daily", "all"),
    ]
    
    for code, period, range_ in test_cases:
        print(f"\n测试代码: {code} | 周期: {period} | 范围: {range_}")
        try:
            klines = fetch_kline_data(code, days=30, period=period, range_=range_)
            if klines:
                latest = klines[-1]
                print(f"  ✓ 获取到 {len(klines)} 条数据")
                print(f"  最新日期: {latest.get('time', 'N/A')}")
                print(f"  最新价格: {latest.get('close', 'N/A')}")
                print(f"  数据源: AKShare海外市场接口")
            else:
                print(f"  ✗ 未获取到数据")
        except Exception as e:
            print(f"  ✗ 获取失败: {e}")


def main():
    """运行所有测试"""
    print(f"\n{'#'*60}")
    print("# 美股和海外市场数据获取功能测试")
    print(f"#{'#'*60}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行测试
    test_akshare_version()
    test_resolve_security()
    test_quote_data()
    test_kline_data()
    
    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
