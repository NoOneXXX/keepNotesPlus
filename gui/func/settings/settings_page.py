"""
设置页面 - Git 配置和同步管理
"""
import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGroupBox, QTextEdit, QMessageBox, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QColor

from gui.func.utils.git_manager import GitManager


class GitWorker(QThread):
    """Git 操作工作线程"""
    finished = Signal(bool, str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            success, msg = self.func(*self.args, **self.kwargs)
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, str(e))


class SettingsDialog(QDialog):
    """设置对话框 - Git 配置和同步"""
    
    def __init__(self, notebook_path: str = None, parent=None):
        super().__init__(parent)
        self.notebook_path = notebook_path
        self.git_manager = None
        self.worker = None
        
        # 设置对话框属性
        self.setWindowTitle("设置 - Git 配置")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)  # 移除帮助按钮
        self.setStyleSheet("""
            QDialog {
                background-color: #F9FAFB;
            }
        """)
        
        self.setup_ui()
        
        if notebook_path:
            self.set_notebook_path(notebook_path)
    
    def set_notebook_path(self, path: str):
        """设置笔记本路径"""
        self.notebook_path = path
        self.git_manager = GitManager(path)
        self.refresh_status()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 标题栏
        header_layout = QHBoxLayout()
        
        close_btn = QPushButton("✕ 关闭")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6B7280;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
                color: #DC2626;
                border-color: #FECACA;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        title_label = QLabel("Git 设置")
        title_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1F2937;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E5E7EB;")
        main_layout.addWidget(line)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #F3F4F6;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #D1D5DB;
                border-radius: 4px;
                min-height: 20px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)
        
        # Git 配置区域
        git_config_group = self.create_git_config_group()
        scroll_layout.addWidget(git_config_group)
        
        # Git 操作区域
        git_ops_group = self.create_git_operations_group()
        scroll_layout.addWidget(git_ops_group)
        
        # 状态显示区域
        status_group = self.create_status_group()
        scroll_layout.addWidget(status_group)
        
        # 提交历史区域
        history_group = self.create_history_group()
        scroll_layout.addWidget(history_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def create_git_config_group(self) -> QGroupBox:
        """创建 Git 配置区域"""
        group = QGroupBox("Git 配置")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 24, 16, 16)
        
        # 仓库状态
        status_layout = QHBoxLayout()
        status_label = QLabel("仓库状态:")
        status_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        status_layout.addWidget(status_label)
        
        self.repo_status_label = QLabel("未初始化")
        self.repo_status_label.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.repo_status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 初始化按钮
        init_layout = QHBoxLayout()
        self.init_btn = QPushButton("初始化 Git 仓库")
        self.init_btn.setFixedHeight(40)
        self.init_btn.setCursor(Qt.PointingHandCursor)
        self.init_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.init_btn.clicked.connect(self.init_repo)
        init_layout.addWidget(self.init_btn)
        init_layout.addStretch()
        layout.addLayout(init_layout)
        
        # 远程仓库 URL
        remote_layout = QHBoxLayout()
        remote_label = QLabel("远程仓库 URL:")
        remote_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        remote_label.setFixedWidth(100)
        remote_layout.addWidget(remote_label)
        
        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("例如: https://github.com/username/repo.git")
        self.remote_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #F9FAFB;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background-color: white;
            }
        """)
        remote_layout.addWidget(self.remote_input)
        
        self.set_remote_btn = QPushButton("设置")
        self.set_remote_btn.setFixedSize(80, 40)
        self.set_remote_btn.setCursor(Qt.PointingHandCursor)
        self.set_remote_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.set_remote_btn.clicked.connect(self.set_remote)
        remote_layout.addWidget(self.set_remote_btn)
        layout.addLayout(remote_layout)
        
        # 当前分支
        branch_layout = QHBoxLayout()
        branch_label = QLabel("当前分支:")
        branch_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        branch_label.setFixedWidth(100)
        branch_layout.addWidget(branch_label)
        
        self.branch_label = QLabel("-")
        self.branch_label.setStyleSheet("color: #374151; font-size: 14px; font-weight: bold;")
        branch_layout.addWidget(self.branch_label)
        branch_layout.addStretch()
        layout.addLayout(branch_layout)
        
        return group
    
    def create_git_operations_group(self) -> QGroupBox:
        """创建 Git 操作区域"""
        group = QGroupBox("Git 操作")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 24, 16, 16)
        
        # 提交信息输入
        commit_layout = QHBoxLayout()
        commit_label = QLabel("提交信息:")
        commit_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        commit_label.setFixedWidth(80)
        commit_layout.addWidget(commit_label)
        
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("输入提交信息...")
        self.commit_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                background-color: #F9FAFB;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background-color: white;
            }
        """)
        commit_layout.addWidget(self.commit_input)
        layout.addLayout(commit_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # Pull 按钮
        self.pull_btn = QPushButton("⬇ Pull")
        self.pull_btn.setFixedHeight(44)
        self.pull_btn.setCursor(Qt.PointingHandCursor)
        self.pull_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
        """)
        self.pull_btn.clicked.connect(self.pull_changes)
        btn_layout.addWidget(self.pull_btn)
        
        # Commit 按钮
        self.commit_btn = QPushButton("✓ Commit")
        self.commit_btn.setFixedHeight(44)
        self.commit_btn.setCursor(Qt.PointingHandCursor)
        self.commit_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        self.commit_btn.clicked.connect(self.commit_changes)
        btn_layout.addWidget(self.commit_btn)
        
        # Push 按钮
        self.push_btn = QPushButton("⬆ Push")
        self.push_btn.setFixedHeight(44)
        self.push_btn.setCursor(Qt.PointingHandCursor)
        self.push_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.push_btn.clicked.connect(self.push_changes)
        btn_layout.addWidget(self.push_btn)
        
        # Sync 按钮（一键同步）
        self.sync_btn = QPushButton("🔄 一键同步")
        self.sync_btn.setFixedHeight(44)
        self.sync_btn.setCursor(Qt.PointingHandCursor)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.sync_btn.clicked.connect(self.sync_all)
        btn_layout.addWidget(self.sync_btn)
        
        layout.addLayout(btn_layout)
        
        # 冲突解决区域
        conflict_layout = QHBoxLayout()
        conflict_layout.setSpacing(12)
        
        self.resolve_ours_btn = QPushButton("解决冲突 (保留本地)")
        self.resolve_ours_btn.setFixedHeight(36)
        self.resolve_ours_btn.setCursor(Qt.PointingHandCursor)
        self.resolve_ours_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        self.resolve_ours_btn.clicked.connect(lambda: self.resolve_conflicts('ours'))
        conflict_layout.addWidget(self.resolve_ours_btn)
        
        self.resolve_theirs_btn = QPushButton("解决冲突 (保留远程)")
        self.resolve_theirs_btn.setFixedHeight(36)
        self.resolve_theirs_btn.setCursor(Qt.PointingHandCursor)
        self.resolve_theirs_btn.setStyleSheet("""
            QPushButton {
                background-color: #EC4899;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #DB2777;
            }
        """)
        self.resolve_theirs_btn.clicked.connect(lambda: self.resolve_conflicts('theirs'))
        conflict_layout.addWidget(self.resolve_theirs_btn)
        
        conflict_layout.addStretch()
        layout.addLayout(conflict_layout)
        
        return group
    
    def create_status_group(self) -> QGroupBox:
        """创建状态显示区域"""
        group = QGroupBox("文件状态")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 24, 16, 16)
        
        # 状态表格
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(2)
        self.status_table.setHorizontalHeaderLabels(["状态", "文件"])
        self.status_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.status_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.status_table.setColumnWidth(0, 100)
        self.status_table.setMaximumHeight(200)
        self.status_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: #F9FAFB;
                gridline-color: #E5E7EB;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                color: #6B7280;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                padding: 8px;
            }
        """)
        layout.addWidget(self.status_table)
        
        # 刷新按钮
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新状态")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_status)
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
        
        return group
    
    def create_history_group(self) -> QGroupBox:
        """创建提交历史区域"""
        group = QGroupBox("提交历史")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #374151;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 24, 16, 16)
        
        # 历史表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["日期", "作者", "提交信息", "Hash"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.history_table.setColumnWidth(0, 100)
        self.history_table.setColumnWidth(1, 100)
        self.history_table.setColumnWidth(3, 80)
        self.history_table.setMaximumHeight(200)
        self.history_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                background-color: #F9FAFB;
                gridline-color: #E5E7EB;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                color: #6B7280;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                padding: 8px;
            }
        """)
        layout.addWidget(self.history_table)
        
        return group
    
    def show_message(self, message: str, msg_type: str):
        """显示消息"""
        if msg_type == "success":
            QMessageBox.information(self, "成功", message)
        elif msg_type == "error":
            QMessageBox.critical(self, "错误", message)
        else:
            QMessageBox.information(self, "提示", message)
    
    def init_repo(self):
        """初始化 Git 仓库"""
        if not self.git_manager:
            self.show_message("请先选择笔记本", "error")
            return
        
        self.worker = GitWorker(self.git_manager.init_repo)
        self.worker.finished.connect(self.on_init_finished)
        self.worker.start()
    
    def on_init_finished(self, success: bool, msg: str):
        """初始化完成回调"""
        if success:
            self.show_message(msg, "success")
            self.refresh_status()
        else:
            self.show_message(msg, "error")
    
    def set_remote(self):
        """设置远程仓库"""
        if not self.git_manager:
            self.show_message("请先初始化 Git 仓库", "error")
            return
        
        remote_url = self.remote_input.text().strip()
        if not remote_url:
            self.show_message("请输入远程仓库 URL", "error")
            return
        
        self.worker = GitWorker(self.git_manager.set_remote, "origin", remote_url)
        self.worker.finished.connect(self.on_set_remote_finished)
        self.worker.start()
    
    def on_set_remote_finished(self, success: bool, msg: str):
        """设置远程仓库完成回调"""
        if success:
            self.show_message(msg, "success")
        else:
            self.show_message(msg, "error")
    
    def pull_changes(self):
        """拉取更改"""
        if not self.git_manager or not self.git_manager.is_git_repo():
            self.show_message("请先初始化 Git 仓库", "error")
            return
        
        self.worker = GitWorker(self.git_manager.pull)
        self.worker.finished.connect(self.on_pull_finished)
        self.worker.start()
    
    def on_pull_finished(self, success: bool, msg: str):
        """拉取完成回调"""
        if success:
            self.show_message(msg, "success")
        else:
            if "conflict" in msg.lower() or self.git_manager.has_conflicts():
                self.show_message("存在冲突，请解决冲突后继续", "error")
            else:
                self.show_message(msg, "error")
        self.refresh_status()
    
    def commit_changes(self):
        """提交更改"""
        if not self.git_manager or not self.git_manager.is_git_repo():
            self.show_message("请先初始化 Git 仓库", "error")
            return
        
        message = self.commit_input.text().strip()
        if not message:
            self.show_message("请输入提交信息", "error")
            return
        
        # 先添加所有更改
        success, msg = self.git_manager.add_all()
        if not success:
            self.show_message(msg, "error")
            return
        
        self.worker = GitWorker(self.git_manager.commit, message)
        self.worker.finished.connect(self.on_commit_finished)
        self.worker.start()
    
    def on_commit_finished(self, success: bool, msg: str):
        """提交完成回调"""
        if success:
            self.show_message(msg, "success")
            self.commit_input.clear()
        else:
            self.show_message(msg, "error")
        self.refresh_status()
    
    def push_changes(self):
        """推送更改"""
        if not self.git_manager or not self.git_manager.is_git_repo():
            self.show_message("请先初始化 Git 仓库", "error")
            return
        
        self.worker = GitWorker(self.git_manager.push)
        self.worker.finished.connect(self.on_push_finished)
        self.worker.start()
    
    def on_push_finished(self, success: bool, msg: str):
        """推送完成回调"""
        if success:
            self.show_message(msg, "success")
        else:
            self.show_message(msg, "error")
    
    def sync_all(self):
        """一键同步"""
        if not self.git_manager or not self.git_manager.is_git_repo():
            self.show_message("请先初始化 Git 仓库", "error")
            return
        
        message = self.commit_input.text().strip() or "Auto sync"
        
        self.worker = GitWorker(self.git_manager.sync_all, message)
        self.worker.finished.connect(self.on_sync_finished)
        self.worker.start()
    
    def on_sync_finished(self, success: bool, msg: str):
        """同步完成回调"""
        if success:
            self.show_message(msg, "success")
            self.commit_input.clear()
        else:
            self.show_message(msg, "error")
        self.refresh_status()
    
    def resolve_conflicts(self, strategy: str):
        """解决冲突"""
        if not self.git_manager or not self.git_manager.is_git_repo():
            self.show_message("请先初始化 Git 仓库", "error")
            return
        
        if strategy == 'ours':
            self.worker = GitWorker(self.git_manager.resolve_conflicts_auto)
        else:
            self.worker = GitWorker(self.git_manager.resolve_conflicts_theirs)
        
        self.worker.finished.connect(self.on_resolve_finished)
        self.worker.start()
    
    def on_resolve_finished(self, success: bool, msg: str):
        """解决冲突完成回调"""
        if success:
            self.show_message(msg, "success")
        else:
            self.show_message(msg, "error")
        self.refresh_status()
    
    def refresh_status(self):
        """刷新状态"""
        if not self.git_manager:
            self.repo_status_label.setText("未选择笔记本")
            self.repo_status_label.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
            return
        
        # 检查仓库状态
        if self.git_manager.is_git_repo():
            self.repo_status_label.setText("已初始化 ✓")
            self.repo_status_label.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold;")
            self.init_btn.setEnabled(False)
            
            # 获取当前分支
            branch = self.git_manager.get_current_branch()
            self.branch_label.setText(branch or "-")
            
            # 获取远程 URL
            remote_url = self.git_manager.get_remote_url()
            if remote_url:
                self.remote_input.setText(remote_url)
            
            # 获取文件状态
            success, status = self.git_manager.get_status()
            if success:
                self.update_status_table(status)
            
            # 获取提交历史
            logs = self.git_manager.get_commit_log(10)
            self.update_history_table(logs)
        else:
            self.repo_status_label.setText("未初始化")
            self.repo_status_label.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold;")
            self.init_btn.setEnabled(True)
            self.branch_label.setText("-")
            self.status_table.setRowCount(0)
            self.history_table.setRowCount(0)
    
    def update_status_table(self, status: dict):
        """更新状态表格"""
        self.status_table.setRowCount(0)
        
        status_map = {
            'modified': ('已修改', '#F59E0B'),
            'added': ('已添加', '#10B981'),
            'deleted': ('已删除', '#EF4444'),
            'untracked': ('未跟踪', '#6B7280'),
            'conflicted': ('冲突', '#DC2626')
        }
        
        for status_type, files in status.items():
            if status_type == 'error':
                continue
            for file_path in files:
                row = self.status_table.rowCount()
                self.status_table.insertRow(row)
                
                status_text, color = status_map.get(status_type, ('未知', '#6B7280'))
                
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor(color))
                self.status_table.setItem(row, 0, status_item)
                
                file_item = QTableWidgetItem(file_path)
                self.status_table.setItem(row, 1, file_item)
    
    def update_history_table(self, logs: list):
        """更新历史表格"""
        self.history_table.setRowCount(0)
        
        for log in logs:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            self.history_table.setItem(row, 0, QTableWidgetItem(log.get('date', '-')))
            self.history_table.setItem(row, 1, QTableWidgetItem(log.get('author', '-')))
            self.history_table.setItem(row, 2, QTableWidgetItem(log.get('message', '-')))
            
            hash_item = QTableWidgetItem(log.get('hash', '-')[:8])
            hash_item.setForeground(QColor('#6B7280'))
            self.history_table.setItem(row, 3, hash_item)
