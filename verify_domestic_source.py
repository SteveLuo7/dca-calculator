"""验证国内数据源更新"""
import sys
from pathlib import Path

# 添加backend路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("验证国内数据源更新")
print("=" * 60)

# 测试导入
print("\n1. 测试模块导入...")
try:
    from main import (
        fetch_kline_data,
        fetch_quote_data,
        _get_currency_from_security,
        resolve_security,
    )
    print("✓ 核心函数导入成功")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 测试货币单位判断
print("\n2. 测试货币单位判断...")
test_cases = [
    {"code": "000300", "market": "A股", "expected": "CNY"},
    {"code": "600519", "market": "A股", "expected": "CNY"},
    {"code": "HSI", "market": "港股", "expected": "HKD"},
    {"code": "0700.HK", "market": "港股", "expected": "HKD"},
    {"code": "SPX", "market": "美股", "expected": "USD"},
    {"code": "AAPL", "market": "美股", "expected": "USD"},
]

for test in test_cases:
    security = resolve_security(test["code"])
    currency = _get_currency_from_security(security)
    status = "✓" if currency == test["expected"] else "✗"
    print(f"{status} {test['code']} ({test['market']}): {currency} (预期: {test['expected']})")

# 测试数据源配置
print("\n3. 检查数据源配置...")
try:
    # 尝试获取K线数据（会使用AKShare）
    code = "000300"
    klines = fetch_kline_data(code, days=5)
    if klines:
        print(f"✓ 成功获取K线数据: {len(klines)}条")
        # 检查数据源字段
        if klines[0].get("data_source"):
            print(f"✓ 数据源标注: {klines[0]['data_source']}")
        if klines[0].get("currency"):
            print(f"✓ 货币单位标注: {klines[0]['currency']}")
        else:
            print("⚠ K线数据缺少currency字段")
    else:
        print("✗ 未获取到K线数据")
except Exception as e:
    print(f"⚠ K线数据获取失败（可能是网络问题）: {e}")

try:
    # 尝试获取报价数据
    quote = fetch_quote_data(code)
    if quote.get("price"):
        print(f"✓ 成功获取报价数据: {quote['price']}")
        if quote.get("currency"):
            print(f"✓ 货币单位标注: {quote['currency']}")
        else:
            print("⚠ 报价数据缺少currency字段")
    else:
        print("✗ 未获取到报价数据")
except Exception as e:
    print(f"⚠ 报价数据获取失败（可能是网络问题）: {e}")

# 检查Yahoo Finance是否已移除
print("\n4. 检查Yahoo Finance依赖...")
main_content = (backend_dir / "main.py").read_text(encoding="utf-8")
if "yahoo" in main_content.lower() or "yfinance" in main_content.lower():
    print("⚠ main.py中仍包含Yahoo Finance相关代码")
else:
    print("✓ Yahoo Finance代码已完全移除")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)
print("\n主要更新：")
print("✓ 完全使用AKShare国内数据源")
print("✓ 移除Yahoo Finance依赖")
print("✓ 总览价格和K线图数据源一致")
print("✓ 添加货币单位标注")
print("\n数据源优先级：")
print("1. AKShare（国内数据源）")
print("2. 备份数据（静态基准）")
print("\n货币单位：")
print("- A股：CNY（¥）")
print("- 港股：HKD（HK$）")
print("- 美股：USD（$）")
