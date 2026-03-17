"""
自动智能调参模块
根据图像特征自动分析并推荐最佳处理参数
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional


class AutoTuner:
    """自动调参器"""
    
    @staticmethod
    def analyze_image(image: np.ndarray) -> Dict:
        """
        分析图像特征
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            图像特征字典
        """
        if image is None or image.size == 0:
            return {}
        
        features = {}
        
        # 基本尺寸信息
        h, w = image.shape[:2]
        features['width'] = w
        features['height'] = h
        features['area'] = w * h
        features['aspect_ratio'] = w / h if h > 0 else 1.0
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 亮度分析
        features['mean_brightness'] = np.mean(gray)
        features['std_brightness'] = np.std(gray)
        
        # 对比度分析
        features['contrast'] = features['std_brightness']
        
        # 边缘密度分析（用于判断图像复杂度）
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (h * w)
        features['edge_density'] = edge_density
        
        # 判断背景类型
        features['background_type'] = AutoTuner._detect_background_type(gray)
        
        # 预估物体数量和大小
        features['estimated_objects'] = AutoTuner._estimate_objects(gray, edges)
        
        return features
    
    @staticmethod
    def _detect_background_type(gray: np.ndarray) -> str:
        """检测背景类型"""
        # 计算边缘区域的亮度
        h, w = gray.shape
        border_pixels = []
        border_pixels.extend(gray[0, :])  # 上边缘
        border_pixels.extend(gray[-1, :])  # 下边缘
        border_pixels.extend(gray[:, 0])  # 左边缘
        border_pixels.extend(gray[:, -1])  # 右边缘
        
        border_brightness = np.mean(border_pixels)
        
        # 根据边缘亮度判断背景类型
        if border_brightness < 50:
            return 'dark'  # 深色背景
        elif border_brightness > 200:
            return 'light'  # 浅色/白色背景
        else:
            return 'mixed'  # 混合背景
    
    @staticmethod
    def _estimate_objects(gray: np.ndarray, edges: np.ndarray) -> Dict:
        """预估物体数量和大小"""
        h, w = gray.shape
        
        # 使用不同阈值进行轮廓检测
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'count': 0, 'avg_area': 0, 'areas': []}
        
        areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 100]
        
        if not areas:
            return {'count': 0, 'avg_area': 0, 'areas': []}
        
        return {
            'count': len(areas),
            'avg_area': np.mean(areas),
            'median_area': np.median(areas),
            'areas': areas
        }
    
    @classmethod
    def recommend_params(cls, image: np.ndarray) -> Dict:
        """
        根据图像特征推荐处理参数
        
        Args:
            image: 输入图像
            
        Returns:
            推荐参数字典
        """
        features = cls.analyze_image(image)
        
        if not features:
            return cls._default_params()
        
        params = {}
        
        # 图像尺寸
        img_area = features['area']
        img_w = features['width']
        
        # 1. 融合度 (dilate) 推荐
        # 根据边缘密度和物体数量调整
        edge_density = features.get('edge_density', 0.1)
        estimated_count = features['estimated_objects'].get('count', 4)
        
        if edge_density > 0.15:
            # 边缘密集，可能是复杂图像，需要更大的融合度
            params['dilate'] = min(25, 15 + int(edge_density * 50))
        elif estimated_count > 8:
            # 物体较多，需要中等融合度
            params['dilate'] = 15
        else:
            # 物体较少，使用较小融合度
            params['dilate'] = 10
        
        # 2. 过滤阈值 (area) 推荐
        # 根据预估物体大小和图像尺寸
        avg_area = features['estimated_objects'].get('avg_area', 10000)
        median_area = features['estimated_objects'].get('median_area', 8000)
        
        # 过滤阈值设为预估平均面积的 5-10%
        suggested_area = int(median_area * 0.08)
        
        # 根据图像尺寸调整
        if img_area > 2000000:  # 大图 (>2MP)
            params['area'] = min(5000, max(500, suggested_area))
        elif img_area > 1000000:  # 中图 (1-2MP)
            params['area'] = min(3000, max(300, suggested_area))
        else:  # 小图
            params['area'] = min(1500, max(100, suggested_area))
        
        # 3. 背景类型相关参数
        bg_type = features.get('background_type', 'mixed')
        
        if bg_type == 'dark':
            # 深色背景通常需要更强的边缘检测
            params['canny_low'] = 30
            params['canny_high'] = 90
        elif bg_type == 'light':
            # 浅色背景使用标准参数
            params['canny_low'] = 50
            params['canny_high'] = 150
        else:
            params['canny_low'] = 50
            params['canny_high'] = 150
        
        # 4. 干扰线过滤建议
        # 根据边缘的方向性判断
        params['remove_horizontal'] = False
        params['remove_vertical'] = False
        
        # 如果检测到明显的网格结构，建议开启
        if edge_density > 0.1 and features['estimated_objects'].get('count', 0) > 6:
            # 可能是网格布局，建议开启干扰线过滤
            params['remove_horizontal'] = True
            params['remove_vertical'] = True
        
        return params
    
    @staticmethod
    def _default_params() -> Dict:
        """默认参数"""
        return {
            'dilate': 15,
            'area': 1000,
            'canny_low': 50,
            'canny_high': 150,
            'remove_horizontal': False,
            'remove_vertical': False
        }
    
    @classmethod
    def auto_tune(cls, image: np.ndarray, processor) -> Tuple[bool, str]:
        """
        自动调参并应用到处理器
        
        Args:
            image: 输入图像
            processor: ImageProcessor实例
            
        Returns:
            (是否成功, 信息字符串)
        """
        try:
            params = cls.recommend_params(image)
            
            # 应用到处理器
            processor.update_config(
                dilate=params['dilate'],
                area=params['area'],
                remove_h=params['remove_horizontal'],
                remove_v=params['remove_vertical']
            )
            
            # 生成信息字符串
            info = (
                f"智能调参完成："
                f"融合度={params['dilate']}, "
                f"过滤阈值={params['area']}, "
                f"背景类型={cls._bg_type_name(params.get('canny_low', 50))}"
            )
            
            return True, info
            
        except Exception as e:
            return False, f"自动调参失败: {str(e)}"
    
    @staticmethod
    def _bg_type_name(canny_low: int) -> str:
        """根据canny_low值返回背景类型名称"""
        if canny_low < 40:
            return "深色"
        elif canny_low > 60:
            return "浅色"
        return "混合"
