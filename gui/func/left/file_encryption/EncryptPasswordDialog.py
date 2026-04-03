# -*- coding: utf-8 -*-
"""
加密密码弹窗组件
用于设置文件夹加密密码和密码提示
"""

from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QLineEdit,
    QPushButton, QHBoxLayout, QWidget, QGraphicsDropShadowEffect, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QCursor


class EncryptPasswordDialog(QDialog):
    """加密密码设置弹窗"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._password = None
        self._tip = None
        
        self._setup_ui()
        self._center_dialog()
    
    def _setup_ui(self):
        """设置界面"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 360)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 主容器
        container = QWidget()
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            #dialogContainer {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(28, 24, 28, 20)
        container_layout.setSpacing(14)
        
        # === 标题区域 ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(40, 40)
        icon_label.setText("🔐")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #EEF2FF;
                border-radius: 10px;
                font-size: 20px;
            }
        """)
        header_layout.addWidget(icon_label)
        
        # 标题文字
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title_label = QLabel("设置加密密码")
        title_label.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("为文件夹设置访问密码")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 12px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)
        
        # === 密码输入 ===
        self.password_input = self._create_input("密码", "请输入密码", True)
        container_layout.addWidget(self.password_input['label'])
        container_layout.addWidget(self.password_input['edit'])
        
        # === 确认密码 ===
        self.confirm_input = self._create_input("确认密码", "请再次输入密码", True)
        container_layout.addWidget(self.confirm_input['label'])
        container_layout.addWidget(self.confirm_input['edit'])
        
        # === 密码提示 ===
        self.tip_input = self._create_input("密码提示（可选）", "输入提示帮助您回忆密码", False)
        container_layout.addWidget(self.tip_input['label'])
        container_layout.addWidget(self.tip_input['edit'])
        
        container_layout.addStretch()
        
        # === 按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 34)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #6B7280;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        # 确认按钮
        confirm_btn = QPushButton("确认加密")
        confirm_btn.setFixedSize(100, 34)
        confirm_btn.setCursor(QCursor(Qt.PointingHandCursor))
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)
        
        container_layout.addLayout(btn_layout)
        main_layout.addWidget(container)
    
    def _create_input(self, label_text, placeholder, is_password=False):
        """创建输入框组件"""
        label = QLabel(label_text)
        label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(36)
        if is_password:
            edit.setEchoMode(QLineEdit.Password)
        
        edit.setStyleSheet("""
            QLineEdit {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #1F2937;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #6366F1;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        
        return {'label': label, 'edit': edit}
    
    def _on_confirm(self):
        """确认按钮点击事件"""
        password = self.password_input['edit'].text()
        confirm = self.confirm_input['edit'].text()
        tip = self.tip_input['edit'].text()
        
        if not password:
            QMessageBox.warning(self, "提示", "请输入密码")
            return
        
        if len(password) < 4:
            QMessageBox.warning(self, "提示", "密码长度至少为4位")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            return
        
        self._password = password
        self._tip = tip
        self.accept()
    
    def _center_dialog(self):
        """将弹窗居中显示"""
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)
    
    def get_password_data(self):
        """
        获取密码数据
        
        Returns:
            tuple: (password, tip) 或 (None, None) 如果用户取消
        """
        return self._password, self._tip


class EncryptSuccessDialog(QDialog):
    """加密成功弹窗"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._center_dialog()
    
    def _setup_ui(self):
        """设置界面"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 180)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 主容器
        container = QWidget()
        container.setObjectName("successContainer")
        container.setStyleSheet("""
            #successContainer {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 20)
        container_layout.setSpacing(12)
        
        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setText("✓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #10B981;
                color: white;
                border-radius: 24px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()
        container_layout.addLayout(icon_layout)
        
        # 标题
        title_label = QLabel("加密成功")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #065F46;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        container_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("文件夹已成功加密")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 12px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        container_layout.addWidget(subtitle_label)
        
        # 确定按钮
        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(100, 34)
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        main_layout.addWidget(container)
    
    def _center_dialog(self):
        """将弹窗居中显示"""
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    
    dialog = EncryptPasswordDialog()
    if dialog.exec():
        password, tip = dialog.get_password_data()
        print(f"密码: {password}, 提示: {tip}")
    
    sys.exit(0)
