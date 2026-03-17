#!/usr/bin/env python3
"""
ViewCrop - 智能图像分割工具
版本：2.0 (带微调按钮和拖拽支持)
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QCheckBox, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QFrame,
    QGroupBox, QStatusBar, QToolButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QImage, QPixmap, QIcon, QPainter

# 核心模块
from core import ImageProcessor, AppConfig, i18n, tr

# 交互式视图组件
from ui.interactive_view import InteractiveImageView, BoxEditToolbar


class ImageItem:
    """图像项"""

    def __init__(self, file_path: str, processor: ImageProcessor):
        self.file_path = file_path
        self.base_name = Path(file_path).stem
        self.processor = processor
        self.source_image = None
        self.result = None
        self.dilate = AppConfig.ImageProcessing.DEFAULT_DILATE
        self.area = AppConfig.ImageProcessing.DEFAULT_AREA
        self.remove_horizontal = False
        self.remove_vertical = False

    def load_source(self) -> bool:
        self.source_image = self.processor.load_image(self.file_path)
        return self.source_image is not None

    def update_params(self, dilate: int, area: int, remove_h: bool, remove_v: bool):
        """更新处理参数"""
        self.dilate = dilate
        self.area = area
        self.remove_horizontal = remove_h
        self.remove_vertical = remove_v

    def process(self) -> bool:
        if self.source_image is None:
            return False
        self.processor.update_config(
            dilate=self.dilate, area=self.area,
            remove_h=self.remove_horizontal, remove_v=self.remove_vertical
        )
        self.result = self.processor.process_image(self.source_image)
        return self.result is not None
        self.area = AppConfig.ImageProcessing.DEFAULT_AREA  
        self.remove_horizontal = False
        self.remove_vertical = False
        
    def load_source(self) -> bool:
        self.source_image = self.processor.load_image(self.file_path)
        return self.source_image is not None
        
    def update_params(self, dilate: int, area: int, remove_h: bool, remove_v: bool):
        """更新处理参数"""
        self.dilate = dilate
        self.area = area
        self.remove_horizontal = remove_h
        self.remove_vertical = remove_v
        
    def process(self) -> bool:
        if self.source_image is None:
            return False
        self.processor.update_config(
            dilate=self.dilate, area=self.area,
            remove_h=self.remove_horizontal, remove_v=self.remove_vertical
        )
        self.result = self.processor.process_image(self.source_image)
        return self.result is not None


class ParameterSlider(QWidget):
    """参数滑块组件（带微调按钮）"""
    
    value_changed = Signal(int)
    
    def __init__(self, label: str, min_val: int, max_val: int, default_val: int, parent=None):
        super().__init__(parent)
        self.step = 1
        self.setup_ui(label, min_val, max_val, default_val)
        
    def setup_ui(self, label: str, min_val: int, max_val: int, default_val: int):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标签
        self.lbl = QLabel(label)
        self.lbl.setFixedWidth(60)
        layout.addWidget(self.lbl)
        
        # 减按钮
        self.btn_minus = QPushButton("-")
        self.btn_minus.setFixedSize(24, 24)
        self.btn_minus.setEnabled(min_val < default_val)
        layout.addWidget(self.btn_minus)
        
        # 滑块
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        self.slider.valueChanged.connect(self._on_value_change)
        layout.addWidget(self.slider, stretch=1)
        
        # 加按钮
        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedSize(24, 24)
        self.btn_plus.setEnabled(default_val < max_val)
        layout.addWidget(self.btn_plus)
        
        # 数值显示
        self.value_label = QLabel(str(default_val))
        self.value_label.setFixedWidth(50)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                border-radius: 3px;
                font-weight: bold;
                font-family: monospace;
            }
        """)
        layout.addWidget(self.value_label)
        
        # 样式设置
        btn_style = """
            QPushButton {
                background-color: #2D2D2D; color: #E0E0E0;
                border: 1px solid #555555; border-radius: 3px;
                font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #3D3D3D; }
            QPushButton:pressed { background-color: #1E1E1E; }
            QPushButton:disabled { background-color: #1E1E1E; color: #666666; border-color: #444444; }
        """
        self.btn_minus.setStyleSheet(btn_style)
        self.btn_plus.setStyleSheet(btn_style)
        
        # 信号连接
        self.btn_minus.clicked.connect(lambda: self.adjust_value(-self.step))
        self.btn_plus.clicked.connect(lambda: self.adjust_value(self.step))
        
    def _on_value_change(self, val: int):
        self.value_label.setText(str(val))
        self._update_button_states()
        self.value_changed.emit(val)
        
    def _update_button_states(self):
        current_val = self.slider.value()
        min_val = self.slider.minimum()
        max_val = self.slider.maximum()
        self.btn_minus.setEnabled(current_val > min_val)
        self.btn_plus.setEnabled(current_val < max_val)
        
    def adjust_value(self, delta: int):
        current_val = self.slider.value()
        new_val = max(self.slider.minimum(), min(self.slider.maximum(), current_val + delta))
        self.slider.setValue(new_val)
        
    def set_step(self, step: int):
        self.step = step
        
    def value(self) -> int:
        return self.slider.value()
        
    def setValue(self, val: int):
        self.slider.setValue(val)
        
    def minimum(self) -> int:
        return self.slider.minimum()
        
    def maximum(self) -> int:
        return self.slider.maximum()
        
    def blockSignals(self, block: bool):
        self.slider.blockSignals(block)
        self.value_label.blockSignals(block)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.processor = ImageProcessor()
        self.image_items: Dict[str, ImageItem] = {}
        self.current_item: Optional[ImageItem] = None

        # 预览模式：0=手动修正结果, 1=自动识别区域
        self.preview_mode = 0
        self.processing_mask = None  # 保存二值化掩膜

        # 启用拖放
        self.setAcceptDrops(True)

        # 注册语言变更监听
        i18n.add_listener(self.on_language_changed)

        self.setup_ui()
        self.load_styles()
        self.update_ui_text()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, stretch=3)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
    def create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 图像预览 - 支持手动修正结果和自动识别区域切换
        self.image_panel = QGroupBox()
        image_layout = QVBoxLayout(self.image_panel)
        image_layout.setSpacing(8)

        # 预览模式切换按钮
        preview_mode_layout = QHBoxLayout()
        preview_mode_layout.setSpacing(5)

        self.btn_mode_result = QToolButton()
        self.btn_mode_result.setCheckable(True)
        self.btn_mode_result.setChecked(True)
        self.btn_mode_result.clicked.connect(lambda: self.set_preview_mode(0))
        self.btn_mode_result.setStyleSheet("""
            QToolButton {
                color: #E0E0E0; background: #2D2D2D; border: 1px solid #555555;
                padding: 6px 12px; border-radius: 4px; font-size: 11px;
            }
            QToolButton:hover { background: #404040; }
            QToolButton:checked {
                background: #2196F3; color: white; border-color: #2196F3;
            }
        """)

        self.btn_mode_mask = QToolButton()
        self.btn_mode_mask.setCheckable(True)
        self.btn_mode_mask.clicked.connect(lambda: self.set_preview_mode(1))
        self.btn_mode_mask.setStyleSheet("""
            QToolButton {
                color: #E0E0E0; background: #2D2D2D; border: 1px solid #555555;
                padding: 6px 12px; border-radius: 4px; font-size: 11px;
            }
            QToolButton:hover { background: #404040; }
            QToolButton:checked {
                background: #FFFFFF; color: #000000; border-color: #FFFFFF;
            }
        """)

        preview_mode_layout.addWidget(self.btn_mode_result)
        preview_mode_layout.addWidget(self.btn_mode_mask)
        preview_mode_layout.addStretch()

        image_layout.addLayout(preview_mode_layout)

        # 框编辑工具栏
        self.box_toolbar = BoxEditToolbar()
        self.box_toolbar.add_clicked.connect(self.on_add_box)
        self.box_toolbar.delete_clicked.connect(self.on_delete_box)
        image_layout.addWidget(self.box_toolbar)

        # 预览图像 - 使用交互式视图
        self.label_result = InteractiveImageView()
        self.label_result.setMinimumSize(600, 400)
        self.label_result.boxes_changed.connect(self.on_boxes_changed)
        self.label_result.box_selected.connect(self.on_box_selected)
        image_layout.addWidget(self.label_result)

        # 预览说明标签
        self.preview_info_label = QLabel()
        self.preview_info_label.setStyleSheet("color: #888888; font-size: 11px; padding: 2px;")
        image_layout.addWidget(self.preview_info_label)

        layout.addWidget(self.image_panel)
        
        # 文件列表
        self.list_panel = QGroupBox()
        list_layout = QVBoxLayout(self.list_panel)
        
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(120)
        self.file_list.itemSelectionChanged.connect(self.on_file_selected)
        list_layout.addWidget(self.file_list)
        
        button_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("添加文件")
        self.btn_load.clicked.connect(self.load_files)
        
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.clicked.connect(self.clear_files)
        
        button_layout.addWidget(self.btn_load)
        button_layout.addWidget(self.btn_clear)
        list_layout.addLayout(button_layout)
        
        layout.addWidget(self.list_panel)
        
        return panel
        
    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(AppConfig.UI.SIDEBAR_WIDTH)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # 语言切换按钮
        self.btn_language = QPushButton()
        self.btn_language.clicked.connect(self.on_toggle_language)
        self.btn_language.setStyleSheet("""
            QPushButton {
                background-color: #607D8B; color: white;
                border: none; padding: 8px; border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        layout.addWidget(self.btn_language)
        
        # 融合度
        self.dilate_label = QLabel()
        self.dilate_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addWidget(self.dilate_label)
        
        self.slider_dilate = ParameterSlider(
            "", 
            AppConfig.ImageProcessing.DILATE_MIN,
            AppConfig.ImageProcessing.DILATE_MAX,
            AppConfig.ImageProcessing.DEFAULT_DILATE
        )
        self.slider_dilate.set_step(1)
        self.slider_dilate.value_changed.connect(self.on_params_changed)
        layout.addWidget(self.slider_dilate)
        
        # 过滤阈值
        self.area_label_title = QLabel()
        self.area_label_title.setStyleSheet("font-weight: bold; color: #FF9800;")
        layout.addWidget(self.area_label_title)
        
        self.slider_area = ParameterSlider(
            "",
            AppConfig.ImageProcessing.AREA_MIN,
            AppConfig.ImageProcessing.AREA_MAX,
            AppConfig.ImageProcessing.DEFAULT_AREA
        )
        self.slider_area.set_step(100)
        self.slider_area.value_changed.connect(self.on_params_changed)
        layout.addWidget(self.slider_area)
        
        # 干扰线过滤选项
        self.chk_horizontal = QCheckBox()
        self.chk_horizontal.stateChanged.connect(self.on_params_changed)
        layout.addWidget(self.chk_horizontal)
        
        self.chk_vertical = QCheckBox()
        self.chk_vertical.stateChanged.connect(self.on_params_changed)
        layout.addWidget(self.chk_vertical)
        
        # 检测统计
        self.info_group = QGroupBox()
        info_layout = QVBoxLayout(self.info_group)
        
        self.label_info = QLabel()
        self.label_info.setWordWrap(True)
        self.label_info.setStyleSheet("""
            QLabel { background-color: #2D2D2D; padding: 8px; border-radius: 4px; font-size: 9px; }
        """)
        info_layout.addWidget(self.label_info)
        
        # 大号区域数量显示
        count_widget = QWidget()
        count_layout = QVBoxLayout(count_widget)
        count_layout.setContentsMargins(0, 0, 0, 0)
        
        self.label_count = QLabel("0")
        self.label_count.setAlignment(Qt.AlignCenter)
        self.label_count.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #CCCCCC, stop: 1 #CCCCCC);
                color: #666666; font-size: 24px; font-weight: bold;
                padding: 10px; border-radius: 8px; margin: 5px 0;
            }
        """)
        count_layout.addWidget(self.label_count)
        
        self.count_label = QLabel()
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("color: #888888; font-size: 12px;")
        count_layout.addWidget(self.count_label)
        
        info_layout.addWidget(count_widget)
        layout.addWidget(self.info_group)
        
        # 导出按钮
        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; font-weight: bold; padding: 10px; border-radius: 5px; font-size: 12px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #CCCCCC; color: #666666; }
        """)
        layout.addWidget(self.btn_export)

        layout.addStretch()
        
        return panel
        
    def load_styles(self):
        style = """
        QMainWindow { background-color: #1E1E1E; color: #E0E0E0; }
        QGroupBox {
            font-weight: bold; border: 2px solid #404040; border-radius: 8px; margin-top: 10px; padding-top: 10px;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }
        QSlider::groove:horizontal { height: 6px; background: #404040; border-radius: 3px; }
        QSlider::handle:horizontal { background: #2196F3; width: 16px; margin: -5px 0; border-radius: 8px; }
        QCheckBox { spacing: 5px; }
        QPushButton { border: 1px solid #555555; padding: 5px; border-radius: 4px; background-color: #2D2D2D; }
        QPushButton:hover { background-color: #404040; }
        """
        self.setStyleSheet(style)
        
    def load_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, tr('add_files'), "",
            f"Images (*{' *'.join(AppConfig.SUPPORTED_FORMATS)})"
        )
        
        if files:
            self.add_files(files)
            
    def add_files(self, files: List[str]):
        for file_path in files:
            if file_path not in self.image_items:
                item = ImageItem(file_path, self.processor)
                
                if item.load_source():
                    self.image_items[file_path] = item
                    
                    list_item = QListWidgetItem(item.base_name)
                    list_item.setData(Qt.UserRole, file_path)
                    self.file_list.addItem(list_item)
                else:
                    QMessageBox.warning(self, tr('error'), tr('cannot_load_image', Path(file_path).name))
        
        self.btn_export.setEnabled(bool(self.image_items))
        
        if not self.current_item and self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            
    def clear_files(self):
        self.image_items.clear()
        self.current_item = None
        self.file_list.clear()
        self.reset_display()
        self.btn_export.setEnabled(False)
        
    def on_file_selected(self):
        items = self.file_list.selectedItems()
        if not items:
            self.current_item = None
            self.reset_display()
            return
            
        file_path = items[0].data(Qt.UserRole)
        if file_path in self.image_items:
            self.current_item = self.image_items[file_path]
            self.load_current_image()
            
    def load_current_image(self):
        if not self.current_item:
            return

        self.block_param_signals(True)
        self.slider_dilate.setValue(self.current_item.dilate)
        self.slider_area.setValue(self.current_item.area)
        self.chk_horizontal.setChecked(self.current_item.remove_horizontal)
        self.chk_vertical.setChecked(self.current_item.remove_vertical)
        self.block_param_signals(False)

        if self.current_item.source_image is not None:
            h, w = self.current_item.source_image.shape[:2]
            self.label_info.setText(
                f"{tr('file')}：{self.current_item.base_name}\n"
                f"{tr('size')}：{w} x {h}\n"
                f"{tr('path')}：{Path(self.current_item.file_path).parent.name}"
            )
        else:
            self.label_info.setText(tr('cannot_load_image', ''))
            return

        self.process_current_image()
        
    def process_current_image(self):
        if not self.current_item:
            return

        self.status_bar.showMessage(tr('processing'))

        if self.current_item.process():
            # 保存二值化掩膜用于预览
            result = self.current_item.result
            if result:
                self.processing_mask = result.mask

            self.display_results()
            regions = len(self.current_item.result.boxes)
            self.update_region_count(regions)
            self.status_bar.showMessage(tr('processing_complete', regions))
        else:
            self.status_bar.showMessage(tr('processing_failed'))

    def set_preview_mode(self, mode):
        """设置预览模式"""
        self.preview_mode = mode
        self.btn_mode_result.setChecked(mode == 0)
        self.btn_mode_mask.setChecked(mode == 1)

        # 更新说明标签
        if mode == 0:
            self.preview_info_label.setText(tr('show_manual_result'))
            self.preview_info_label.setStyleSheet("color: #888888; font-size: 11px; padding: 2px;")
        elif mode == 1:
            self.preview_info_label.setText(tr('show_auto_region'))
            self.preview_info_label.setStyleSheet("color: #FFFFFF; font-size: 11px; padding: 2px;")

        # 重新显示
        self.display_results()

    def display_results(self):
        if not self.current_item or not self.current_item.result:
            return

        # 根据预览模式显示不同图像
        if self.preview_mode == 0:
            # 最终结果（带标注）- 使用交互式视图
            self.label_result.set_cv_image(self.current_item.result.preview)
            self.label_result.set_boxes(self.current_item.result.boxes)
        elif self.preview_mode == 1 and self.processing_mask is not None:
            # 二值化掩膜（带绿框标注）
            mask_with_boxes = self.processor.create_mask_preview(
                self.processing_mask, 
                self.current_item.result.boxes
            )
            self.label_result.set_cv_image(mask_with_boxes)
            self.label_result.set_boxes(self.current_item.result.boxes)
        
    def show_cv2_img(self, cv2_img, label):
        try:
            if cv2_img is None:
                return
                
            import cv2
            if len(cv2_img.shape) == 3:
                rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
            else:
                rgb = cv2.cvtColor(cv2_img, cv2.COLOR_GRAY2RGB)
                
            h, w, c = rgb.shape
            bytes_per_line = c * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimg)
            scaled_pixmap = pixmap.scaled(
                label.width() - 4, label.height() - 4,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"[ERROR] 显示图像失败：{e}")
            label.setText("显示错误")
        
    def update_region_count(self, count: int):
        """更新区域计数显示（带颜色变化）"""
        self.label_count.setText(str(count))
        
        if count == 0:
            color = "#F44336"  # 红色
        elif count < 5:
            color = "#FF9800"  # 橙色
        elif count < 20:
            color = "#4CAF50"  # 绿色
        else:
            color = "#2196F3"  # 蓝色
            
        self.label_count.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {color}, stop: 1 {color});
                color: white; font-size: 24px; font-weight: bold;
                padding: 10px; border-radius: 8px; margin: 5px 0;
            }}
        """)
        
    def on_params_changed(self):
        if not self.current_item:
            return
            
        self.current_item.update_params(
            dilate=self.slider_dilate.value(),
            area=self.slider_area.value(),
            remove_h=self.chk_horizontal.isChecked(),
            remove_v=self.chk_vertical.isChecked()
        )
        
        self.process_current_image()
        
    def block_param_signals(self, block: bool):
        self.slider_dilate.blockSignals(block)
        self.slider_area.blockSignals(block)
        self.chk_horizontal.blockSignals(block)
        self.chk_vertical.blockSignals(block)
        
    def reset_display(self):
        # 重置显示
        self.label_result.set_cv_image(None)
        self.label_result.set_boxes([])
        self.label_info.setText(tr('no_image'))
        self.label_count.setText("0")
        self.label_count.setStyleSheet("""
            QLabel {
                background-color: #CCCCCC; color: #666666;
                font-size: 24px; font-weight: bold;
                padding: 10px; border-radius: 8px; margin: 5px 0;
            }
        """)

        # 重置预览模式
        self.processing_mask = None
        self.box_toolbar.set_delete_enabled(False)
        
    def export_results(self):
        if not self.image_items:
            return
            
        export_dir = QFileDialog.getExistingDirectory(self, tr('export_results'))
        if not export_dir:
            return
            
        export_count = 0
        
        for item in self.image_items.values():
            # 使用当前编辑后的框（如果有）
            boxes = self.label_result.get_boxes() if item == self.current_item else item.result.boxes
            
            if item.result and boxes:
                output_dir = Path(export_dir) / item.base_name
                output_dir.mkdir(parents=True, exist_ok=True)
                
                crops = self.processor.crop_boxes(item.source_image, boxes)
                
                for i, crop in enumerate(crops, 1):
                    filename = f"{item.base_name}_{i}.png"
                    output_path = output_dir / filename
                    
                    if self.processor.save_image(crop, str(output_path)):
                        export_count += 1
                        
        QMessageBox.information(
            self, 
            tr('export_finished'), 
            tr('export_success', export_count, export_dir)
        )
        
        self.status_bar.showMessage(tr('export_complete', export_count))
    
    def on_add_box(self):
        """开始添加框模式"""
        if not self.current_item or not self.current_item.result:
            QMessageBox.warning(self, tr('warning'), tr('add_box_first'))
            return
        self.label_result.start_add_mode()
        self.status_bar.showMessage("Add mode: Drag on image to draw new box" if i18n.current_lang == 'en' else "添加模式：在图像上拖拽绘制新框")
    
    def on_delete_box(self):
        """删除选中的框"""
        self.label_result.delete_selected_box()
        self.box_toolbar.set_delete_enabled(False)
        self.status_bar.showMessage("Box deleted" if i18n.current_lang == 'en' else "已删除选中框")
    
    def on_boxes_changed(self, boxes: List[tuple]):
        """框发生变化时更新数据"""
        if self.current_item and self.current_item.result:
            # 更新结果中的框
            self.current_item.result.boxes = boxes
            # 更新区域计数
            self.update_region_count(len(boxes))
            self.status_bar.showMessage(tr('box_updated', len(boxes)))
    
    def on_box_selected(self, index: int):
        """框被选中时更新工具栏"""
        self.box_toolbar.set_delete_enabled(True)
        self.status_bar.showMessage(tr('box_selected', index))

    def on_toggle_language(self):
        """切换语言"""
        i18n.toggle_language()

    def on_language_changed(self, lang: str):
        """语言变更回调"""
        self.update_ui_text()
        # 刷新当前显示
        if self.current_item:
            self.load_current_image()

    def update_ui_text(self):
        """更新所有UI文本"""
        # 窗口标题
        self.setWindowTitle(tr('app_title'))

        # 图像预览面板
        self.image_panel.setTitle(tr('image_preview'))
        self.btn_mode_result.setText(tr('manual_result'))
        self.btn_mode_mask.setText(tr('auto_detect_region'))

        # 预览说明标签
        if self.preview_mode == 0:
            self.preview_info_label.setText(tr('show_manual_result'))
        else:
            self.preview_info_label.setText(tr('show_auto_region'))

        # 框编辑工具栏
        self.box_toolbar.btn_add.setText(tr('add_box'))
        self.box_toolbar.btn_add.setToolTip(tr('add_box_tooltip'))
        self.box_toolbar.btn_delete.setText(tr('delete_selected'))
        self.box_toolbar.btn_delete.setToolTip(tr('delete_tooltip'))
        self.box_toolbar.label_hint.setText(tr('edit_hint'))

        # 文件列表面板
        self.list_panel.setTitle(tr('file_list'))
        self.btn_load.setText(tr('add_files'))
        self.btn_clear.setText(tr('clear_list'))

        # 参数标签
        self.dilate_label.setText(tr('dilate'))
        self.slider_dilate.lbl.setText(tr('dilate_label'))
        self.area_label_title.setText(tr('area'))
        self.slider_area.lbl.setText(tr('area_label'))

        # 干扰线过滤
        self.chk_horizontal.setText(tr('filter_horizontal'))
        self.chk_horizontal.setToolTip(tr('filter_horizontal_tooltip'))
        self.chk_vertical.setText(tr('filter_vertical'))
        self.chk_vertical.setToolTip(tr('filter_vertical_tooltip'))

        # 统计面板
        self.info_group.setTitle(tr('detection_stats'))
        if not self.current_item:
            self.label_info.setText(tr('no_image'))
        self.count_label.setText(tr('detected_regions'))

        # 导出按钮
        self.btn_export.setText(tr('export_results'))

        # 语言按钮
        current_lang_name = i18n.LANGUAGES.get(i18n.current_lang, '中文')
        self.btn_language.setText(f"🌐 {current_lang_name}")

        # 状态栏
        if not self.current_item:
            self.status_bar.showMessage(tr('ready'))
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_item:
            self.display_results()
    
    def dragEnterEvent(self, event):
        """拖入文件事件"""
        try:
            if event.mimeData().hasUrls():
                urls = event.mimeData().urls()
                
                image_extensions = AppConfig.SUPPORTED_FORMATS
                has_image = False
                
                for url in urls:
                    file_path = url.toLocalFile()
                    if file_path and file_path.lower().endswith(image_extensions):
                        has_image = True
                        break
                
                if has_image:
                    event.acceptProposedAction()
                    return
                
            event.ignore()
            
        except Exception as e:
            print(f"[WARN] 拖入检测失败：{e}")
            event.ignore()
    
    def dragLeaveEvent(self, event):
        pass
    
    def dropEvent(self, event):
        """放下文件事件"""
        try:
            if not event.mimeData().hasUrls():
                event.ignore()
                return
            
            urls = event.mimeData().urls()
            image_extensions = AppConfig.SUPPORTED_FORMATS
            image_files = []
            
            for url in urls:
                file_path = url.toLocalFile()
                if file_path and file_path.lower().endswith(image_extensions):
                    image_files.append(file_path)
            
            if image_files:
                self.add_files(image_files)
                self.status_bar.showMessage(f"Added {len(image_files)} files" if i18n.current_lang == 'en' else f"添加了 {len(image_files)} 个文件")
                
            event.acceptProposedAction()
            
        except Exception as e:
            print(f"[ERROR] 处理拖入文件失败：{e}")
            import traceback
            traceback.print_exc()
            event.ignore()