#!/usr/bin/env python3
"""
ViewCrop 快速启动脚本
自动检查环境并启动程序
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("[ERROR] 错误: 需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        return False
    print(f"[OK] Python版本: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_dependencies():
    """检查依赖包"""
    required_packages = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('PySide6', 'PySide6'),
        ('PIL', 'Pillow')
    ]
    
    all_ok = True
    for module_name, package_name in required_packages:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                raise ImportError
            print(f"[OK] {package_name} - 已安装")
        except ImportError:
            print(f"[FAIL] {package_name} - 未安装")
            all_ok = False
            
    return all_ok


def install_dependencies():
    """提示安装依赖"""
    print("\n需要安装依赖包，请运行以下命令：")
    print("pip install -r requirements.txt")
    print("\n或者手动安装：")
    print("pip install opencv-python numpy PySide6 Pillow")


def start_application():
    """启动应用程序"""
    try:
        print("\n🚀 启动ViewCrop...")
        print("-" * 40)
        
        # 导入主程序
        from main import main as main_func
        
        # 启动
        exit_code = main_func()
        
        if exit_code == 0:
            print("\n[OK] ViewCrop正常退出")
        else:
            print(f"\n[ERROR] ViewCrop异常退出 (代码: {exit_code})")
            
        return exit_code
        
    except Exception as e:
        print(f"\n[ERROR] 启动失败: {e}")
        print("\n请检查：")
        print("1. 依赖包是否正确安装")
        print("2. Python版本是否满足要求")
        print("3. 文件是否完整")
        return 1


def main():
    """主函数"""
    print("ViewCrop 2.0 启动器")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 检查依赖
    if not check_dependencies():
        install_dependencies()
        return 1
    
    # 启动应用
    return start_application()


if __name__ == "__main__":
    try:
        exit_code = main()
        input("\n按回车键退出...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户中断，退出程序")
        sys.exit(0)