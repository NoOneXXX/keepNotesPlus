"""
颜色选择器对话框
提供15种可自定义的颜色选择，用于设置树节点字体颜色
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QLineEdit, QColorDialog, QApplication
)
from PySide6.QtGui import QColor, QPalette, QFont, QCursor
from PySide6.QtCore import Qt, Signal


class ColorPickerDialog(QDialog):
    """颜色选择器对话框"""
    
    # 信号：当颜色被选择时发射 (color_hex: str)
    color_selected = Signal(str)
    
    # 默认15种颜色（十六进制）
    DEFAULT_COLORS = [
        "#000000",  # 黑色
        "#FF0000",  # 红色
        "#00FF00",  # 绿色
        "#0000FF",  # 蓝色
        "#FFFF00",  # 黄色
        "#FF00FF",  # 紫色
        "#00FFFF",  # 青色
        "#FFA500",  # 橙色
        "#800080",  # 深紫
        "#FFC0CB",  # 粉色
        "#A52A2A",  # 棕色
        "#808080",  # 灰色
        "#008000",  # 深绿
        "#800000",  # 深红
        "#000080",  # 深蓝
    ]
    
    def __init__(self, parent=None, current_color="", custom_colors=None):
        """
        初始化颜色选择器
        
        Args:
            parent: 父窗口
            current_color: 当前选中的颜色（十六进制）
            custom_colors: 自定义颜色列表（15个十六进制颜色字符串）
        """
        super().__init__(parent)
        
        self.current_color = current_color if current_color else "#000000"
        self.custom_colors = custom_colors if custom_colors else self.DEFAULT_COLORS.copy()
        
        # 确保有15个颜色
        while len(self.custom_colors) < 15:
            self.custom_colors.append(self.DEFAULT_COLORS[len(self.custom_colors)])
        self.custom_colors = self.custom_colors[:15]  # 只取前15个
        
        self.selected_color = self.current_color
        self.color_buttons = []
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("设置字体颜色")
        self.setFixedSize(400, 350)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("选择字体颜色")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # 颜色网格
        self.color_grid = QGridLayout()
        self.color_grid.setSpacing(12)
        
        for i, color in enumerate(self.custom_colors):
            row = i // 5
            col = i % 5
            btn = self._create_color_button(color, i)
            self.color_grid.addWidget(btn, row, col)
            self.color_buttons.append(btn)
            
        layout.addLayout(self.color_grid)
        
        # 当前颜色显示
        current_layout = QHBoxLayout()
        current_layout.setSpacing(10)
        
        current_label = QLabel("当前颜色:")
        current_label.setFont(QFont("Microsoft YaHei", 11))
        current_layout.addWidget(current_label)
        
        self.current_color_preview = QLabel()
        self.current_color_preview.setFixedSize(40, 24)
        self._update_color_preview(self.current_color)
        current_layout.addWidget(self.current_color_preview)
        
        self.current_color_input = QLineEdit(self.current_color)
        self.current_color_input.setFont(QFont("Consolas", 10))
        self.current_color_input.setMaxLength(7)
        self.current_color_input.textChanged.connect(self._on_input_changed)
        current_layout.addWidget(self.current_color_input, 1)
        
        layout.addLayout(current_layout)
        
        # 自定义颜色按钮
        custom_btn = QPushButton("自定义颜色...")
        custom_btn.setCursor(QCursor(Qt.PointingHandCursor))
        custom_btn.clicked.connect(self._open_color_dialog)
        layout.addWidget(custom_btn)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
        
    def _create_color_button(self, color, index):
        """创建颜色按钮"""
        btn = QPushButton()
        btn.setFixedSize(50, 50)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setProperty("color_index", index)
        btn.setProperty("color_value", color)
        
        # 设置按钮样式
        self._set_button_style(btn, color)
        
        btn.clicked.connect(lambda: self._on_color_clicked(index))
        return btn
        
    def _set_button_style(self, btn, color):
        """设置按钮样式"""
        # 判断是否需要白色边框（深色背景）
        border_color = "#FFFFFF" if self._is_dark_color(color) else "#E0E0E0"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                border: 3px solid #3B82F6;
            }}
            QPushButton:pressed {{
                border: 3px solid #2563EB;
            }}
        """)
        
    def _is_dark_color(self, color_hex):
        """判断颜色是否为深色"""
        try:
            color = QColor(color_hex)
            # 计算亮度 (0-255)
            brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
            return brightness < 128
        except:
            return False
            
    def _on_color_clicked(self, index):
        """颜色按钮点击事件"""
        color = self.custom_colors[index]
        self.selected_color = color
        self.current_color = color
        self.current_color_input.setText(color)
        self._update_color_preview(color)
        self._highlight_selected_button(index)
        
    def _highlight_selected_button(self, selected_index):
        """高亮选中的按钮"""
        for i, btn in enumerate(self.color_buttons):
            color = self.custom_colors[i]
            if i == selected_index:
                # 选中状态：蓝色边框
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        border: 4px solid #3B82F6;
                        border-radius: 8px;
                    }}
                """)
            else:
                # 普通状态
                self._set_button_style(btn, color)
                
    def _update_color_preview(self, color):
        """更新颜色预览"""
        self.current_color_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border: 1px solid #D1D5DB;
                border-radius: 4px;
            }}
        """)
        
    def _on_input_changed(self, text):
        """输入框内容改变事件"""
        text = text.strip().upper()
        if self._is_valid_hex_color(text):
            self.selected_color = text
            self.current_color = text
            self._update_color_preview(text)
            
    def _is_valid_hex_color(self, text):
        """验证是否为有效的十六进制颜色"""
        if not text:
            return False
        if not text.startswith("#"):
            return False
        if len(text) != 7:
            return False
        try:
            int(text[1:], 16)
            return True
        except ValueError:
            return False
            
    def _open_color_dialog(self):
        """打开系统颜色选择对话框"""
        color = QColorDialog.getColor(
            QColor(self.current_color),
            self,
            "选择自定义颜色"
        )
        if color.isValid():
            hex_color = color.name().upper()
            self.selected_color = hex_color
            self.current_color = hex_color
            self.current_color_input.setText(hex_color)
            self._update_color_preview(hex_color)
            
            # 更新自定义颜色列表中的第一个空位或替换当前选中的
            self._update_custom_colors(hex_color)
            
    def _update_custom_colors(self, new_color):
        """更新自定义颜色列表"""
        # 如果颜色已存在，不重复添加
        if new_color in self.custom_colors:
            idx = self.custom_colors.index(new_color)
            self._highlight_selected_button(idx)
            return
            
        # 替换第一个与默认值相同的颜色，或替换最后一个
        for i, color in enumerate(self.custom_colors):
            if color not in self.DEFAULT_COLORS:
                self.custom_colors[i] = new_color
                self._refresh_color_buttons()
                self._highlight_selected_button(i)
                return
                
        # 如果没有非默认颜色，替换最后一个
        self.custom_colors[-1] = new_color
        self._refresh_color_buttons()
        self._highlight_selected_button(len(self.custom_colors) - 1)
        
    def _refresh_color_buttons(self):
        """刷新颜色按钮显示"""
        for i, (btn, color) in enumerate(zip(self.color_buttons, self.custom_colors)):
            btn.setProperty("color_value", color)
            self._set_button_style(btn, color)
            
    def _on_confirm(self):
        """确认按钮点击事件"""
        if self._is_valid_hex_color(self.selected_color):
            self.color_selected.emit(self.selected_color)
            self.accept()
        else:
            # 显示错误提示
            self.current_color_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #EF4444;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
            """)
            
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 12px;
            }
            QLabel {
                color: #1F2937;
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            }
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: 'Consolas', monospace;
                background-color: #F9FAFB;
            }
            QLineEdit:focus {
                border: 2px solid #3B82F6;
                background-color: #FFFFFF;
            }
            QPushButton {
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton#custom_btn {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
            }
            QPushButton#custom_btn:hover {
                background-color: #E5E7EB;
            }
        """)
        
        # 设置按钮样式
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        
    def get_selected_color(self):
        """获取选中的颜色"""
        return self.selected_color
        
    def get_custom_colors(self):
        """获取自定义颜色列表"""
        return self.custom_colors.copy()


def show_color_picker(parent=None, current_color="", custom_colors=None):
    """
    显示颜色选择器对话框
    
    Args:
        parent: 父窗口
        current_color: 当前颜色（十六进制）
        custom_colors: 自定义颜色列表
        
    Returns:
        tuple: (是否确认, 选中的颜色, 自定义颜色列表)
    """
    dialog = ColorPickerDialog(parent, current_color, custom_colors)
    
    # 居中显示
    if parent:
        center_x = parent.x() + (parent.width() - dialog.width()) // 2
        center_y = parent.y() + (parent.height() - dialog.height()) // 2
        dialog.move(center_x, center_y)
        
    result = dialog.exec()
    
    if result == QDialog.Accepted:
        return True, dialog.get_selected_color(), dialog.get_custom_colors()
    else:
        return False, current_color, custom_colors


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    # 测试
    confirmed, color, colors = show_color_picker(current_color="#FF0000")
    print(f"Confirmed: {confirmed}, Color: {color}")
    print(f"Custom colors: {colors}")
    
    sys.exit(0)
