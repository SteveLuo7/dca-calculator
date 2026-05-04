#!/usr/bin/env python3
"""
快速启动测试脚本 - 验证前端重构功能
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n▶ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} 失败")
            if result.stderr.strip():
                print(f"错误: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} 超时")
        return False
    except Exception as e:
        print(f"❌ {description} 异常: {e}")
        return False

def test_backend_api():
    """测试后端API功能"""
    print_header("1. 测试后端API功能")

    backend_dir = Path(__file__).parent / "backend"

    # 测试导入
    print("\n测试模块导入...")
    test_script = backend_dir / "test_refactor_api.py"
    if test_script.exists():
        success = run_command(
            f'cd {backend_dir} && python test_refactor_api.py',
            "API功能测试"
        )
        return success
    else:
        print(f"❌ 测试文件不存在: {test_script}")
        return False

def check_frontend_files():
    """检查前端文件"""
    print_header("2. 检查前端文件")

    frontend_file = Path(__file__).parent / "frontend" / "index.html"
    test_file = Path(__file__).parent / "test_refactor.html"

    checks = [
        (frontend_file, "主页面文件"),
        (test_file, "测试页面文件")
    ]

    all_ok = True
    for file_path, desc in checks:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {desc}: {file_path} ({size} bytes)")
        else:
            print(f"❌ {desc}: {file_path} 不存在")
            all_ok = False

    # 检查HTML结构
    if frontend_file.exists():
        content = frontend_file.read_text(encoding='utf-8')
        required_elements = [
            ('market-tabs', '市场标签页'),
            ('asiaContent', '亚洲市场内容区'),
            ('europeContent', '欧洲市场内容区'),
            ('americasContent', '美洲市场内容区'),
            ('searchInput', '搜索输入框')
        ]

        print("\n检查HTML结构:")
        for element_id, desc in required_elements:
            if f'id="{element_id}"' in content:
                print(f"✅ {desc} ({element_id})")
            else:
                print(f"❌ {desc} ({element_id}) 未找到")
                all_ok = False

    return all_ok

def start_server():
    """启动后端服务器"""
    print_header("3. 启动后端服务器")

    backend_dir = Path(__file__).parent / "backend"
    print(f"\n启动服务器在 {backend_dir}...")
    print("提示: 按 Ctrl+C 停止服务器")

    try:
        # 启动uvicorn服务器
        process = subprocess.Popen(
            ['uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        time.sleep(3)

        # 检查进程是否仍在运行
        if process.poll() is None:
            print("✅ 服务器已启动在 http://localhost:8000")

            # 打开测试页面
            test_file = Path(__file__).parent / "test_refactor.html"
            if test_file.exists():
                print(f"\n🌐 打开测试页面...")
                webbrowser.open(f'file://{test_file.absolute()}')

            print("\n" + "=" * 60)
            print("  服务器运行中")
            print("  测试页面: test_refactor.html")
            print("  主页面: http://localhost:8000")
            print("  API文档: http://localhost:8000/docs")
            print("  按 Ctrl+C 停止服务器")
            print("=" * 60)

            # 保持服务器运行
            process.wait()
        else:
            print("❌ 服务器启动失败")
            return False

    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动服务器异常: {e}")
        return False

def main():
    """主函数"""
    print_header("前端重构功能测试")
    print("本脚本将:")
    print("1. 测试后端API功能")
    print("2. 检查前端文件")
    print("3. 启动服务器并打开测试页面")

    # 测试后端API
    api_ok = test_backend_api()

    # 检查前端文件
    frontend_ok = check_frontend_files()

    # 如果都通过，启动服务器
    if api_ok and frontend_ok:
        print("\n" + "=" * 60)
        print("✅ 所有检查通过！")
        print("=" * 60)
        print("\n现在启动服务器进行手动测试...")
        print("提示: 按 Ctrl+C 可以跳过服务器启动\n")

        try:
            response = input("是否启动服务器? (y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                start_server()
            else:
                print("\n跳过服务器启动。")
                print("您可以手动启动:")
                print("  cd backend")
                print("  uvicorn main:app --reload --port 8000")
        except KeyboardInterrupt:
            print("\n\n👋 测试完成")
    else:
        print("\n" + "=" * 60)
        print("❌ 检查失败，请修复问题后再试")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
