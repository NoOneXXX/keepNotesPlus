"""
Markdown 编辑器组件
==================

支持编辑和预览两种模式的 Markdown 编辑器。
使用 markdown_renderer 模块进行渲染。

特性：
- 编辑/预览/分屏三种模式
- 语法高亮（编辑器）
- 图片粘贴支持
- PDF 导出
"""

import os
import re
import time
import json
import shutil

from PySide6.QtWidgets import (
    QTextEdit, QMenu, QMessageBox, QFileDialog, QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QStackedWidget, QFrame, QPlainTextEdit
)
from PySide6.QtGui import (
    QImage, QClipboard, QAction, QTextCharFormat,
    QFont, QCursor, QIcon, QKeySequence, QColor,
    QSyntaxHighlighter
)
from PySide6.QtCore import (
    QMimeData, QUrl, Qt, Signal, QRegularExpression, QTimer
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from gui.func.utils import logger
from gui.func.utils.markdown_renderer import render_markdown


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown 语法高亮器 - 用于编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # 标题 # ## ###
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#2E7D32"))
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'^#{1,6}\s.*'), header_format))
        
        # 粗体 **text**
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#D32F2F"))
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\*\*[^*]+\*\*'), bold_format))
        self.highlighting_rules.append((QRegularExpression(r'__[^_]+__'), bold_format))
        
        # 斜体 *text*
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#F57C00"))
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r'\*[^*]+\*'), italic_format))
        self.highlighting_rules.append((QRegularExpression(r'_[^_]+_'), italic_format))
        
        # 行内代码 `code`
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#1976D2"))
        code_format.setBackground(QColor("#F5F5F5"))
        code_format.setFontFamily("Consolas, Monaco, monospace")
        self.highlighting_rules.append((QRegularExpression(r'`[^`]+`'), code_format))
        
        # 代码块 ```code```
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(QColor("#1976D2"))
        code_block_format.setBackground(QColor("#F5F5F5"))
        code_block_format.setFontFamily("Consolas, Monaco, monospace")
        self.highlighting_rules.append((QRegularExpression(r'^```.*$'), code_block_format))
        
        # 链接 [text](url)
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#7B1FA2"))
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((QRegularExpression(r'\[([^\]]+)\]\(([^)]+)\)'), link_format))
        
        # 图片 ![alt](url)
        image_format = QTextCharFormat()
        image_format.setForeground(QColor("#00796B"))
        self.highlighting_rules.append((QRegularExpression(r'!\[([^\]]*)\]\(([^)]+)\)'), image_format))
        
        # 引用 >
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#5D4037"))
        quote_format.setBackground(QColor("#FFF8E1"))
        self.highlighting_rules.append((QRegularExpression(r'^>\s.*'), quote_format))
        
        # 列表 - * +
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#C62828"))
        self.highlighting_rules.append((QRegularExpression(r'^\s*[-*+]\s'), list_format))
        
        # 数字列表 1. 2.
        num_list_format = QTextCharFormat()
        num_list_format.setForeground(QColor("#C62828"))
        self.highlighting_rules.append((QRegularExpression(r'^\s*\d+\.\s'), num_list_format))
        
        # 分隔线 ---
        hr_format = QTextCharFormat()
        hr_format.setForeground(QColor("#9E9E9E"))
        hr_format.setBackground(QColor("#EEEEEE"))
        self.highlighting_rules.append((QRegularExpression(r'^-{3,}$'), hr_format))
        self.highlighting_rules.append((QRegularExpression(r'^\*{3,}$'), hr_format))
        
        # HTML 标签
        html_format = QTextCharFormat()
        html_format.setForeground(QColor("#E91E63"))
        self.highlighting_rules.append((QRegularExpression(r'<[^>]+>'), html_format))
    
    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class MarkdownEditor(QWidget):
    """
    Markdown 编辑器组件
    支持编辑、预览和分屏三种模式
    """
    
    content_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.md_file_path = None
        self._is_preview_mode = False
        self._split_preview_initialized = False
        self._preview_update_timer = QTimer(self)
        self._preview_update_timer.setSingleShot(True)
        self._preview_update_timer.timeout.connect(self._do_update_split_preview)
        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部工具栏
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border-bottom: 1px solid #E2E8F0;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 0, 12, 0)
        toolbar_layout.setSpacing(8)
        
        # 模式切换按钮
        self.edit_btn = QPushButton("✏ 编辑")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setChecked(True)
        self.edit_btn.setStyleSheet(self._get_toolbar_btn_style(True))
        
        self.preview_btn = QPushButton("👁 预览")
        self.preview_btn.setCheckable(True)
        self.preview_btn.setStyleSheet(self._get_toolbar_btn_style(False))
        
        self.split_btn = QPushButton("◫ 分屏")
        self.split_btn.setCheckable(True)
        self.split_btn.setStyleSheet(self._get_toolbar_btn_style(False))
        
        toolbar_layout.addWidget(self.edit_btn)
        toolbar_layout.addWidget(self.preview_btn)
        toolbar_layout.addWidget(self.split_btn)
        toolbar_layout.addStretch()
        
        # 文件路径标签
        self.path_label = QLabel("未保存")
        self.path_label.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 12px;
                font-family: 'Microsoft YaHei UI', sans-serif;
            }
        """)
        toolbar_layout.addWidget(self.path_label)
        
        layout.addWidget(toolbar)
        
        # 内容区域
        self.content_stack = QStackedWidget()
        
        # 编辑模式
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background-color: #FFFFFF;
                font-family: 'Consolas', 'Microsoft YaHei Mono', 'Monaco', monospace;
                font-size: 14px;
                line-height: 1.6;
                padding: 16px;
                color: #1E293B;
            }
            QPlainTextEdit:focus {
                outline: none;
            }
        """)
        self.editor.setPlaceholderText("在此输入 Markdown 内容...\n\n支持标准 Markdown 语法：\n# 标题\n**粗体**\n*斜体*\n[链接](url)\n![图片](url)\n- 列表项")
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        self.editor.installEventFilter(self)
        
        # 添加语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 预览模式
        self.preview = QWebEngineView()
        self.preview.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #FFFFFF;
            }
        """)
        QTimer.singleShot(0, lambda: self.preview.setHtml("<html><body style='background-color:#1e1e2e;'></body></html>"))
        
        # 分屏模式
        self.split_editor = QPlainTextEdit()
        self.split_editor.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background-color: #FFFFFF;
                font-family: 'Consolas', 'Microsoft YaHei Mono', 'Monaco', monospace;
                font-size: 14px;
                line-height: 1.6;
                padding: 16px;
                color: #1E293B;
            }
            QPlainTextEdit:focus {
                outline: none;
            }
        """)
        self.split_highlighter = MarkdownHighlighter(self.split_editor.document())
        self.split_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.split_editor.customContextMenuRequested.connect(self._show_context_menu)
        self.split_editor.installEventFilter(self)
        
        self.split_preview = QWebEngineView()
        self.split_preview.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #FFFFFF;
            }
        """)
        QTimer.singleShot(0, lambda: self.split_preview.setHtml("<html><body style='background-color:#1e1e2e;'></body></html>"))
        
        # 分屏容器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.split_editor)
        self.splitter.addWidget(self.split_preview)
        self.splitter.setSizes([400, 400])
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E2E8F0;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #CBD5E1;
            }
        """)
        
        self.content_stack.addWidget(self.editor)      # 0 - 编辑
        self.content_stack.addWidget(self.preview)     # 1 - 预览
        self.content_stack.addWidget(self.splitter)    # 2 - 分屏
        
        layout.addWidget(self.content_stack)
        
        # 设置默认模式
        self._set_mode("edit", update_preview=False)
        
    def _get_toolbar_btn_style(self, active):
        """获取工具栏按钮样式"""
        if active:
            return """
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 13px;
                    font-family: 'Microsoft YaHei UI', sans-serif;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: transparent;
                    color: #64748B;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 13px;
                    font-family: 'Microsoft YaHei UI', sans-serif;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    color: #334155;
                }
                QPushButton:checked {
                    background-color: #3B82F6;
                    color: white;
                }
            """
    
    def _setup_connections(self):
        """设置信号连接"""
        self.edit_btn.clicked.connect(lambda: self._set_mode("edit"))
        self.preview_btn.clicked.connect(lambda: self._set_mode("preview"))
        self.split_btn.clicked.connect(lambda: self._set_mode("split"))
        
        self.editor.textChanged.connect(self._on_content_changed)
        self.split_editor.textChanged.connect(self._on_split_content_changed)
        
        self.split_editor.verticalScrollBar().valueChanged.connect(self._on_split_editor_scroll)
        self.editor.verticalScrollBar().valueChanged.connect(self._on_editor_scroll)
        
    def _on_split_content_changed(self):
        """分屏编辑器内容变化时同步"""
        split_content = self.split_editor.toPlainText()
        if self.editor.toPlainText() != split_content:
            self.editor.setPlainText(split_content)
        self.content_changed.emit()
        self._update_split_preview()
    
    def _on_split_editor_scroll(self, value):
        """分屏编辑器滚动时同步到预览"""
        if self.content_stack.currentIndex() == 2:
            editor_scrollbar = self.split_editor.verticalScrollBar()
            if editor_scrollbar.maximum() > 0:
                scroll_percent = value / editor_scrollbar.maximum()
                js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent:.4f});"
                self.split_preview.page().runJavaScript(js_code)
    
    def _on_editor_scroll(self, value):
        """编辑器滚动时同步到预览"""
        if self.content_stack.currentIndex() == 1:
            editor_scrollbar = self.editor.verticalScrollBar()
            if editor_scrollbar.maximum() > 0:
                scroll_percent = value / editor_scrollbar.maximum()
                js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent:.4f});"
                self.preview.page().runJavaScript(js_code)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        sender = self.sender()
        active_editor = self.split_editor if sender == self.split_editor else self.editor
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 4px;
                font-size: 14px;
                font-family: 'Microsoft YaHei', 'Arial', sans-serif;
            }
            QMenu::item {
                padding: 6px 24px 6px 8px;
                border-radius: 4px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #e6f7ff;
                color: #1890ff;
            }
            QMenu::separator {
                height: 1px;
                background: #f0f0f0;
                margin: 4px 0px;
            }
        """)
        
        copy_action = QAction(QIcon(":images/document-copy.png"), "复制", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(active_editor.copy)
        copy_action.setEnabled(active_editor.textCursor().hasSelection())
        
        paste_action = QAction(QIcon(":images/clipboard-paste-document-text.png"), "粘贴", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: self._handle_paste(active_editor))
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(clipboard.mimeData().hasText() or clipboard.mimeData().hasImage() or clipboard.mimeData().hasHtml())
        
        export_pdf_action = QAction(QIcon(":images/question.png"), "导出PDF", self)
        export_pdf_action.triggered.connect(self.export_to_pdf)
        
        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(export_pdf_action)
        
        menu.exec(QCursor.pos())
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理 Ctrl+V 粘贴图片"""
        if obj in (self.editor, self.split_editor):
            if event.type() == event.Type.KeyPress:
                if event.matches(QKeySequence.StandardKey.Paste):
                    self._handle_paste(obj)
                    return True
        return super().eventFilter(obj, event)
    
    def _handle_paste(self, editor):
        """处理粘贴操作，支持图片粘贴"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self._insert_image_from_qimage(editor, image)
                return
        
        if mime_data.hasUrls():
            urls = mime_data.urls()
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    ext = os.path.splitext(file_path)[1].lower()
                    if ext in image_extensions:
                        self._insert_image_from_file(editor, file_path)
                        return
        
        editor.paste()
    
    def _insert_image_from_qimage(self, editor, image):
        """从 QImage 插入图片"""
        if not self.md_file_path:
            QMessageBox.warning(self, "无法插入图片", "请先保存 Markdown 文件")
            return
        
        try:
            md_dir = os.path.dirname(self.md_file_path)
            images_dir = os.path.join(md_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_name = f"image_{timestamp}.png"
            image_path = os.path.join(images_dir, image_name)
            
            if not image.save(image_path, "PNG"):
                QMessageBox.warning(self, "保存失败", "无法保存图片文件")
                return
            
            relative_path = f"images/{image_name}"
            md_image = f"![图片]({relative_path})"
            
            cursor = editor.textCursor()
            cursor.insertText(md_image)
            
            logger.info(f"图片已保存: {image_path}")
            
        except Exception as e:
            logger.error(f"插入图片失败: {str(e)}")
            QMessageBox.critical(self, "插入失败", f"插入图片时出错:\n{str(e)}")
    
    def _insert_image_from_file(self, editor, source_path):
        """从文件路径插入图片"""
        if not self.md_file_path:
            QMessageBox.warning(self, "无法插入图片", "请先保存 Markdown 文件")
            return
        
        try:
            md_dir = os.path.dirname(self.md_file_path)
            images_dir = os.path.join(md_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            original_name = os.path.basename(source_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(original_name)
            new_name = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(images_dir, new_name)
            
            shutil.copy2(source_path, dest_path)
            
            relative_path = f"images/{new_name}"
            md_image = f"![{name}]({relative_path})"
            
            cursor = editor.textCursor()
            cursor.insertText(md_image)
            
            logger.info(f"图片已复制: {dest_path}")
            
        except Exception as e:
            logger.error(f"插入图片失败: {str(e)}")
            QMessageBox.critical(self, "插入失败", f"插入图片时出错:\n{str(e)}")
    
    def export_to_pdf(self):
        """导出当前内容为PDF文件"""
        default_filename = "导出文档.pdf"
        if self.md_file_path:
            default_filename = os.path.splitext(os.path.basename(self.md_file_path))[0] + ".pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", default_filename, "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            from PySide6.QtPrintSupport import QPrinter
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            printer.setPageSize(QPrinter.A4)
            
            current_widget = self.content_stack.currentWidget()
            active_editor = self.split_editor if current_widget == self.splitter else self.editor
            
            active_editor.document().print_(printer)
            
            logger.info(f"PDF导出成功: {file_path}")
            QMessageBox.information(self, "导出成功", f"PDF文件已保存到:\n{file_path}")
        except Exception as e:
            logger.error(f"PDF导出失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出PDF时出错:\n{str(e)}")
        
    def _update_split_preview(self):
        """更新分屏预览内容（带防抖）"""
        self._preview_update_timer.start(100)
    
    def _do_update_split_preview(self):
        """实际执行分屏预览更新"""
        md_content = self.split_editor.toPlainText()
        html_content = render_markdown(md_content, dark_mode=True)
        
        if not self._split_preview_initialized:
            if self.md_file_path:
                base_url = QUrl.fromLocalFile(os.path.dirname(self.md_file_path) + '/')
                self.split_preview.setHtml(html_content, base_url)
            else:
                self.split_preview.setHtml(html_content)
            self._split_preview_initialized = True
        else:
            # 更新内容区域
            html_body = render_markdown(md_content, dark_mode=True)
            # 使用 JavaScript 更新
            self.split_preview.page().runJavaScript(
                f"document.body.innerHTML = {json.dumps(html_body, ensure_ascii=False)};"
            )
    
    def _set_mode(self, mode, update_preview=True):
        """设置显示模式"""
        self.edit_btn.setChecked(mode == "edit")
        self.preview_btn.setChecked(mode == "preview")
        self.split_btn.setChecked(mode == "split")
        
        self.edit_btn.setStyleSheet(self._get_toolbar_btn_style(mode == "edit"))
        self.preview_btn.setStyleSheet(self._get_toolbar_btn_style(mode == "preview"))
        self.split_btn.setStyleSheet(self._get_toolbar_btn_style(mode == "split"))
        
        if mode == "edit":
            self.content_stack.setCurrentIndex(0)
            self._is_preview_mode = False
        elif mode == "preview":
            if update_preview:
                self._update_preview()
            self.content_stack.setCurrentIndex(1)
            self._is_preview_mode = True
        elif mode == "split":
            self.split_editor.setPlainText(self.editor.toPlainText())
            self._split_preview_initialized = False
            if update_preview:
                self._update_split_preview()
            self.content_stack.setCurrentIndex(2)
            self._is_preview_mode = False
            
    def _on_content_changed(self):
        """内容变化时触发"""
        self.content_changed.emit()
        if self.content_stack.currentIndex() == 2:
            self._update_preview()
            
    def _update_preview(self):
        """更新预览内容"""
        md_content = self.editor.toPlainText()
        html_content = render_markdown(md_content, dark_mode=True)
        
        if self.md_file_path:
            base_url = QUrl.fromLocalFile(os.path.dirname(self.md_file_path) + '/')
            self.preview.setHtml(html_content, base_url)
        else:
            self.preview.setHtml(html_content)
        
    def set_file_path(self, file_path):
        """设置文件路径"""
        self.md_file_path = file_path
        if file_path:
            self.path_label.setText(os.path.basename(file_path))
            self.path_label.setToolTip(file_path)
        else:
            self.path_label.setText("未保存")
            self.path_label.setToolTip("")
            
    def load_file(self, file_path):
        """加载 Markdown 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.split_editor.setPlainText(content)
            self.set_file_path(file_path)
            
            current_mode = self.content_stack.currentIndex()
            if current_mode == 1:
                self._update_preview()
            elif current_mode == 2:
                self._update_split_preview()
            
            return True
        except Exception as e:
            logger.error(f"加载 Markdown 文件失败: {e}")
            return False
            
    def save_file(self, file_path=None):
        """保存 Markdown 文件"""
        if file_path:
            self.md_file_path = file_path
        
        if not self.md_file_path:
            return False
            
        try:
            parent_dir = os.path.dirname(self.md_file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            content = self.editor.toPlainText()
            with open(self.md_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.set_file_path(self.md_file_path)
            return True
        except Exception as e:
            logger.error(f"保存 Markdown 文件失败: {e}")
            return False
            
    def get_content(self):
        """获取当前内容"""
        return self.editor.toPlainText()
        
    def set_content(self, content):
        """设置内容"""
        self.editor.setPlainText(content)
        
    def is_modified(self):
        """检查是否有修改"""
        return self.editor.document().isModified()
        
    def clear(self):
        """清空内容"""
        self.editor.clear()
        self.md_file_path = None
        self.path_label.setText("未保存")
