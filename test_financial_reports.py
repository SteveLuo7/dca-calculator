#!/usr/bin/env python
"""测试财报信息API功能"""
import sys
sys.path.insert(0, 'backend')

from main import fetch_financial_reports, normalize_code

def test_financial_reports():
    """测试财报数据获取"""
    print("=" * 60)
    print("测试财报信息功能")
    print("=" * 60)

    test_cases = [
        "600519",  # 贵州茅台
        "000001",  # 平安银行
        "510300",  # 沪深300 ETF
        "000300",  # 沪深300指数
    ]

    for code in test_cases:
        print(f"\n测试代码: {code}")
        print("-" * 40)

        try:
            reports = fetch_financial_reports(code, limit=3)

            if reports:
                print(f"✓ 成功获取 {len(reports)} 条财报记录")
                for i, report in enumerate(reports, 1):
                    print(f"\n  记录 {i}:")
                    print(f"    年份: {report.get('year', '-')}")
                    print(f"    类型: {report.get('report_type', '-')}")
                    if report.get('fund_type'):
                        print(f"    类型说明: {report['fund_type']}")
                        print(f"    备注: {report.get('note', '')}")
                    else:
                        if report.get('roe') is not None:
                            print(f"    ROE: {report.get('roe')}%")
                        if report.get('roa') is not None:
                            print(f"    ROA: {report.get('roa')}%")
                        if report.get('eps') is not None:
                            print(f"    EPS: {report.get('eps')}")
                        if report.get('revenue') is not None:
                            print(f"    营业收入: {report.get('revenue')}")
                        if report.get('net_profit') is not None:
                            print(f"    净利润: {report.get('net_profit')}")
                        if report.get('total_assets') is not None:
                            print(f"    总资产: {report.get('total_assets')}")
                    print(f"    来源: {report.get('source', '-')}")
            else:
                print("✗ 未获取到财报数据（可能是基金/指数/海外标的）")
        except Exception as e:
            print(f"✗ 获取失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_financial_reports()
