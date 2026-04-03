# -*- coding: utf-8 -*-
"""
优化后的加密密码弹窗组件
保持原有的类名、方法名和参数接口，仅优化视觉效果
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
        """设置界面 - 优化视觉样式"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 420)  # 稍微调整宽高比

        # 更加平滑的弥散阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 45))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 主容器
        container = QWidget()
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            #dialogContainer {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #F3F4F6;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 25)
        container_layout.setSpacing(0)

        # === 标题区域 ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        icon_label = QLabel()
        icon_label.setFixedSize(44, 44)
        icon_label.setText("🛡️")  # 使用盾牌或锁
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #F5F3FF;
                border-radius: 12px;
                font-size: 22px;
            }
        """)
        header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel("安全加密")
        title_label.setStyleSheet("""
            QLabel {
                color: #111827;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI';
            }
        """)
        subtitle_label = QLabel("为您的文件夹添加密码保护")
        subtitle_label.setStyleSheet("color: #6B7280; font-size: 12px;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        container_layout.addLayout(header_layout)
        container_layout.addSpacing(25)  # 留白

        # === 密码输入 ===
        self.password_input = self._create_input("设置密码", "输入新密码", True)
        container_layout.addWidget(self.password_input['label'])
        container_layout.addWidget(self.password_input['edit'])
        container_layout.addSpacing(15)

        # === 确认密码 ===
        self.confirm_input = self._create_input("确认密码", "再次输入密码", True)
        container_layout.addWidget(self.confirm_input['label'])
        container_layout.addWidget(self.confirm_input['edit'])
        container_layout.addSpacing(15)

        # === 密码提示 ===
        self.tip_input = self._create_input("密码提示", "可选，帮助您找回密码", False)
        container_layout.addWidget(self.tip_input['label'])
        container_layout.addWidget(self.tip_input['edit'])

        container_layout.addStretch()

        # === 按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(90, 38)
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #9CA3AF;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton("确认设置")
        confirm_btn.setFixedSize(110, 38)
        confirm_btn.setCursor(QCursor(Qt.PointingHandCursor))
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366F1;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4F46E5;
            }
            QPushButton:pressed {
                background-color: #4338CA;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)

        container_layout.addLayout(btn_layout)
        main_layout.addWidget(container)

    def _create_input(self, label_text, placeholder, is_password=False):
        """创建输入框组件 - 增强焦点样式"""
        label = QLabel(label_text)
        label.setStyleSheet("color: #4B5563; font-size: 13px; font-weight: 600; margin-bottom: 5px;")

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setFixedHeight(40)  # 稍微加高，更现代
        if is_password:
            edit.setEchoMode(QLineEdit.Password)

        edit.setStyleSheet("""
            QLineEdit {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 0 15px;
                font-size: 13px;
                color: #111827;
            }
            QLineEdit:focus {
                background-color: #FFFFFF;
                border: 2px solid #6366F1;
            }
        """)

        return {'label': label, 'edit': edit}

    def _on_confirm(self):
        password = self.password_input['edit'].text()
        confirm = self.confirm_input['edit'].text()
        tip = self.tip_input['edit'].text()

        if not password:
            self._show_custom_warning("请输入密码")
            return
        if len(password) < 4:
            self._show_custom_warning("密码长度至少为4位")
            return
        if password != confirm:
            self._show_custom_warning("两次输入的密码不一致")
            return

        self._password = password
        self._tip = tip
        self.accept()

    def _show_custom_warning(self, text):
        """简单优化MessageBox外观"""
        msg = QMessageBox(self)
        msg.setWindowTitle("提示")
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; border-radius: 10px; }
            QPushButton { background-color: #6366F1; color: white; border-radius: 6px; width: 60px; height: 28px; }
        """)
        msg.exec()

    def _center_dialog(self):
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)

    def get_password_data(self):
        return self._password, self._tip


class EncryptSuccessDialog(QDialog):
    """加密成功弹窗 - 视觉优化"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._center_dialog()

    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 220)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 8)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container = QWidget()
        container.setObjectName("successContainer")
        container.setStyleSheet("#successContainer { background-color: #FFFFFF; border-radius: 20px; }")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 30, 20, 20)
        container_layout.setSpacing(15)

        # 成功图标
        icon_label = QLabel("✓")
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #D1FAE5;
                color: #059669;
                border-radius: 28px;
                font-size: 28px;
                font-weight: bold;
            }
        """)

        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon_label)
        icon_layout.addStretch()
        container_layout.addLayout(icon_layout)

        # 文字
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        title_label = QLabel("操作成功")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #111827; font-size: 16px; font-weight: bold;")

        subtitle_label = QLabel("文件夹已安全加密")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #6B7280; font-size: 13px;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        container_layout.addLayout(text_layout)

        # 确定按钮
        ok_btn = QPushButton("完成")
        ok_btn.setFixedSize(120, 36)
        ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        ok_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        container_layout.addLayout(btn_layout)

        main_layout.addWidget(container)

    def _center_dialog(self):
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    # 全局字体微调
    app.setFont(QFont("Microsoft YaHei UI", 9))

    dialog = EncryptPasswordDialog()
    if dialog.exec():
        password, tip = dialog.get_password_data()

        success = EncryptSuccessDialog()
        success.exec()

    sys.exit(0)