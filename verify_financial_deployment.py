#!/usr/bin/env python3
"""
验证财报功能部署状态
"""
import sys
import os

def check_backend_code():
    """检查后端代码是否包含财报功能"""
    print("\n" + "="*60)
    print("检查后端代码")
    print("="*60)

    main_py_path = "backend/main.py"
    if not os.path.exists(main_py_path):
        print(f"✗ 未找到 {main_py_path}")
        return False

    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("fetch_financial_reports 函数", "def fetch_financial_reports"),
        ("/api/financial_reports 端点", '@app.get("/api/financial_reports/{code}")'),
        ("get_financial_reports 函数", "def get_financial_reports"),
    ]

    all_ok = True
    for name, pattern in checks:
        if pattern in content:
            print(f"✓ {name}")
        else:
            print(f"✗ {name} - 未找到")
            all_ok = False

    return all_ok


def check_frontend_code():
    """检查前端代码是否包含财报功能"""
    print("\n" + "="*60)
    print("检查前端代码")
    print("="*60)

    index_html_path = "index.html"
    if not os.path.exists(index_html_path):
        print(f"✗ 未找到 {index_html_path}")
        return False

    with open(index_html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("财报面板 HTML", 'id="financialPanel"'),
        ("财报列表容器", 'id="financialList"'),
        ("fetchFinancialReports 函数", "async function fetchFinancialReports"),
        ("renderFinancialReports 函数", "function renderFinancialReports"),
        ("在 refreshSelectedCode 中调用", "fetchFinancialReports(code)"),
        ("财报样式 .financial-item", ".financial-item"),
    ]

    all_ok = True
    for name, pattern in checks:
        if pattern in content:
            print(f"✓ {name}")
        else:
            print(f"✗ {name} - 未找到")
            all_ok = False

    return all_ok


def check_dockerfile():
    """检查 Dockerfile 配置"""
    print("\n" + "="*60)
    print("检查 Dockerfile")
    print("="*60)

    dockerfile_path = "Dockerfile"
    if not os.path.exists(dockerfile_path):
        print(f"✗ 未找到 {dockerfile_path}")
        return False

    with open(dockerfile_path, 'r', encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("复制后端文件", "COPY backend/*.py"),
        ("复制依赖文件", "COPY backend/requirements.txt"),
        ("安装依赖", "RUN pip install"),
        ("启动命令", "CMD uvicorn main:app"),
    ]

    all_ok = True
    for name, pattern in checks:
        if pattern in content:
            print(f"✓ {name}")
        else:
            print(f"✗ {name} - 未找到")
            all_ok = False

    return all_ok


def check_git_status():
    """检查 Git 状态"""
    print("\n" + "="*60)
    print("检查 Git 状态")
    print("="*60)

    import subprocess

    try:
        # 检查是否有未提交的修改
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        if result.returncode != 0:
            print("⚠️  Git 仓库检查失败")
            return None

        if result.stdout.strip():
            print("⚠️  有未提交的修改:")
            print(result.stdout)
            return False
        else:
            print("✓ 工作目录干净，所有修改已提交")

        # 检查是否已推送到远程
        result = subprocess.run(
            ['git', 'status', '-sb'],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        if 'ahead' in result.stdout:
            print("⚠️  有未推送的提交")
            return False
        elif 'up to date' in result.stdout.lower():
            print("✓ 本地与远程同步")
            return True
        else:
            print("⚠️  无法确定同步状态")
            return None

    except FileNotFoundError:
        print("⚠️  Git 未安装或不在 PATH 中")
        return None


def print_next_steps():
    """打印下一步操作"""
    print("\n" + "="*60)
    print("下一步操作")
    print("="*60)
    print("""
如果检查全部通过：
1. 确保代码已推送到 GitHub
   git push origin main

2. 在 Railway 控制台触发重新部署
   - 登录 https://railway.app
   - 进入 dca-calculator 项目
   - 点击 "Redeploy" 按钮

3. 等待部署完成（约 2-3 分钟）

4. 验证部署
   curl https://dca-calculator-production.up.railway.app/api/financial_reports/600519

5. 刷新前端页面并测试

如果检查失败：
- 后端代码缺失：检查 backend/main.py 是否包含最新代码
- 前端代码缺失：检查 index.html 是否包含最新代码
- Git 未推送：运行 git push origin main

调试工具：
- debug_financial.html: 浏览器调试页面
- test_api_endpoint.py: API 端点测试脚本
    """)


def main():
    """主函数"""
    print("\n" + "="*60)
    print("财报功能部署验证工具")
    print("="*60)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    backend_ok = check_backend_code()
    frontend_ok = check_frontend_code()
    docker_ok = check_dockerfile()
    git_ok = check_git_status()

    print("\n" + "="*60)
    print("检查总结")
    print("="*60)
    print(f"后端代码: {'✓ 通过' if backend_ok else '✗ 失败'}")
    print(f"前端代码: {'✓ 通过' if frontend_ok else '✗ 失败'}")
    print(f"Dockerfile: {'✓ 通过' if docker_ok else '✗ 失败'}")
    print(f"Git 状态: {'✓ 已推送' if git_ok is True else '⚠️  需要推送' if git_ok is False else '⚠️  无法确定'}")

    all_ok = backend_ok and frontend_ok and docker_ok
    if all_ok and git_ok:
        print("\n✓ 所有关键检查通过！可以开始部署。")
    elif all_ok:
        print("\n⚠️  代码已就绪，但需要推送到 GitHub。")
    else:
        print("\n✗ 发现问题，请根据上述提示修复。")

    print_next_steps()

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
