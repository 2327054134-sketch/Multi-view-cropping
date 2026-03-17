"""
ViewCrop - 智能图像分割工具
版本: 2.0 全新重构

一个用于自动识别和分割图像中独立区域的工具。
支持批量处理、参数调节和高质量导出。
"""

__version__ = "2.0.0"
__author__ = "CoPaw"
__description__ = "智能图像分割工具"

from .core import ImageProcessor, AppConfig
from .ui import MainWindow

__all__ = ['ImageProcessor', 'AppConfig', 'MainWindow', '__version__']