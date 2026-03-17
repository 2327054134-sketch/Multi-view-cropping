"""
智能后处理模块
提供框的后处理功能：合并重叠框、去除小碎片、宽高比过滤等
"""

from typing import List, Tuple
import numpy as np


class PostProcessor:
    """后处理器"""
    
    @staticmethod
    def merge_overlapping_boxes(
        boxes: List[Tuple[int, int, int, int]],
        overlap_threshold: float = 0.3
    ) -> List[Tuple[int, int, int, int]]:
        """
        合并重叠的框
        
        Args:
            boxes: 边界框列表 (x, y, w, h)
            overlap_threshold: IOU阈值，超过此值则合并
            
        Returns:
            合并后的框列表
        """
        if not boxes:
            return []
        
        # 转换为numpy数组便于计算
        boxes_array = np.array(boxes)
        
        # 计算每个框的面积
        areas = boxes_array[:, 2] * boxes_array[:, 3]
        
        # 按面积从大到小排序（优先保留大框）
        indices = np.argsort(areas)[::-1]
        
        merged = []
        suppressed = set()
        
        for i in indices:
            if i in suppressed:
                continue
            
            box_i = boxes_array[i]
            merged.append(tuple(box_i))
            
            # 检查与其他框的重叠
            for j in indices:
                if i == j or j in suppressed:
                    continue
                
                box_j = boxes_array[j]
                iou = PostProcessor._calculate_iou(box_i, box_j)
                
                if iou > overlap_threshold:
                    suppressed.add(j)
        
        return merged
    
    @staticmethod
    def _calculate_iou(
        box1: np.ndarray,
        box2: np.ndarray
    ) -> float:
        """计算两个框的IOU（交并比）"""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # 计算交集
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        
        # 计算并集
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def remove_small_fragments(
        boxes: List[Tuple[int, int, int, int]],
        min_area: int = 500,
        min_width: int = 30,
        min_height: int = 30
    ) -> List[Tuple[int, int, int, int]]:
        """
        去除小碎片框
        
        Args:
            boxes: 边界框列表
            min_area: 最小面积
            min_width: 最小宽度
            min_height: 最小高度
            
        Returns:
            过滤后的框列表
        """
        filtered = []
        for x, y, w, h in boxes:
            area = w * h
            if area >= min_area and w >= min_width and h >= min_height:
                filtered.append((x, y, w, h))
        return filtered
    
    @staticmethod
    def filter_by_aspect_ratio(
        boxes: List[Tuple[int, int, int, int]],
        min_ratio: float = 0.3,
        max_ratio: float = 3.0
    ) -> List[Tuple[int, int, int, int]]:
        """
        按宽高比过滤框
        
        Args:
            boxes: 边界框列表
            min_ratio: 最小宽高比 (w/h)
            max_ratio: 最大宽高比 (w/h)
            
        Returns:
            过滤后的框列表
        """
        filtered = []
        for x, y, w, h in boxes:
            if h == 0:
                continue
            ratio = w / h
            if min_ratio <= ratio <= max_ratio:
                filtered.append((x, y, w, h))
        return filtered
    
    @staticmethod
    def remove_contained_boxes(
        boxes: List[Tuple[int, int, int, int]],
        containment_threshold: float = 0.9
    ) -> List[Tuple[int, int, int, int]]:
        """
        移除被其他框完全包含的小框
        
        Args:
            boxes: 边界框列表
            containment_threshold: 包含阈值，小框被包含面积超过此比例则被移除
            
        Returns:
            过滤后的框列表
        """
        if not boxes:
            return []
        
        to_remove = set()
        
        for i, box1 in enumerate(boxes):
            for j, box2 in enumerate(boxes):
                if i >= j:
                    continue
                
                # 检查box1是否被box2包含
                if PostProcessor._is_contained(box1, box2, containment_threshold):
                    to_remove.add(i)
                # 检查box2是否被box1包含
                elif PostProcessor._is_contained(box2, box1, containment_threshold):
                    to_remove.add(j)
        
        return [box for i, box in enumerate(boxes) if i not in to_remove]
    
    @staticmethod
    def _is_contained(
        small_box: Tuple[int, int, int, int],
        large_box: Tuple[int, int, int, int],
        threshold: float
    ) -> bool:
        """检查small_box是否被large_box包含超过threshold比例"""
        x1, y1, w1, h1 = small_box
        x2, y2, w2, h2 = large_box
        
        # 计算交集
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        
        if xi2 <= xi1 or yi2 <= yi1:
            return False
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        small_area = w1 * h1
        
        return intersection / small_area >= threshold
    
    @staticmethod
    def sort_boxes_z_order(
        boxes: List[Tuple[int, int, int, int]],
        row_height: int = 100
    ) -> List[Tuple[int, int, int, int]]:
        """
        按Z字顺序排序框（从上到下，从左到右）
        
        Args:
            boxes: 边界框列表
            row_height: 行高阈值，用于判断哪些框在同一行
            
        Returns:
            排序后的框列表
        """
        # 按y坐标分组到行
        rows = []
        used = set()
        
        sorted_by_y = sorted(enumerate(boxes), key=lambda x: x[1][1])
        
        for i, (orig_idx, box) in enumerate(sorted_by_y):
            if orig_idx in used:
                continue
            
            # 找到同一行的所有框
            row = [(orig_idx, box)]
            used.add(orig_idx)
            
            for j, (other_idx, other_box) in enumerate(sorted_by_y[i+1:], i+1):
                if other_idx in used:
                    continue
                
                # 检查是否在同一行（y坐标接近）
                if abs(box[1] - other_box[1]) < row_height:
                    row.append((other_idx, other_box))
                    used.add(other_idx)
            
            # 按x坐标排序
            row.sort(key=lambda x: x[1][0])
            rows.append(row)
        
        # 展平结果
        result = []
        for row in rows:
            result.extend([box for _, box in row])
        
        return result
    
    @classmethod
    def apply_all(
        cls,
        boxes: List[Tuple[int, int, int, int]],
        merge_overlap: bool = True,
        overlap_threshold: float = 0.3,
        remove_fragments: bool = True,
        min_area: int = 500,
        min_width: int = 30,
        min_height: int = 30,
        filter_aspect: bool = False,
        min_ratio: float = 0.3,
        max_ratio: float = 3.0,
        remove_contained: bool = True,
        containment_threshold: float = 0.9
    ) -> List[Tuple[int, int, int, int]]:
        """
        应用所有启用的后处理
        
        Args:
            boxes: 原始框列表
            merge_overlap: 是否合并重叠框
            overlap_threshold: 重叠阈值
            remove_fragments: 是否去除小碎片
            min_area: 最小面积
            min_width: 最小宽度
            min_height: 最小高度
            filter_aspect: 是否按宽高比过滤
            min_ratio: 最小宽高比
            max_ratio: 最大宽高比
            remove_contained: 是否移除被包含的框
            containment_threshold: 包含阈值
            
        Returns:
            处理后的框列表
        """
        result = boxes.copy()
        
        # 1. 合并重叠框
        if merge_overlap:
            result = cls.merge_overlapping_boxes(result, overlap_threshold)
        
        # 2. 移除被包含的框
        if remove_contained:
            result = cls.remove_contained_boxes(result, containment_threshold)
        
        # 3. 去除小碎片
        if remove_fragments:
            result = cls.remove_small_fragments(result, min_area, min_width, min_height)
        
        # 4. 宽高比过滤
        if filter_aspect:
            result = cls.filter_by_aspect_ratio(result, min_ratio, max_ratio)
        
        # 5. 重新排序
        result = cls.sort_boxes_z_order(result)
        
        return result
