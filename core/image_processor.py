"""
图像处理核心模块
负责所有的图像处理算法
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional
import logging

from .config import AppConfig, ImageProcessingConfig

logger = logging.getLogger(__name__)


class ProcessingResult:
    """处理结果类"""

    def __init__(self, boxes: List[Tuple[int, int, int, int]],
                 mask: np.ndarray, preview: np.ndarray,
                 gray: Optional[np.ndarray] = None,
                 edges: Optional[np.ndarray] = None):
        self.boxes = boxes  # 边界框列表 (x, y, w, h)
        self.mask = mask    # 二值化遮罩
        self.preview = preview  # 预览图像（带标注）
        self.gray = gray    # 灰度图（用于预览）
        self.edges = edges  # 边缘检测图（用于预览）


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        self.config = ImageProcessingConfig()
    
    def process_image(self, image: np.ndarray) -> Optional[ProcessingResult]:
        """
        处理图像，提取分割区域

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            ProcessingResult: 包含边界框、遮罩、预览和中间步骤的结果
        """
        try:
            # 检查图像有效性
            if image is None or image.size == 0:
                logger.error("输入图像无效")
                return None

            # 执行图像处理流程（保存中间步骤用于预览）
            gray = self._to_grayscale(image)
            edges = self._detect_edges(gray)
            filtered_edges = self._filter_lines(edges)
            mask = self._dilate_mask(filtered_edges)
            boxes = self._find_contours(mask)
            preview = self._create_preview(image.copy(), boxes)

            # 返回包含中间步骤的结果
            return ProcessingResult(boxes, mask, preview, gray=gray, edges=edges)

        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            return None
    
    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """转换为灰度图"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def _detect_edges(self, gray: np.ndarray) -> np.ndarray:
        """边缘检测"""
        return cv2.Canny(gray, 
                        AppConfig.ImageProcessing.CANNY_LOW,
                        AppConfig.ImageProcessing.CANNY_HIGH)
    
    def _filter_lines(self, edges: np.ndarray) -> np.ndarray:
        """过滤水平线和垂直线"""
        filtered = edges.copy()
        
        # 移除水平线
        if self.config.remove_horizontal:
            kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            lines_h = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_h)
            filtered = cv2.subtract(filtered, lines_h)
        
        # 移除垂直线
        if self.config.remove_vertical:
            kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            lines_v = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_v)
            filtered = cv2.subtract(filtered, lines_v)
        
        return filtered
    
    def _dilate_mask(self, edges: np.ndarray) -> np.ndarray:
        """膨胀遮罩"""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, 
                                          (self.config.dilate, self.config.dilate))
        return cv2.dilate(edges, kernel, iterations=1)
    
    def _find_contours(self, mask: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """查找轮廓并转换为边界框"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.config.area:
                x, y, w, h = cv2.boundingRect(contour)
                boxes.append((x, y, w, h))
        
        # 按Z字顺序排序 (从上到下，从左到右)
        boxes.sort(key=lambda b: (b[1] // 100, b[0]))
        
        return boxes
    
    def _create_preview(self, image: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """创建带标注的预览图（自动识别结果，标注auto）"""
        preview = image.copy()
        
        # 绘制参数 - 绿框绿底
        box_color = (0, 255, 0)  # 绿色
        text_color = (0, 0, 0)  # 黑色文字
        text_bg_color = (0, 255, 0)  # 绿色背景
        thickness = 3  # 加粗到3像素
        
        # 字体设置
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        
        for i, (x, y, w, h) in enumerate(boxes):
            # 绘制矩形框
            cv2.rectangle(preview, (x, y), (x + w, y + h), box_color, thickness)
            
            # 绘制编号 + auto 标记
            label = f"#{i + 1} auto"
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # 绿色背景矩形
            cv2.rectangle(preview, 
                         (x, y - text_h - 8), 
                         (x + text_w + 10, y),
                         text_bg_color, -1)
            
            # 黑色文字
            cv2.putText(preview, label, 
                       (x + 5, y - 5),
                       font, font_scale, text_color, 2, cv2.LINE_AA)
        
        return preview
    
    def create_mask_preview(self, mask: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        在二值化掩膜上绘制框和序号（自动识别区域视图）
        
        Args:
            mask: 二值化掩膜 (单通道灰度图，黑底白块)
            boxes: 边界框列表
            
        Returns:
            带标注的RGB图像
        """
        # 将灰度掩膜转为BGR彩色图
        mask_colored = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        
        # 绘制参数 - 青色框黄底黑字，在黑底白块上更醒目
        box_color = (255, 255, 0)  # 青色 (BGR)
        text_color = (0, 0, 0)  # 黑色文字
        text_bg_color = (0, 255, 255)  # 黄色背景
        thickness = 3  # 加粗到3像素
        
        # 字体设置
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        
        for i, (x, y, w, h) in enumerate(boxes):
            # 绘制矩形框
            cv2.rectangle(mask_colored, (x, y), (x + w, y + h), box_color, thickness)
            
            # 绘制编号 + auto 标记
            label = f"#{i + 1} auto"
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # 黄色背景矩形
            cv2.rectangle(mask_colored, 
                         (x, y - text_h - 8), 
                         (x + text_w + 10, y),
                         text_bg_color, -1)
            
            # 黑色文字
            cv2.putText(mask_colored, label, 
                       (x + 5, y - 5),
                       font, font_scale, text_color, 2, cv2.LINE_AA)
        
        return mask_colored
    
    def create_thumbnail(self, image: np.ndarray, size: int = 80) -> np.ndarray:
        """创建缩略图"""
        h, w = image.shape[:2]
        
        # 中心裁剪
        m = min(h, w)
        x1 = (w - m) // 2
        y1 = (h - m) // 2
        cropped = image[y1:y1 + m, x1:x1 + m]
        
        # 缩放
        return cv2.resize(cropped, (size, size), interpolation=cv2.INTER_AREA)
    
    def load_image(self, file_path: str) -> Optional[np.ndarray]:
        """
        加载图像文件
        
        Args:
            file_path: 图像文件路径
            
        Returns:
            numpy.ndarray: 图像数组 (BGR格式) 或 None
        """
        try:
            # 支持中文路径
            image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
            
            if image is None:
                logger.error(f"无法加载图像: {file_path}")
                return None
            
            # 转换BGRA到BGR
            if len(image.shape) == 3 and image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            
            return image
            
        except Exception as e:
            logger.error(f"加载图像失败 {file_path}: {e}")
            return None
    
    def save_image(self, image: np.ndarray, file_path: str) -> bool:
        """
        保存图像文件
        
        Args:
            image: 图像数组
            file_path: 保存路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 支持中文路径
            success = cv2.imencode(".png", image)[1].tofile(file_path)
            return True
        except Exception as e:
            logger.error(f"保存图像失败 {file_path}: {e}")
            return False
    
    def crop_boxes(self, image: np.ndarray, boxes: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """
        根据边界框裁剪图像
        
        Args:
            image: 原始图像
            boxes: 边界框列表
            
        Returns:
            List[np.ndarray]: 裁剪后的图像列表
        """
        h, w = image.shape[:2]
        crops = []
        
        for x, y, bw, bh in boxes:
            # 防止越界
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w, x + bw)
            y2 = min(h, y + bh)
            
            if x2 > x1 and y2 > y1:
                crop = image[y1:y2, x1:x2]
                if crop.size > 0:
                    crops.append(crop)
        
        return crops
    
    def get_config(self) -> ImageProcessingConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, **kwargs):
        """更新配置"""
        self.config.set_params(**kwargs)