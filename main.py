#!/usr/bin/env python3
"""
ViewCrop - 智能图像分割工具
版本: 2.0 (全新重构)
功能: 自动识别和分割图像中的独立区域
"""

import sys
import os
from pathlib import Path

# PyInstaller 兼容性修复 - 必须在任何导入之前！
if getattr(sys, 'frozen', False):
    bundle_dir = Path(sys._MEIPASS)
    plugin_path = bundle_dir / "PySide6" / "plugins"
    platform_path = plugin_path / "platforms"
    
    # 强制设置所有可能的路径变量
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(plugin_path)
    os.environ['QT_PLUGIN_PATH'] = str(plugin_path)
    os.environ['PATH'] = str(platform_path) + os.pathsep + os.environ['PATH']
    
    # 调试输出
    print(f"[FORCE] Bundle Dir: {bundle_dir}")
    print(f"[FORCE] Plugin Path: {plugin_path}")
    print(f"[FORCE] Platform Path: {platform_path}")
    print(f"[FORCE] Plugin Exists: {plugin_path.exists()}")
    print(f"[FORCE] qwindows.dll Exists: {(platform_path / 'qwindows.dll').exists()}")

# 添加项目路径到Python.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Qt应用类
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QLibraryInfo
from PySide6.QtGui import QFont

def setup_application():
    """设置应用程序"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("ViewCrop")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("CoPaw")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    return app

def import_modules():
    """导入必要模块"""
    try:
        from ui.main_window import MainWindow
        return MainWindow
    except ImportError as e:
        print(f"模块导入失败: {e}")
        return None

def main():
    """主函数"""
    print("=" * 50)
    print("ViewCrop 2.0 - 智能图像分割工具")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return 1
    
    # 创建应用
    app = setup_application()
    
    # 导入主窗口
    MainWindow = import_modules()
    if not MainWindow:
        return 1
    
    try:
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        print("ViewCrop启动成功！")
        print("=" * 50)
        
        # 运行应用
        return app.exec()
        
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())