"""
国际化(i18n)模块
支持中英文切换
"""

from typing import Dict, Callable


class I18n:
    """国际化管理器"""
    
    # 支持的语言
    LANGUAGES = {
        'zh': '中文',
        'en': 'English'
    }
    
    # 翻译字典
    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        'zh': {
            # 窗口标题
            'app_title': 'Multi-view cropping - 智能多视图批量裁切工具',
            
            # 图像预览
            'image_preview': '图像预览',
            'manual_result': '✏️ 手动修正结果',
            'auto_detect_region': '🤖 自动识别区域',
            'show_manual_result': '显示：手动修正结果（可编辑框）',
            'show_auto_region': '显示：自动识别区域（AI检测结果）',
            'drop_images_here': '📁 批量拖入图片到此处',
            
            # 框编辑工具栏
            'add_box': '➕ 添加框',
            'add_box_tooltip': '点击后在图像上拖拽绘制新框',
            'delete_selected': '🗑️ 删除选中',
            'delete_tooltip': '删除当前选中的框 (也可按 Delete 键)',
            'edit_hint': '提示：点击框选中，拖拽移动，拖拽手柄调整大小',
            
            # 参数控制
            'dilate': '[ ] 融合度:',
            'dilate_label': '融合度',
            'area': '[X] 过滤阈值:',
            'area_label': '过滤',
            'filter_horizontal': '过滤横向干扰',
            'filter_horizontal_tooltip': '移除图像中的水平线条干扰\n适用场景：\n• 网格/表格中的横线\n• 角色地平线阴影\n• 扫描件中的扫描线',
            'filter_vertical': '过滤纵向干扰',
            'filter_vertical_tooltip': '移除图像中的垂直线条干扰\n适用场景：\n• 网格/表格中的竖线\n• 分栏布局的分隔线\n• 扫描件边缘的黑边',
            
            # 统计
            'detection_stats': '[统计] 检测统计',
            'no_image': '无图像',
            'file': '文件',
            'size': '尺寸',
            'path': '路径',
            'detected_regions': '识别区域',
            
            # 文件列表
            'file_list': '文件列表',
            'add_files': '添加文件',
            'clear_list': '清空列表',
            
            # 按钮
            'export_results': '导出结果',
            'language': '🌐 语言',
            
            # 状态栏
            'ready': '就绪',
            'processing': '处理中...',
            'processing_complete': '处理完成，检测到 {} 个区域',
            'processing_failed': '处理失败',
            'export_complete': '导出完成：{} 个文件',
            'box_updated': '框已更新，当前共 {} 个区域',
            'box_selected': '选中框 #{}，拖拽移动，拖拽手柄调整大小，按 Delete 删除',
            
            # 消息框
            'error': '错误',
            'warning': '提示',
            'info': '信息',
            'cannot_load_image': '无法加载图像：{}',
            'export_finished': '导出完成',
            'export_success': '成功导出 {} 个图像到:\n{}',
            'add_box_first': '请先加载并处理图像',
        },
        'en': {
            # Window title
            'app_title': 'Multi-view cropping - Intelligent Batch Cropping Tool',
            
            # Image preview
            'image_preview': 'Image Preview',
            'manual_result': '✏️ Manual Result',
            'auto_detect_region': '🤖 Auto Detection',
            'show_manual_result': 'Show: Manual Result (Editable)',
            'show_auto_region': 'Show: Auto Detection (AI Result)',
            'drop_images_here': '📁 Drop Images Here',
            
            # Box edit toolbar
            'add_box': '➕ Add Box',
            'add_box_tooltip': 'Click then drag on image to draw new box',
            'delete_selected': '🗑️ Delete Selected',
            'delete_tooltip': 'Delete selected box (or press Delete key)',
            'edit_hint': 'Hint: Click box to select, drag to move, drag handles to resize',
            
            # Parameters
            'dilate': '[ ] Merge:',
            'dilate_label': 'Merge',
            'area': '[X] Filter:',
            'area_label': 'Filter',
            'filter_horizontal': 'Filter Horizontal',
            'filter_horizontal_tooltip': 'Remove horizontal line interference\nUse cases:\n• Grid/table horizontal lines\n• Character horizon shadows\n• Scan lines',
            'filter_vertical': 'Filter Vertical',
            'filter_vertical_tooltip': 'Remove vertical line interference\nUse cases:\n• Grid/table vertical lines\n• Column separators\n• Scan edge artifacts',
            
            # Stats
            'detection_stats': '[Stats] Detection',
            'no_image': 'No Image',
            'file': 'File',
            'size': 'Size',
            'path': 'Path',
            'detected_regions': 'Detected',
            
            # File list
            'file_list': 'File List',
            'add_files': 'Add Files',
            'clear_list': 'Clear List',
            
            # Buttons
            'export_results': 'Export Results',
            'language': '🌐 Language',
            
            # Status bar
            'ready': 'Ready',
            'processing': 'Processing...',
            'processing_complete': 'Processing complete, {} regions detected',
            'processing_failed': 'Processing failed',
            'export_complete': 'Export complete: {} files',
            'box_updated': 'Boxes updated, {} regions total',
            'box_selected': 'Box #{} selected, drag to move, drag handles to resize, press Delete to remove',
            
            # Message boxes
            'error': 'Error',
            'warning': 'Warning',
            'info': 'Information',
            'cannot_load_image': 'Cannot load image: {}',
            'export_finished': 'Export Finished',
            'export_success': 'Successfully exported {} images to:\n{}',
            'add_box_first': 'Please load and process an image first',
        }
    }
    
    def __init__(self):
        self._lang = 'zh'  # 默认中文
        self._listeners: list[Callable] = []
    
    @property
    def current_lang(self) -> str:
        return self._lang
    
    def set_language(self, lang: str):
        """设置语言"""
        if lang in self.LANGUAGES:
            self._lang = lang
            self._notify_listeners()
    
    def toggle_language(self):
        """切换语言"""
        new_lang = 'en' if self._lang == 'zh' else 'zh'
        self.set_language(new_lang)
    
    def get(self, key: str, *args) -> str:
        """获取翻译文本"""
        text = self.TRANSLATIONS.get(self._lang, {}).get(key, key)
        if args:
            return text.format(*args)
        return text
    
    def add_listener(self, callback: Callable):
        """添加语言变更监听器"""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """移除语言变更监听器"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self):
        """通知所有监听器语言已变更"""
        for callback in self._listeners:
            callback(self._lang)


# 全局单例
i18n = I18n()


# 便捷函数
def tr(key: str, *args) -> str:
    """翻译函数"""
    return i18n.get(key, *args)


def set_lang(lang: str):
    """设置语言"""
    i18n.set_language(lang)


def toggle_lang():
    """切换语言"""
    i18n.toggle_language()
