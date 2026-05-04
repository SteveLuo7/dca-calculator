#!/usr/bin/env python3
"""
测试后端财报API是否可用
"""
import requests
import json

# 测试本地API
local_api = "http://localhost:8000"
# 测试部署API
deployed_api = "https://dca-calculator-production.up.railway.app"

test_code = "600519"

def test_api(api_url):
    """测试API端点"""
    url = f"{api_url}/api/financial_reports/{test_code}"
    print(f"\n{'='*60}")
    print(f"测试 API: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 成功！获取到财报数据:")
            print(f"  - 代码: {data.get('code')}")
            print(f"  - 名称: {data.get('name')}")
            print(f"  - 财报数量: {data.get('count')}")
            print(f"  - 数据源: {data.get('source')}")
            if data.get('reports'):
                print(f"\n  财报数据预览:")
                for report in data.get('reports', [])[:2]:
                    print(f"    - {report.get('year')}年: ROE={report.get('roe')}, EPS={report.get('eps')}")
            return True
        else:
            print(f"\n✗ 失败！状态码: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ 连接失败！无法连接到 {api_url}")
        return False
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return False

if __name__ == "__main__":
    print("测试财报API端点")
    
    # 测试本地API
    local_ok = test_api(local_api)
    
    # 测试部署API
    deployed_ok = test_api(deployed_api)
    
    print("\n" + "="*60)
    print("测试总结:")
    print("="*60)
    print(f"本地API ({local_api}): {'✓ 可用' if local_ok else '✗ 不可用'}")
    print(f"部署API ({deployed_api}): {'✓ 可用' if deployed_ok else '✗ 不可用'}")
    
    if not deployed_ok and local_ok:
        print("\n⚠️  问题诊断:")
        print("  本地API可用但部署API不可用")
        print("  这意味着Railway部署没有包含最新的后端代码")
        print("\n解决方案:")
        print("  1. 将最新代码推送到GitHub")
        print("  2. Railway会自动重新部署")
        print("  3. 或者手动在Railway控制台触发重新部署")
    elif not deployed_ok and not local_ok:
        print("\n⚠️  问题诊断:")
        print("  本地和部署API都不可用")
        print("  可能的原因:")
        print("  - 后端服务未启动")
        print("  - 代码有错误")
        print("  - 依赖未安装")
