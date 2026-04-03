# -*- coding: utf-8 -*-
"""
深度视觉优化版 - 解密密码弹窗
1. 强化提示醒目度 (高对比度警示色)
2. 提升字体质感 (Semibold 权重)
3. 保持原始接口与变量名不变
"""

import os
from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QLineEdit,
    QPushButton, QHBoxLayout, QWidget, QGraphicsDropShadowEffect, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QCursor


class DecryptPasswordDialog(QDialog):
    """解密密码输入弹窗"""

    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self._folder_path = folder_path
        self._password = None
        self._tip = self._read_tip_from_metadata()

        self._setup_ui()
        self._center_dialog()

    def _read_tip_from_metadata(self) -> str:
        """保持原有逻辑不变"""
        try:
            from gui.func.utils.json_utils import JsonEditor
            editor = JsonEditor()
            detail_info = editor.read_file_metadata_infos(self._folder_path)
            if detail_info:
                return detail_info.get('tip', '')
        except Exception:
            pass
        return ''

    def _setup_ui(self):
        """深度优化 UI 表现力"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 340)  # 略微加宽，增加呼吸感

        # 更加拟物的投影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 60))
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
                border-radius: 24px;
                border: 1px solid #E5E7EB;
            }
        """)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 32, 32, 28)
        container_layout.setSpacing(0)

        # === 标题区域 ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        icon_label = QLabel("🔑")
        icon_label.setFixedSize(46, 46)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #FEE2E2; 
                border: 1px solid #FECACA;
                border-radius: 14px;
                font-size: 22px;
            }
        """)
        header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel("访问授权")
        title_label.setStyleSheet("""
            QLabel {
                color: #111827;
                font-size: 20px;
                font-weight: 800;
                font-family: 'Segoe UI Semibold', 'Microsoft YaHei UI';
                letter-spacing: 0.5px;
            }
        """)
        subtitle_label = QLabel("此目录已加密，请输入密码解锁")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #6B7280;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI';
            }
        """)

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        container_layout.addLayout(header_layout)

        container_layout.addSpacing(25)

        # === 密码提示：极度醒目的红黑风格卡片 ===
        if self._tip:
            tip_card = QWidget()
            # 采用左侧加粗红条的通知框样式，比纯边框更醒目
            tip_card.setStyleSheet("""
                QWidget {
                    background-color: #FFF1F2;
                    border-left: 5px solid #E11D48; /* 加粗左侧边框 */
                    border-top-right-radius: 12px;
                    border-bottom-right-radius: 12px;
                    border-top-left-radius: 4px;
                    border-bottom-left-radius: 4px;
                }
            """)
            tip_layout = QHBoxLayout(tip_card)
            tip_layout.setContentsMargins(18, 12, 18, 12)

            tip_text = QLabel(f"<b>提示</b>：{self._tip}")
            tip_text.setStyleSheet("""
                QLabel {
                    color: #9F1239;
                    font-size: 14px;
                    font-family: 'Microsoft YaHei UI';
                }
            """)
            tip_text.setWordWrap(True)
            tip_layout.addWidget(tip_text)

            container_layout.addWidget(tip_card)
            container_layout.addSpacing(22)

        # === 密码输入区域 ===
        pwd_label = QLabel("解密密码")
        pwd_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 8px;
                font-family: 'Microsoft YaHei UI';
            }
        """)
        container_layout.addWidget(pwd_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("请输入密码以继续...")
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFC;
                border: 2px solid #F1F5F9;
                border-radius: 12px;
                padding: 0 16px;
                font-size: 15px;
                color: #0F172A;
                font-family: 'Segoe UI', 'Microsoft YaHei UI';
            }
            QLineEdit:focus {
                background-color: #FFFFFF;
                border: 2px solid #E11D48; /* 焦点与提示红同步，增强暗示 */
            }
        """)
        self.password_input.returnPressed.connect(self._on_confirm)
        container_layout.addWidget(self.password_input)

        # === 错误信息 ===
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            QLabel {
                color: #E11D48;
                font-size: 12px;
                font-weight: bold;
                margin-top: 8px;
                font-family: 'Microsoft YaHei UI';
            }
        """)
        self.error_label.hide()
        container_layout.addWidget(self.error_label)

        container_layout.addStretch()

        # === 按钮区域 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(90, 42)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #64748B;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                font-weight: 700;
                font-family: 'Microsoft YaHei UI';
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
                color: #1E293B;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        unlock_btn = QPushButton("立即解锁")
        unlock_btn.setFixedSize(120, 42)
        unlock_btn.setCursor(Qt.PointingHandCursor)
        unlock_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B; /* 采用深色技术感按钮，突出专业性 */
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-weight: 800;
                font-family: 'Microsoft YaHei UI';
            }
            QPushButton:hover {
                background-color: #334155;
            }
            QPushButton:pressed {
                transform: translateY(2px);
                background-color: #0F172A;
            }
        """)
        unlock_btn.clicked.connect(self._on_confirm)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(unlock_btn)

        container_layout.addLayout(btn_layout)
        main_layout.addWidget(container)

    def _on_confirm(self):
        password = self.password_input.text()
        if not password:
            self._show_error("✕ 请输入解锁密码")
            return
        self._password = password
        self.accept()

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()

    def _center_dialog(self):
        main_window = QApplication.activeWindow()
        if main_window:
            x = main_window.x() + (main_window.width() - self.width()) // 2
            y = main_window.y() + (main_window.height() - self.height()) // 2
            self.move(x, y)

    def get_password(self) -> str:
        return self._password


class DecryptSuccessDialog(QDialog):
    """解密成功弹窗 - 视觉同步"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._center_dialog()

    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 220)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container = QWidget()
        container.setStyleSheet("background-color: #FFFFFF; border-radius: 24px;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 30, 25, 25)

        icon = QLabel("🔓")
        icon.setFixedSize(60, 60)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("""
            QLabel {
                background-color: #F0FDF4;
                color: #22C55E;
                border: 1px solid #BBF7D0;
                border-radius: 30px;
                font-size: 30px;
            }
        """)

        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)

        title = QLabel("解密完成")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #0F172A; font-size: 18px; font-weight: 800; font-family: 'Microsoft YaHei UI'; margin-top: 10px;")
        layout.addWidget(title)

        ok_btn = QPushButton("确定")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #22C55E;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-family: 'Microsoft YaHei UI';
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #16A34A; }
        """)
        ok_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

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

    # 全局字体强制开启，避免渲染偏差
    app.setFont(QFont("Microsoft YaHei UI", 9))

    dialog = DecryptPasswordDialog("/test")
    dialog._tip = "123456"  # 模拟醒目测试
    if dialog.exec():
        success = DecryptSuccessDialog()
        success.exec()

    sys.exit(0)