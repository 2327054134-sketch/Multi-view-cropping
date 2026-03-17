"""
可交互图像视图组件
支持框的增删改：选中、移动、调整大小、删除、添加
"""

from typing import List, Tuple, Optional, Callable
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QMouseEvent, QKeyEvent, QCursor
import cv2
import numpy as np


class BoundingBox:
    """边界框数据类"""
    
    HANDLE_SIZE = 8  # 调整手柄大小
    BORDER_WIDTH = 3  # 边框宽度
    SELECTED_COLOR = QColor(255, 165, 0)  # 选中时橙色
    NORMAL_COLOR = QColor(0, 191, 255)  # 正常深天蓝色（手动修正结果）
    HANDLE_COLOR = QColor(255, 255, 0)  # 手柄黄色
    
    def __init__(self, x: int, y: int, w: int, h: int, index: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.index = index  # 序号
        self.selected = False
        
    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)
    
    def rect(self) -> QRect:
        return QRect(self.x, self.y, self.w, self.h)
    
    def contains(self, point: QPoint) -> bool:
        return self.rect().contains(point)
    
    def get_handle_at(self, point: QPoint) -> Optional[str]:
        """获取点所在的手柄位置，返回位置标识或None"""
        if not self.selected:
            return None
            
        hs = self.HANDLE_SIZE
        x, y, w, h = self.x, self.y, self.w, self.h
        
        # 八个手柄区域
        handles = {
            'tl': QRect(x - hs, y - hs, hs * 2, hs * 2),  # 左上
            'tr': QRect(x + w - hs, y - hs, hs * 2, hs * 2),  # 右上
            'bl': QRect(x - hs, y + h - hs, hs * 2, hs * 2),  # 左下
            'br': QRect(x + w - hs, y + h - hs, hs * 2, hs * 2),  # 右下
            't': QRect(x + hs, y - hs, w - hs * 2, hs * 2),  # 上中
            'b': QRect(x + hs, y + h - hs, w - hs * 2, hs * 2),  # 下中
            'l': QRect(x - hs, y + hs, hs * 2, h - hs * 2),  # 左中
            'r': QRect(x + w - hs, y + hs, hs * 2, h - hs * 2),  # 右中
        }
        
        for name, rect in handles.items():
            if rect.contains(point):
                return name
        return None
    
    def move(self, dx: int, dy: int):
        """移动框"""
        self.x += dx
        self.y += dy
    
    def resize(self, handle: str, dx: int, dy: int):
        """根据手柄调整大小"""
        if handle == 'tl':
            self.x += dx
            self.y += dy
            self.w -= dx
            self.h -= dy
        elif handle == 'tr':
            self.y += dy
            self.w += dx
            self.h -= dy
        elif handle == 'bl':
            self.x += dx
            self.w -= dx
            self.h += dy
        elif handle == 'br':
            self.w += dx
            self.h += dy
        elif handle == 't':
            self.y += dy
            self.h -= dy
        elif handle == 'b':
            self.h += dy
        elif handle == 'l':
            self.x += dx
            self.w -= dx
        elif handle == 'r':
            self.w += dx
        
        # 确保最小尺寸
        if self.w < 20:
            self.w = 20
        if self.h < 20:
            self.h = 20


