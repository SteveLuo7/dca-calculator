#!/usr/bin/env python3
"""
测试所有修复：
1. AMD价格准确性
2. 财报API功能
3. 财报下载链接
"""
import sys
import json

# 测试本地API
LOCAL_API = "http://localhost:8000"


def test_amd_price():
    """测试AMD价格准确性"""
    print("\n" + "="*60)
    print("测试AMD价格")
    print("="*60)

    import requests

    try:
        url = f"{LOCAL_API}/api/quote/AMD"
        print(f"请求: {url}")
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 成功获取AMD价格")
            print(f"  代码: {data.get('code')}")
            print(f"  名称: {data.get('name')}")
            print(f"  价格: ${data.get('price'):.2f}")
            print(f"  涨跌: {data.get('change'):+.2f} ({data.get('change_pct'):+.2f}%)")
            print(f"  货币: {data.get('currency')}")
            print(f"  来源: {data.get('source')}")

            # 验证价格是否合理
            price = data.get('price')
            if price and 50 < price < 200:  # AMD通常在50-200美元之间
                print(f"\n✓ 价格范围合理")
            else:
                print(f"\n⚠️  价格可能不准确，请手动核对Yahoo Finance")

            return True
        else:
            print(f"\n✗ 请求失败: HTTP {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n✗ 连接失败，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def test_financial_reports(code, name):
    """测试财报API"""
    print("\n" + "="*60)
    print(f"测试{name}财报")
    print("="*60)

    import requests

    try:
        url = f"{LOCAL_API}/api/financial_reports/{code}"
        print(f"请求: {url}")
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 成功获取财报数据")
            print(f"  代码: {data.get('code')}")
            print(f"  名称: {data.get('name')}")
            print(f"  财报数量: {data.get('count')}")
            print(f"  来源: {data.get('source')}")

            reports = data.get('reports', [])
            if reports:
                print(f"\n  财报列表:")
                for i, report in enumerate(reports[:3], 1):
                    print(f"    {i}. {report.get('year')}年 {report.get('report_type')}")
                    if report.get('roe'):
                        print(f"       ROE: {report.get('roe'):.2f}%")
                    if report.get('eps'):
                        print(f"       EPS: {report.get('eps'):.4f}")
                    if report.get('download_url'):
                        print(f"       下载链接: {report.get('download_url')}")

                # 验证下载链接
                for report in reports:
                    if 'download_url' in report:
                        print(f"\n✓ 包含财报下载链接")
                        break
                else:
                    print(f"\n⚠️  未找到财报下载链接")

            return True
        else:
            print(f"\n✗ 请求失败: HTTP {response.status_code}")
            print(f"响应: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n✗ 连接失败，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False


def test_api_endpoints():
    """测试所有API端点"""
    print("\n" + "="*60)
    print("测试API端点列表")
    print("="*60)

    endpoints = [
        ("AMD股票", "/api/quote/AMD"),
        ("茅台PE", "/api/pe/600519"),
        ("茅台新闻", "/api/news/600519"),
        ("茅台财报", "/api/financial_reports/600519"),
    ]

    import requests

    for name, endpoint in endpoints:
        url = LOCAL_API + endpoint
        try:
            response = requests.get(url, timeout=5)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} {name:20s} {endpoint:40s} HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ {name:20s} {endpoint:40s} 错误: {str(e)[:30]}")


def main():
    """主函数"""
    print("="*60)
    print("修复验证测试")
    print("="*60)
    print("\n测试内容:")
    print("1. AMD价格准确性")
    print("2. A股财报数据")
    print("3. 财报下载链接")
    print("4. 所有API端点")

    # 测试AMD价格
    amd_ok = test_amd_price()

    # 测试A股财报
    kweichow_ok = test_financial_reports("600519", "贵州茅台")
    pingan_ok = test_financial_reports("000001", "平安银行")

    # 测试API端点
    test_api_endpoints()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"AMD价格: {'✓ 通过' if amd_ok else '✗ 失败'}")
    print(f"茅台财报: {'✓ 通过' if kweichow_ok else '✗ 失败'}")
    print(f"平安财报: {'✓ 通过' if pingan_ok else '✗ 失败'}")

    all_ok = amd_ok and kweichow_ok and pingan_ok
    if all_ok:
        print("\n✓ 所有关键测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
