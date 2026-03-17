"""
配置文件定义
包含所有应用程序的常量和配置
"""

class AppConfig:
    """应用程序配置"""
    
    # 基本信息
    APP_NAME = "ViewCrop"
    APP_VERSION = "2.0"
    WINDOW_TITLE = f"ViewCrop {APP_VERSION} - 智能图像分割工具"
    WINDOW_SIZE = (1200, 800)
    
    # 支持的图像格式
    SUPPORTED_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')
    
    # 图像处理参数
    class ImageProcessing:
        """图像处理参数"""
        # 默认参数
        DEFAULT_DILATE = 15
        DEFAULT_AREA = 2000
        
        # 参数范围
        DILATE_MIN = 1
        DILATE_MAX = 100
        AREA_MIN = 100
        AREA_MAX = 50000
        
        # 边缘检测参数
        CANNY_LOW = 30
        CANNY_HIGH = 100
        
        # 预处理参数
        MAX_PREVIEW_WIDTH = 800
        THUMBNAIL_SIZE = 80
    
    # UI配置
    class UI:
        """界面配置"""
        # 颜色主题
        COLORS = {
            'primary': '#2196F3',
            'success': '#4CAF50', 
            'warning': '#FF9800',
            'error': '#F44336',
            'background': '#1E1E1E',
            'surface': '#2D2D2D',
            'on_surface': '#FFFFFF',
            'on_background': '#E0E0E0'
        }
        
        # 尺寸配置
        MIN_WINDOW_WIDTH = 800
        MIN_WINDOW_HEIGHT = 600
        SIDEBAR_WIDTH = 280
        TOOLBAR_HEIGHT = 40
        
        # 字体大小
        FONT_SMALL = 9
        FONT_NORMAL = 10
        FONT_LARGE = 12
    
    # 文件操作
    class Files:
        """文件操作配置"""
        # 默认导出文件夹名
        EXPORT_DIR_PREFIX = "ViewCrop_Export"
        
        # 导出文件名格式
        EXPORT_FORMAT = "{basename}_{index}.{ext}"
        
        # 批处理设置
        MAX_BATCH_FILES = 100


class ImageProcessingConfig:
    """图像处理配置"""
    
    def __init__(self):
        # 基本参数
        self.dilate = AppConfig.ImageProcessing.DEFAULT_DILATE
        self.area = AppConfig.ImageProcessing.DEFAULT_AREA
        
        # 滤波选项
        self.remove_horizontal = False
        self.remove_vertical = False
        
        # 高级参数
        self.canny_low = AppConfig.ImageProcessing.CANNY_LOW
        self.canny_high = AppConfig.ImageProcessing.CANNY_HIGH
        
        # 缓存
        self._cached_result = None
        self._cached_mask = None
        self._cache_valid = False
    
    def invalidate_cache(self):
        """使缓存失效"""
        self._cached_result = None
        self._cached_mask = None
        self._cache_valid = False
    
    def set_params(self, dilate=None, area=None, remove_h=None, remove_v=None):
        """设置参数并清除缓存"""
        changed = False
        
        if dilate is not None and dilate != self.dilate:
            self.dilate = dilate
            changed = True
            
        if area is not None and area != self.area:
            self.area = area
            changed = True
            
        if remove_h is not None and remove_h != self.remove_horizontal:
            self.remove_horizontal = remove_h
            changed = True
            
        if remove_v is not None and remove_v != self.remove_vertical:
            self.remove_vertical = remove_v
            changed = True
        
        if changed:
            self.invalidate_cache()