class InteractiveImageView(QLabel):
    """
    可交互图像视图
    支持框的选中、移动、调整大小、删除、添加
    """
    
    # 信号
    boxes_changed = Signal(list)  # 框发生变化时发射
    box_selected = Signal(int)  # 选中框时发射（发射框的index）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setAlignment(Qt.AlignCenter)
        self.setText("📁 批量拖入图片到此处")
        self.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                border: 3px solid #555555;
                border-radius: 8px;
                color: #888888;
                font-size: 16px;
            }
        """)
        
        # 图像数据
        self.cv_image: Optional[np.ndarray] = None
        self.display_pixmap: Optional[QPixmap] = None
        self.scale_factor = 1.0  # 显示缩放比例
        self.offset = QPoint(0, 0)  # 图像在label中的偏移
        
        # 框数据
        self.boxes: List[BoundingBox] = []
        self.selected_box: Optional[BoundingBox] = None
        
        # 交互状态
        self.is_dragging = False
        self.is_resizing = False
        self.drag_start_pos: Optional[QPoint] = None
        self.resize_handle: Optional[str] = None
        self.last_mouse_pos: Optional[QPoint] = None
        
        # 添加模式
        self.is_adding_mode = False
        self.add_start_pos: Optional[QPoint] = None
        self.temp_rect: Optional[QRect] = None
        
        # 设置鼠标追踪
        self.setMouseTracking(True)
        
    def set_cv_image(self, cv_img: np.ndarray):
        """设置OpenCV图像"""
        self.cv_image = cv_img
        self.update_display()
    
    def set_boxes(self, boxes: List[Tuple[int, int, int, int]]):
        """设置边界框列表"""
        self.boxes = []
        for i, (x, y, w, h) in enumerate(boxes):
            self.boxes.append(BoundingBox(x, y, w, h, i + 1))
        self.selected_box = None
        self.update()
    
    def get_boxes(self) -> List[Tuple[int, int, int, int]]:
        """获取当前所有框的坐标"""
        return [box.to_tuple() for box in self.boxes]
    
    def update_display(self):
        """更新显示"""
        if self.cv_image is None:
            return
            
        # 转换OpenCV图像为QPixmap
        if len(self.cv_image.shape) == 3:
            rgb = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
        else:
            rgb = cv2.cvtColor(self.cv_image, cv2.COLOR_GRAY2RGB)
            
        h, w, c = rgb.shape
        bytes_per_line = c * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # 缩放以适应label大小
        label_w = self.width() - 10
        label_h = self.height() - 10
        self.display_pixmap = pixmap.scaled(
            label_w, label_h,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        # 计算缩放比例和偏移
        self.scale_factor = self.display_pixmap.width() / w
        self.offset = QPoint(
            (self.width() - self.display_pixmap.width()) // 2,
            (self.height() - self.display_pixmap.height()) // 2
        )
        
        self.update()
    
    def image_to_widget(self, x: int, y: int) -> QPoint:
        """将图像坐标转换为widget坐标"""
        return QPoint(
            int(x * self.scale_factor) + self.offset.x(),
            int(y * self.scale_factor) + self.offset.y()
        )
    
    def widget_to_image(self, x: int, y: int) -> Tuple[int, int]:
        """将widget坐标转换为图像坐标"""
        img_x = int((x - self.offset.x()) / self.scale_factor)
        img_y = int((y - self.offset.y()) / self.scale_factor)
        return (img_x, img_y)
    
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        
        if self.display_pixmap is None:
            return
            
        painter = QPainter(self)
        
        # 绘制图像
        painter.drawPixmap(self.offset, self.display_pixmap)
        
        # 绘制框
        for box in self.boxes:
            self._draw_box(painter, box)
        
        # 绘制临时框（添加模式）
        if self.temp_rect:
            pen = QPen(QColor(255, 255, 0))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.temp_rect)
    
    def _draw_box(self, painter: QPainter, box: BoundingBox):
        """绘制单个框（手动修正结果：蓝框绿底黑字）"""
        # 转换到widget坐标
        top_left = self.image_to_widget(box.x, box.y)
        bottom_right = self.image_to_widget(box.x + box.w, box.y + box.h)
        rect = QRect(top_left, bottom_right)
        
        # 绘制边框
        color = BoundingBox.SELECTED_COLOR if box.selected else BoundingBox.NORMAL_COLOR
        pen = QPen(color)
        pen.setWidth(BoundingBox.BORDER_WIDTH)
        painter.setPen(pen)
        painter.drawRect(rect)
        
        # 绘制序号背景 - 绿色背景
        label = f"#{box.index}"
        font = painter.font()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        text_rect = painter.boundingRect(rect, Qt.AlignLeft | Qt.AlignTop, label)
        text_rect.adjust(0, 0, 10, 6)
        
        # 绿底
        painter.fillRect(text_rect, QColor(0, 255, 0))
        
        # 黑字
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(text_rect, Qt.AlignCenter, label)
        
        # 如果选中，绘制调整手柄
        if box.selected:
            painter.setBrush(BoundingBox.HANDLE_COLOR)
            painter.setPen(Qt.NoPen)
            
            hs = BoundingBox.HANDLE_SIZE
            handles = [
                rect.topLeft(),
                rect.topRight(),
                rect.bottomLeft(),
                rect.bottomRight(),
                QPoint((rect.left() + rect.right()) // 2, rect.top()),
                QPoint((rect.left() + rect.right()) // 2, rect.bottom()),
                QPoint(rect.left(), (rect.top() + rect.bottom()) // 2),
                QPoint(rect.right(), (rect.top() + rect.bottom()) // 2),
            ]
            
            for handle_pos in handles:
                handle_rect = QRect(
                    handle_pos.x() - hs, handle_pos.y() - hs,
                    hs * 2, hs * 2
                )
                painter.drawRect(handle_rect)
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if self.cv_image is None:
            return
            
        pos = event.pos()
        img_pos = self.widget_to_image(pos.x(), pos.y())
        img_point = QPoint(img_pos[0], img_pos[1])
        
        if event.button() == Qt.LeftButton:
            # 添加模式
            if self.is_adding_mode:
                self.add_start_pos = img_point
                self.temp_rect = QRect(pos, QSize(0, 0))
                return
            
            # 检查是否点击了选中框的手柄
            if self.selected_box:
                handle = self.selected_box.get_handle_at(img_point)
                if handle:
                    self.is_resizing = True
                    self.resize_handle = handle
                    self.drag_start_pos = img_point
                    return
            
            # 检查是否点击了某个框
            clicked_box = None
            for box in reversed(self.boxes):  # 从后往前检查（上层优先）
                if box.contains(img_point):
                    clicked_box = box
                    break
            
            if clicked_box:
                # 选中框并开始拖拽
                self._select_box(clicked_box)
                self.is_dragging = True
                self.drag_start_pos = img_point
            else:
                # 点击空白处，取消选中
                self._deselect_all()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if self.cv_image is None:
            return
            
        pos = event.pos()
        img_pos = self.widget_to_image(pos.x(), pos.y())
        img_point = QPoint(img_pos[0], img_pos[1])
        
        # 添加模式 - 绘制临时框
        if self.is_adding_mode and self.add_start_pos:
            start_widget = self.image_to_widget(self.add_start_pos.x(), self.add_start_pos.y())
            self.temp_rect = QRect(start_widget, pos).normalized()
            self.update()
            return
        
        # 调整大小
        if self.is_resizing and self.selected_box and self.drag_start_pos:
            dx = img_point.x() - self.drag_start_pos.x()
            dy = img_point.y() - self.drag_start_pos.y()
            self.selected_box.resize(self.resize_handle, dx, dy)
            self.drag_start_pos = img_point
            self.update()
            return
        
        # 拖拽移动
        if self.is_dragging and self.selected_box and self.drag_start_pos:
            dx = img_point.x() - self.drag_start_pos.x()
            dy = img_point.y() - self.drag_start_pos.y()
            self.selected_box.move(dx, dy)
            self.drag_start_pos = img_point
            self.update()
            return
        
        # 更新鼠标样式
        self._update_cursor(img_point)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            # 添加模式 - 完成添加
            if self.is_adding_mode and self.add_start_pos:
                pos = event.pos()
                img_pos = self.widget_to_image(pos.x(), pos.y())
                
                x1, y1 = self.add_start_pos.x(), self.add_start_pos.y()
                x2, y2 = img_pos[0], img_pos[1]
                
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                x = min(x1, x2)
                y = min(y1, y2)
                
                # 最小尺寸检查
                if w >= 20 and h >= 20:
                    new_box = BoundingBox(x, y, w, h, len(self.boxes) + 1)
                    self.boxes.append(new_box)
                    self._select_box(new_box)
                    self.boxes_changed.emit(self.get_boxes())
                
                self.add_start_pos = None
                self.temp_rect = None
                self.is_adding_mode = False
                self.update()
                return
            
            # 结束拖拽或调整大小
            if self.is_dragging or self.is_resizing:
                self.boxes_changed.emit(self.get_boxes())
            
            self.is_dragging = False
            self.is_resizing = False
            self.resize_handle = None
            self.drag_start_pos = None
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件 - 删除选中框"""
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.delete_selected_box()
    
    def _select_box(self, box: BoundingBox):
        """选中指定框"""
        for b in self.boxes:
            b.selected = False
        box.selected = True
        self.selected_box = box
        self.box_selected.emit(box.index)
        self.update()
    
    def _deselect_all(self):
        """取消所有选中"""
        for box in self.boxes:
            box.selected = False
        self.selected_box = None
        self.update()
    
    def _update_cursor(self, img_point: QPoint):
        """根据位置更新鼠标样式"""
        if self.selected_box:
            handle = self.selected_box.get_handle_at(img_point)
            if handle:
                cursors = {
                    'tl': Qt.SizeFDiagCursor,
                    'br': Qt.SizeFDiagCursor,
                    'tr': Qt.SizeBDiagCursor,
                    'bl': Qt.SizeBDiagCursor,
                    't': Qt.SizeVerCursor,
                    'b': Qt.SizeVerCursor,
                    'l': Qt.SizeHorCursor,
                    'r': Qt.SizeHorCursor,
                }
                self.setCursor(cursors.get(handle, Qt.ArrowCursor))
                return
            elif self.selected_box.contains(img_point):
                self.setCursor(Qt.SizeAllCursor)
                return
        
        # 检查是否在其他框上
        for box in reversed(self.boxes):
            if box.contains(img_point):
                self.setCursor(Qt.OpenHandCursor)
                return
        
        self.setCursor(Qt.ArrowCursor)
    
    def delete_selected_box(self):
        """删除选中的框"""
        if self.selected_box:
            self.boxes.remove(self.selected_box)
            # 重新编号
            for i, box in enumerate(self.boxes):
                box.index = i + 1
            self.selected_box = None
            self.boxes_changed.emit(self.get_boxes())
            self.update()
    
    def start_add_mode(self):
        """开始添加模式"""
        self.is_adding_mode = True
        self._deselect_all()
        self.setCursor(Qt.CrossCursor)
    
    def cancel_add_mode(self):
        """取消添加模式"""
        self.is_adding_mode = False
        self.add_start_pos = None
        self.temp_rect = None
        self.setCursor(Qt.ArrowCursor)
        self.update()
    
    def resizeEvent(self, event):
        """大小改变时重新计算显示"""
        super().resizeEvent(event)
        self.update_display()


class BoxEditToolbar(QWidget):
    """框编辑工具栏"""
    
    add_clicked = Signal()
    delete_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 添加框按钮
        self.btn_add = QPushButton("➕ 添加框")
        self.btn_add.setToolTip("点击后在图像上拖拽绘制新框")
        self.btn_add.clicked.connect(self.add_clicked.emit)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
        """)
        layout.addWidget(self.btn_add)
        
        # 删除框按钮
        self.btn_delete = QPushButton("🗑️ 删除选中")
        self.btn_delete.setToolTip("删除当前选中的框 (也可按 Delete 键)")
        self.btn_delete.clicked.connect(self.delete_clicked.emit)
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:pressed { background-color: #b71c1c; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        layout.addWidget(self.btn_delete)
        
        # 提示标签
        self.label_hint = QLabel("提示：点击框选中，拖拽移动，拖拽手柄调整大小")
        self.label_hint.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.label_hint)
        
        layout.addStretch()
    
    def set_delete_enabled(self, enabled: bool):
        """设置删除按钮状态"""
        self.btn_delete.setEnabled(enabled)
