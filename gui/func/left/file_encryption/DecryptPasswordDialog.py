# -*- coding: utf-8 -*-
"""
解密密码弹窗组件
用于输入密码解密文件夹
"""

import os
from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QLineEdit,
    QPushButton, QHBoxLayout, QWidget, QGraphicsDropShadowEffect, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QCursor

from gui.func.utils.json_utils import JsonEditor


class DecryptPasswordDialog(QDialog):
    """解密密码输入弹窗"""
    
    def __init__(self, folder_path: str, parent=None):
        """
        初始化解密弹窗
        
        Args:
            folder_path: 加密文件夹路径，用于读取密码提示
            parent: 父窗口
        """
        super().__init__(parent)
        self._folder_path = folder_path
        self._password = None
        self._tip = self._read_tip_from_metadata()
        
        self._setup_ui()
        self._center_dialog()
    
    def _read_tip_from_metadata(self) -> str:
        """从 .metadata.json 读取密码提示"""
        try:
            editor = JsonEditor()
            detail_info = editor.read_file_metadata_infos(self._folder_path)
            if detail_info:
                return detail_info.get('tip', '')
        except Exception:
            pass
        return ''
    
    def _setup_ui(self):
        """设置界面"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 280)
        
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
        icon_label.setText("🔓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #FEF3C7;
                border-radius: 10px;
                font-size: 20px;
            }
        """)
        header_layout.addWidget(icon_label)
        
        # 标题文字
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title_label = QLabel("输入解密密码")
        title_label.setStyleSheet("""
            QLabel {
                color: #1F2937;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("请输入密码以解锁文件夹")
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
        
        # === 密码提示（如果有） ===
        if self._tip:
            tip_container = QWidget()
            tip_container.setStyleSheet("""
                QWidget {
                    background-color: #FFFBEB;
                    border: 1px solid #FCD34D;
                    border-radius: 8px;
                }
            """)
            tip_layout = QHBoxLayout(tip_container)
            tip_layout.setContentsMargins(12, 8, 12, 8)
            tip_layout.setSpacing(8)
            
            tip_icon = QLabel("💡")
            tip_icon.setStyleSheet("background: transparent; font-size: 14px;")
            tip_layout.addWidget(tip_icon)
            
            tip_text = QLabel(f"提示: {self._tip}")
            tip_text.setStyleSheet("""
                QLabel {
                    background: transparent;
                    color: #92400E;
                    font-size: 12px;
                    font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
                }
            """)
            tip_text.setWordWrap(True)
            tip_layout.addWidget(tip_text, 1)
            
            container_layout.addWidget(tip_container)
        
        # === 密码输入 ===
        password_label = QLabel("密码")
        password_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        container_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入解密密码")
        self.password_input.setFixedHeight(36)
        self.password_input.setStyleSheet("""
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
                border: 1px solid #F59E0B;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        self.password_input.returnPressed.connect(self._on_confirm)
        container_layout.addWidget(self.password_input)
        
        # === 错误提示标签 ===
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            QLabel {
                color: #DC2626;
                font-size: 12px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
        """)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)
        
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
        
        # 解锁按钮
        unlock_btn = QPushButton("解锁")
        unlock_btn.setFixedSize(80, 34)
        unlock_btn.setCursor(QCursor(Qt.PointingHandCursor))
        unlock_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        unlock_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(unlock_btn)
        
        container_layout.addLayout(btn_layout)
        main_layout.addWidget(container)
    
    def _on_confirm(self):
        """确认按钮点击事件"""
        password = self.password_input.text()
        
        if not password:
            self._show_error("请输入密码")
            return
        
        self._password = password
        self.accept()
    
    def _show_error(self, message: str):
        """显示错误信息"""
        self.error_label.setText(message)
        self.error_label.show()
    
    def _center_dialog(self):
        """将弹窗居中显示"""
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)
    
    def get_password(self) -> str:
        """
        获取用户输入的密码
        
        Returns:
            str: 密码，如果用户取消则返回 None
        """
        return self._password


class DecryptSuccessDialog(QDialog):
    """解密成功弹窗"""
    
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
        icon_label.setText("🔓")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #D1FAE5;
                border-radius: 24px;
                font-size: 24px;
            }
        """)
        
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()
        container_layout.addLayout(icon_layout)
        
        # 标题
        title_label = QLabel("解密成功")
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
        subtitle_label = QLabel("文件夹已成功解锁")
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
    
    # 测试带提示的弹窗
    dialog = DecryptPasswordDialog("/test/path")
    dialog._tip = "我的生日"
    if dialog.exec():
        password = dialog.get_password()
        print(f"密码: {password}")
    
    sys.exit(0)
