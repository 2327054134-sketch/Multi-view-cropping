"""
核心功能模块
包含图像处理、数据分析等核心功能
"""

from .image_processor import ImageProcessor
from .config import AppConfig
from .i18n import i18n, tr, set_lang, toggle_lang

__all__ = ['ImageProcessor', 'AppConfig', 'i18n', 'tr', 'set_lang', 'toggle_lang']