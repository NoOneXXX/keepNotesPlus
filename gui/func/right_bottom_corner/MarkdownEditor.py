import os
import re
import base64
import time
import json
import markdown

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from PySide6.QtWidgets import (
    QTextEdit, QMenu, QMessageBox, QFileDialog, QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QStackedWidget, QFrame, QPlainTextEdit
)
from PySide6.QtGui import (
    QImage, QClipboard, QContextMenuEvent, QAction, QTextCharFormat,
    QFont, QCursor, QIcon, QKeySequence, QColor, QFontMetrics,
    QTextDocument, QSyntaxHighlighter, QTextCursor
)
from PySide6.QtCore import QMimeData, QBuffer, QByteArray, QUrl, Qt, Signal, Slot, QRegularExpression, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from gui.func.utils import logger


# ========================
# 自定义 Pygments 样式
# DBeaver 风格 SQL 配色
# XShell 风格 Shell 配色
# ========================
class DBeaverSQLStyle(HtmlFormatter):
    """DBeaver 风格的 SQL 语法高亮样式"""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.style = 'default'
    
    def get_style_defs(self, cssclass=''):
        return f'''
        {cssclass} .hll {{ background-color: #49483e }}
        {cssclass} {{ background: #1E1E1E; color: #D4D4D4 }}
        {cssclass} .c {{ color: #6A9955; font-style: italic }} /* Comment */
        {cssclass} .err {{ color: #F44747 }} /* Error */
        {cssclass} .k {{ color: #569CD6; font-weight: bold }} /* Keyword */
        {cssclass} .o {{ color: #D4D4D4 }} /* Operator */
        {cssclass} .cm {{ color: #6A9955; font-style: italic }} /* Comment.Multiline */
        {cssclass} .cp {{ color: #C586C0 }} /* Comment.Preproc */
        {cssclass} .c1 {{ color: #6A9955; font-style: italic }} /* Comment.Single */
        {cssclass} .cs {{ color: #6A9955; font-style: italic }} /* Comment.Special */
        {cssclass} .gd {{ color: #F44747 }} /* Generic.Deleted */
        {cssclass} .ge {{ font-style: italic }} /* Generic.Emph */
        {cssclass} .gr {{ color: #F44747 }} /* Generic.Error */
        {cssclass} .gh {{ color: #FFFFFF }} /* Generic.Heading */
        {cssclass} .gi {{ color: #4EC9B0 }} /* Generic.Inserted */
        {cssclass} .go {{ color: #D4D4D4 }} /* Generic.Output */
        {cssclass} .gp {{ color: #D4D4D4 }} /* Generic.Prompt */
        {cssclass} .gs {{ font-weight: bold }} /* Generic.Strong */
        {cssclass} .gu {{ color: #FFFFFF }} /* Generic.Subheading */
        {cssclass} .gt {{ color: #F44747 }} /* Generic.Traceback */
        {cssclass} .kc {{ color: #569CD6; font-weight: bold }} /* Keyword.Constant */
        {cssclass} .kd {{ color: #569CD6; font-weight: bold }} /* Keyword.Declaration */
        {cssclass} .kn {{ color: #C586C0 }} /* Keyword.Namespace */
        {cssclass} .kp {{ color: #569CD6 }} /* Keyword.Pseudo */
        {cssclass} .kr {{ color: #569CD6; font-weight: bold }} /* Keyword.Reserved */
        {cssclass} .kt {{ color: #4EC9B0 }} /* Keyword.Type */
        {cssclass} .ld {{ color: #CE9178 }} /* Literal.Date */
        {cssclass} .m {{ color: #B5CEA8 }} /* Literal.Number */
        {cssclass} .s {{ color: #CE9178 }} /* Literal.String */
        {cssclass} .na {{ color: #9CDCFE }} /* Name.Attribute */
        {cssclass} .nb {{ color: #4EC9B0 }} /* Name.Builtin */
        {cssclass} .nc {{ color: #4EC9B0 }} /* Name.Class */
        {cssclass} .no {{ color: #569CD6 }} /* Name.Constant */
        {cssclass} .nd {{ color: #DCDCAA }} /* Name.Decorator */
        {cssclass} .ni {{ color: #D4D4D4 }} /* Name.Entity */
        {cssclass} .ne {{ color: #4EC9B0 }} /* Name.Exception */
        {cssclass} .nf {{ color: #DCDCAA }} /* Name.Function */
        {cssclass} .nl {{ color: #9CDCFE }} /* Name.Label */
        {cssclass} .nn {{ color: #4EC9B0 }} /* Name.Namespace */
        {cssclass} .nt {{ color: #569CD6 }} /* Name.Tag */
        {cssclass} .nv {{ color: #9CDCFE }} /* Name.Variable */
        {cssclass} .ow {{ color: #C586C0 }} /* Operator.Word */
        {cssclass} .w {{ color: #D4D4D4 }} /* Text.Whitespace */
        {cssclass} .mb {{ color: #B5CEA8 }} /* Literal.Number.Bin */
        {cssclass} .mf {{ color: #B5CEA8 }} /* Literal.Number.Float */
        {cssclass} .mh {{ color: #B5CEA8 }} /* Literal.Number.Hex */
        {cssclass} .mi {{ color: #B5CEA8 }} /* Literal.Number.Integer */
        {cssclass} .mo {{ color: #B5CEA8 }} /* Literal.Number.Oct */
        {cssclass} .sb {{ color: #CE9178 }} /* Literal.String.Backtick */
        {cssclass} .sc {{ color: #CE9178 }} /* Literal.String.Char */
        {cssclass} .sd {{ color: #6A9955 }} /* Literal.String.Doc */
        {cssclass} .s2 {{ color: #CE9178 }} /* Literal.String.Double */
        {cssclass} .se {{ color: #D7BA7D }} /* Literal.String.Escape */
        {cssclass} .sh {{ color: #CE9178 }} /* Literal.String.Heredoc */
        {cssclass} .si {{ color: #CE9178 }} /* Literal.String.Interpol */
        {cssclass} .sx {{ color: #CE9178 }} /* Literal.String.Other */
        {cssclass} .sr {{ color: #D16969 }} /* Literal.String.Regex */
        {cssclass} .s1 {{ color: #CE9178 }} /* Literal.String.Single */
        {cssclass} .ss {{ color: #CE9178 }} /* Literal.String.Symbol */
        {cssclass} .bp {{ color: #4EC9B0 }} /* Name.Builtin.Pseudo */
        {cssclass} .vc {{ color: #9CDCFE }} /* Name.Variable.Class */
        {cssclass} .vg {{ color: #9CDCFE }} /* Name.Variable.Global */
        {cssclass} .vi {{ color: #9CDCFE }} /* Name.Variable.Instance */
        {cssclass} .il {{ color: #B5CEA8 }} /* Literal.Number.Integer.Long */
        '''


class XShellStyle(HtmlFormatter):
    """XShell 风格的 Shell/Bash 语法高亮样式"""
    
    def __init__(self, **options):
        super().__init__(**options)
        self.style = 'default'
    
    def get_style_defs(self, cssclass=''):
        return f'''
        {cssclass} .hll {{ background-color: #49483e }}
        {cssclass} {{ background: #0C0C0C; color: #CCCCCC }}
        {cssclass} .c {{ color: #6A9955; font-style: italic }} /* Comment */
        {cssclass} .err {{ color: #F44747 }} /* Error */
        {cssclass} .k {{ color: #569CD6; font-weight: bold }} /* Keyword */
        {cssclass} .o {{ color: #D4D4D4 }} /* Operator */
        {cssclass} .cm {{ color: #6A9955; font-style: italic }} /* Comment.Multiline */
        {cssclass} .cp {{ color: #C586C0 }} /* Comment.Preproc */
        {cssclass} .c1 {{ color: #6A9955; font-style: italic }} /* Comment.Single */
        {cssclass} .cs {{ color: #6A9955; font-style: italic }} /* Comment.Special */
        {cssclass} .gd {{ color: #F44747 }} /* Generic.Deleted */
        {cssclass} .ge {{ font-style: italic }} /* Generic.Emph */
        {cssclass} .gr {{ color: #F44747 }} /* Generic.Error */
        {cssclass} .gh {{ color: #569CD6 }} /* Generic.Heading */
        {cssclass} .gi {{ color: #4EC9B0 }} /* Generic.Inserted */
        {cssclass} .go {{ color: #CCCCCC }} /* Generic.Output */
        {cssclass} .gp {{ color: #CCCCCC }} /* Generic.Prompt */
        {cssclass} .gs {{ font-weight: bold }} /* Generic.Strong */
        {cssclass} .gu {{ color: #569CD6 }} /* Generic.Subheading */
        {cssclass} .gt {{ color: #F44747 }} /* Generic.Traceback */
        {cssclass} .kc {{ color: #569CD6; font-weight: bold }} /* Keyword.Constant */
        {cssclass} .kd {{ color: #569CD6; font-weight: bold }} /* Keyword.Declaration */
        {cssclass} .kn {{ color: #C586C0 }} /* Keyword.Namespace */
        {cssclass} .kp {{ color: #569CD6 }} /* Keyword.Pseudo */
        {cssclass} .kr {{ color: #569CD6; font-weight: bold }} /* Keyword.Reserved */
        {cssclass} .kt {{ color: #4EC9B0 }} /* Keyword.Type */
        {cssclass} .ld {{ color: #CE9178 }} /* Literal.Date */
        {cssclass} .m {{ color: #B5CEA8 }} /* Literal.Number */
        {cssclass} .s {{ color: #CE9178 }} /* Literal.String */
        {cssclass} .na {{ color: #9CDCFE }} /* Name.Attribute */
        {cssclass} .nb {{ color: #4EC9B0 }} /* Name.Builtin */
        {cssclass} .nc {{ color: #4EC9B0 }} /* Name.Class */
        {cssclass} .no {{ color: #569CD6 }} /* Name.Constant */
        {cssclass} .nd {{ color: #DCDCAA }} /* Name.Decorator */
        {cssclass} .ni {{ color: #D4D4D4 }} /* Name.Entity */
        {cssclass} .ne {{ color: #4EC9B0 }} /* Name.Exception */
        {cssclass} .nf {{ color: #DCDCAA }} /* Name.Function */
        {cssclass} .nl {{ color: #9CDCFE }} /* Name.Label */
        {cssclass} .nn {{ color: #4EC9B0 }} /* Name.Namespace */
        {cssclass} .nt {{ color: #569CD6 }} /* Name.Tag */
        {cssclass} .nv {{ color: #9CDCFE; font-weight: bold }} /* Name.Variable - 变量高亮 */
        {cssclass} .ow {{ color: #C586C0 }} /* Operator.Word */
        {cssclass} .w {{ color: #D4D4D4 }} /* Text.Whitespace */
        {cssclass} .mb {{ color: #B5CEA8 }} /* Literal.Number.Bin */
        {cssclass} .mf {{ color: #B5CEA8 }} /* Literal.Number.Float */
        {cssclass} .mh {{ color: #B5CEA8 }} /* Literal.Number.Hex */
        {cssclass} .mi {{ color: #B5CEA8 }} /* Literal.Number.Integer */
        {cssclass} .mo {{ color: #B5CEA8 }} /* Literal.Number.Oct */
        {cssclass} .sb {{ color: #CE9178 }} /* Literal.String.Backtick */
        {cssclass} .sc {{ color: #CE9178 }} /* Literal.String.Char */
        {cssclass} .sd {{ color: #6A9955 }} /* Literal.String.Doc */
        {cssclass} .s2 {{ color: #CE9178 }} /* Literal.String.Double */
        {cssclass} .se {{ color: #D7BA7D }} /* Literal.String.Escape */
        {cssclass} .sh {{ color: #CE9178 }} /* Literal.String.Heredoc */
        {cssclass} .si {{ color: #CE9178 }} /* Literal.String.Interpol */
        {cssclass} .sx {{ color: #CE9178 }} /* Literal.String.Other */
        {cssclass} .sr {{ color: #D16969 }} /* Literal.String.Regex */
        {cssclass} .s1 {{ color: #CE9178 }} /* Literal.String.Single */
        {cssclass} .ss {{ color: #CE9178 }} /* Literal.String.Symbol */
        {cssclass} .bp {{ color: #4EC9B0 }} /* Name.Builtin.Pseudo */
        {cssclass} .vc {{ color: #9CDCFE }} /* Name.Variable.Class */
        {cssclass} .vg {{ color: #9CDCFE }} /* Name.Variable.Global */
        {cssclass} .vi {{ color: #9CDCFE }} /* Name.Variable.Instance */
        {cssclass} .il {{ color: #B5CEA8 }} /* Literal.Number.Integer.Long */
        /* Shell 特殊样式 */
        {cssclass} .nb {{ color: #4EC9B0; font-weight: bold }} /* 内置命令 */
        {cssclass} .gp {{ color: #6A9955 }} /* 提示符 */
        '''


class MarkdownHighlighter(QSyntaxHighlighter):
    """Markdown 语法高亮器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # 标题 # ## ###
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#2E7D32"))  # 深绿色
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'^#{1,6}\s.*'), header_format))
        
        # 粗体 **text**
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#D32F2F"))  # 红色
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r'\*\*[^*]+\*\*'), bold_format))
        self.highlighting_rules.append((QRegularExpression(r'__[^_]+__'), bold_format))
        
        # 斜体 *text*
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#F57C00"))  # 橙色
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r'\*[^*]+\*'), italic_format))
        self.highlighting_rules.append((QRegularExpression(r'_[^_]+_'), italic_format))
        
        # 行内代码 `code`
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#1976D2"))  # 蓝色
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
        link_format.setForeground(QColor("#7B1FA2"))  # 紫色
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((QRegularExpression(r'\[([^\]]+)\]\(([^)]+)\)'), link_format))
        
        # 图片 ![alt](url)
        image_format = QTextCharFormat()
        image_format.setForeground(QColor("#00796B"))  # 青色
        self.highlighting_rules.append((QRegularExpression(r'!\[([^\]]*)\]\(([^)]+)\)'), image_format))
        
        # 引用 >
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#5D4037"))  # 棕色
        quote_format.setBackground(QColor("#FFF8E1"))
        self.highlighting_rules.append((QRegularExpression(r'^>\s.*'), quote_format))
        
        # 列表 - * +
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#C62828"))  # 深红色
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
        html_format.setForeground(QColor("#E91E63"))  # 粉色
        self.highlighting_rules.append((QRegularExpression(r'<[^>]+>'), html_format))
    
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class MarkdownEditor(QWidget):
    """
    Markdown 编辑器组件
    支持编辑和预览两种模式
    """
    
    # 信号：内容发生变化
    content_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.md_file_path = None
        self._is_preview_mode = False
        self._split_scroll_percent = 0  # 保存分屏预览的滚动位置
        self._split_preview_initialized = False  # 标记分屏预览是否已初始化
        self._preview_update_timer = QTimer(self)  # 防抖定时器
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
        
        # 编辑模式 - 使用 QPlainTextEdit 支持语法高亮
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
        # 启用自定义右键菜单
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self._show_context_menu)
        # 安装事件过滤器以支持 Ctrl+V 粘贴图片
        self.editor.installEventFilter(self)
        
        # 添加语法高亮
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        # 预览模式 - 使用 QWebEngineView
        self.preview = QWebEngineView()
        self.preview.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #FFFFFF;
            }
        """)
        # 延迟设置空白页面避免 QPainter 错误
        QTimer.singleShot(0, lambda: self.preview.setHtml("<html><body style='background-color:#FFFFFF;'></body></html>"))
        
        # 分屏模式 - 创建独立的编辑器和预览控件
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
        # 分屏编辑器也添加语法高亮
        self.split_highlighter = MarkdownHighlighter(self.split_editor.document())
        # 启用自定义右键菜单
        self.split_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.split_editor.customContextMenuRequested.connect(self._show_context_menu)
        # 安装事件过滤器以支持 Ctrl+V 粘贴图片
        self.split_editor.installEventFilter(self)
        self.split_preview = QWebEngineView()
        self.split_preview.setStyleSheet("""
            QWebEngineView {
                border: none;
                background-color: #FFFFFF;
            }
        """)
        # 延迟设置空白页面避免 QPainter 错误
        QTimer.singleShot(0, lambda: self.split_preview.setHtml("<html><body style='background-color:#FFFFFF;'></body></html>"))
        
        # 分屏模式 - 使用 QSplitter
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
        
        # 设置默认模式（不立即更新预览，避免初始化闪烁）
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
        
        # 编辑内容变化时更新预览（QPlainTextEdit 使用 textChanged）
        self.editor.textChanged.connect(self._on_content_changed)
        # 分屏编辑器内容变化时同步到主编辑器
        self.split_editor.textChanged.connect(self._on_split_content_changed)
        
        # 分屏模式下滚动联动
        self.split_editor.verticalScrollBar().valueChanged.connect(self._on_split_editor_scroll)
        self.editor.verticalScrollBar().valueChanged.connect(self._on_editor_scroll)
        
    def _on_split_content_changed(self):
        """分屏编辑器内容变化时同步"""
        # 同步到主编辑器
        split_content = self.split_editor.toPlainText()
        if self.editor.toPlainText() != split_content:
            self.editor.setPlainText(split_content)
        self.content_changed.emit()
        # 更新分屏预览
        self._update_split_preview()
    
    def _on_split_editor_scroll(self, value):
        """分屏编辑器滚动时同步到预览"""
        # 使用JavaScript滚动预览页面
        if self.content_stack.currentIndex() == 2:  # 分屏模式
            editor_scrollbar = self.split_editor.verticalScrollBar()
            if editor_scrollbar.maximum() > 0:
                scroll_percent = value / editor_scrollbar.maximum()
                js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent:.4f});"
                self.split_preview.page().runJavaScript(js_code)
    
    def _on_editor_scroll(self, value):
        """编辑器滚动时同步到预览"""
        if self.content_stack.currentIndex() == 1:  # 预览模式
            editor_scrollbar = self.editor.verticalScrollBar()
            if editor_scrollbar.maximum() > 0:
                scroll_percent = value / editor_scrollbar.maximum()
                js_code = f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent:.4f});"
                self.preview.page().runJavaScript(js_code)
    
    def _show_context_menu(self, pos):
        """显示右键菜单 - 与 RichTextEdit 保持一致"""
        # 获取发送者（当前点击的编辑器）
        sender = self.sender()
        if sender == self.split_editor:
            active_editor = self.split_editor
        else:
            active_editor = self.editor
        
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
            QMenu::icon {
                padding-left: 0px;
                margin-left: 0px;
            }
            QMenu::separator {
                height: 1px;
                background: #f0f0f0;
                margin: 4px 0px;
            }
        """)
        
        # 复制功能
        copy_action = QAction(QIcon(":images/document-copy.png"), "复制", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(active_editor.copy)
        copy_action.setEnabled(active_editor.textCursor().hasSelection())
        
        # 粘贴功能
        paste_action = QAction(QIcon(":images/clipboard-paste-document-text.png"), "粘贴", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(lambda: self._handle_paste(active_editor))
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(clipboard.mimeData().hasText() or clipboard.mimeData().hasImage() or clipboard.mimeData().hasHtml())
        
        # 导出PDF功能
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
                # 检查是否是 Ctrl+V
                if event.matches(QKeySequence.StandardKey.Paste):
                    self._handle_paste(obj)
                    return True
        return super().eventFilter(obj, event)
    
    def _handle_paste(self, editor):
        """处理粘贴操作，支持图片粘贴"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # 检查是否有图片数据
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self._insert_image_from_qimage(editor, image)
                return
        
        # 检查是否有文件URL（从文件管理器复制的图片）
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
        
        # 默认粘贴文本
        editor.paste()
    
    def _insert_image_from_qimage(self, editor, image):
        """从 QImage 插入图片"""
        if not self.md_file_path:
            QMessageBox.warning(self, "无法插入图片", "请先保存 Markdown 文件")
            return
        
        try:
            # 获取 markdown 文件所在目录
            md_dir = os.path.dirname(self.md_file_path)
            # 创建 images 子目录
            images_dir = os.path.join(md_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_name = f"image_{timestamp}.png"
            image_path = os.path.join(images_dir, image_name)
            
            # 保存图片
            if not image.save(image_path, "PNG"):
                QMessageBox.warning(self, "保存失败", "无法保存图片文件")
                return
            
            # 生成相对路径的 markdown 图片语法
            relative_path = f"images/{image_name}"
            md_image = f"![图片]({relative_path})"
            
            # 插入到编辑器
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
            # 获取 markdown 文件所在目录
            md_dir = os.path.dirname(self.md_file_path)
            # 创建 images 子目录
            images_dir = os.path.join(md_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # 生成新文件名
            original_name = os.path.basename(source_path)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(original_name)
            new_name = f"{name}_{timestamp}{ext}"
            dest_path = os.path.join(images_dir, new_name)
            
            # 复制图片文件
            import shutil
            shutil.copy2(source_path, dest_path)
            
            # 生成相对路径的 markdown 图片语法
            relative_path = f"images/{new_name}"
            md_image = f"![{name}]({relative_path})"
            
            # 插入到编辑器
            cursor = editor.textCursor()
            cursor.insertText(md_image)
            
            logger.info(f"图片已复制: {dest_path}")
            
        except Exception as e:
            logger.error(f"插入图片失败: {str(e)}")
            QMessageBox.critical(self, "插入失败", f"插入图片时出错:\n{str(e)}")
    
    def export_to_pdf(self):
        """导出当前内容为PDF文件"""
        # 获取默认文件名
        default_filename = "导出文档.pdf"
        if self.md_file_path:
            default_filename = os.path.splitext(os.path.basename(self.md_file_path))[0] + ".pdf"
        
        # 弹出保存文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出PDF",
            default_filename,
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        try:
            from PySide6.QtPrintSupport import QPrinter
            # 创建打印机对象，设置为PDF格式
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            
            # 设置页面大小为A4
            printer.setPageSize(QPrinter.A4)
            
            # 获取当前编辑器
            current_widget = self.content_stack.currentWidget()
            if current_widget == self.splitter:
                active_editor = self.split_editor
            else:
                active_editor = self.editor
            
            # 打印文档到PDF
            active_editor.document().print_(printer)
            
            logger.info(f"PDF导出成功: {file_path}")
            QMessageBox.information(self, "导出成功", f"PDF文件已保存到:\n{file_path}")
        except Exception as e:
            logger.error(f"PDF导出失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出PDF时出错:\n{str(e)}")
        
    def _update_split_preview(self):
        """更新分屏预览内容（带防抖）"""
        # 使用防抖定时器，延迟 100ms 更新
        self._preview_update_timer.start(100)
    
    def _do_update_split_preview(self):
        """实际执行分屏预览更新，保持滚动位置"""
        md_content = self.split_editor.toPlainText()
        html_body = self._render_markdown_body(md_content)
        
        if not self._split_preview_initialized:
            # 首次加载，使用完整的 HTML
            full_html = self._render_markdown(md_content)
            # 设置 baseUrl 以支持本地图片加载
            if self.md_file_path:
                base_url = QUrl.fromLocalFile(os.path.dirname(self.md_file_path) + '/')
                self.split_preview.setHtml(full_html, base_url)
            else:
                self.split_preview.setHtml(full_html)
            self._split_preview_initialized = True
        else:
            # 后续更新，只更新内容，避免闪烁
            # 使用 JSON 来安全转义 HTML 内容
            html_json = json.dumps(html_body, ensure_ascii=False)
            js_code = f"""
                (function() {{
                    var content = document.getElementById('md-content');
                    if (content) {{
                        content.innerHTML = {html_json};
                    }}
                }})()
            """
            self.split_preview.page().runJavaScript(js_code)
    
    def _highlight_code_block(self, code, lang):
        """使用 Pygments 高亮代码块"""
        try:
            # 根据语言选择不同的样式
            if lang and lang.lower() in ['sql', 'mysql', 'postgresql', 'sqlite', 'plsql', 'tsql']:
                lexer = get_lexer_by_name('sql', stripall=True)
                formatter = DBeaverSQLStyle(cssclass='code-sql', nowrap=False)
            elif lang and lang.lower() in ['shell', 'bash', 'sh', 'zsh', 'ksh', 'powershell', 'pwsh']:
                lexer = get_lexer_by_name('bash', stripall=True)
                formatter = XShellStyle(cssclass='code-shell', nowrap=False)
            elif lang:
                # 其他语言使用默认样式
                try:
                    lexer = get_lexer_by_name(lang, stripall=True)
                except ClassNotFound:
                    lexer = guess_lexer(code)
                formatter = HtmlFormatter(cssclass='code-generic', nowrap=False)
            else:
                # 没有指定语言，尝试猜测
                try:
                    lexer = guess_lexer(code)
                except:
                    lexer = get_lexer_by_name('text', stripall=True)
                formatter = HtmlFormatter(cssclass='code-generic', nowrap=False)
            
            highlighted = highlight(code, lexer, formatter)
            return highlighted
        except Exception as e:
            # 如果高亮失败，返回原始代码
            return f'<pre><code>{code}</code></pre>'
    
    def _process_code_blocks(self, md_content):
        """处理 Markdown 中的代码块，使用 Pygments 进行语法高亮"""
        # 匹配 fenced code blocks: ```lang\ncode\n```
        pattern = r'```(\w*)\n(.*?)```'
        
        def replace_code_block(match):
            lang = match.group(1) or ''
            code = match.group(2)
            # 转义 HTML 特殊字符
            code_escaped = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return self._highlight_code_block(code_escaped, lang)
        
        # 使用 DOTALL 标志使 . 匹配换行符
        processed = re.sub(pattern, replace_code_block, md_content, flags=re.DOTALL)
        return processed
    
    def _render_markdown_body(self, md_content):
        """只渲染 Markdown 的 body 内容"""
        # 先处理代码块高亮
        processed_content = self._process_code_blocks(md_content)
        
        # 然后使用 markdown 库处理其他内容（不包括 fenced_code，因为我们已经处理了）
        return markdown.markdown(
            processed_content,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.toc',
                'markdown.extensions.nl2br'
            ]
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
            # 同步主编辑器内容到分屏编辑器
            self.split_editor.setPlainText(self.editor.toPlainText())
            # 重置分屏预览初始化标志，确保重新加载完整 HTML
            self._split_preview_initialized = False
            if update_preview:
                self._update_split_preview()
            self.content_stack.setCurrentIndex(2)
            self._is_preview_mode = False
            
    def _on_content_changed(self):
        """内容变化时触发"""
        self.content_changed.emit()
        # 如果在分屏模式，实时更新预览
        if self.content_stack.currentIndex() == 2:
            self._update_preview()
            
    def _update_preview(self):
        """更新预览内容"""
        md_content = self.editor.toPlainText()
        html_content = self._render_markdown(md_content)
        # 设置 baseUrl 以支持本地图片加载
        if self.md_file_path:
            base_url = QUrl.fromLocalFile(os.path.dirname(self.md_file_path) + '/')
            self.preview.setHtml(html_content, base_url)
        else:
            self.preview.setHtml(html_content)
        
    def _render_markdown(self, md_content):
        """将 Markdown 渲染为 HTML"""
        # 先处理代码块高亮
        processed_content = self._process_code_blocks(md_content)
        
        # 转换 Markdown 为 HTML
        html_body = markdown.markdown(
            processed_content,
            extensions=[
                'markdown.extensions.tables',
                'markdown.extensions.toc',
                'markdown.extensions.nl2br'
            ]
        )
        
        # 自然优雅配色方案 - 使用字符串拼接避免 format 冲突
        html_template = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            '    <meta charset="UTF-8">\n'
            "    <style>\n"
            "        /* 基础样式 - 柔和的米白背景 */\n"
            "        body {\n"
            "            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;\n"
            "            font-size: 15px;\n"
            "            line-height: 1.8;\n"
            "            color: #334155;\n"
            "            max-width: 800px;\n"
            "            margin: 0 auto;\n"
            "            padding: 40px 48px;\n"
            "            background: linear-gradient(180deg, #FDFCFA 0%, #F8F6F3 100%);\n"
            "            min-height: 100vh;\n"
            "        }\n"
            "        \n"
            "        /* 标题样式 - 温和的自然色系 */\n"
            "        h1, h2, h3, h4, h5, h6 {\n"
            "            font-weight: 600;\n"
            "            line-height: 1.4;\n"
            "            margin-top: 36px;\n"
            "            margin-bottom: 18px;\n"
            "            letter-spacing: -0.01em;\n"
            "        }\n"
            "        h1 {\n"
            "            font-size: 32px;\n"
            "            color: #1E3A5F;\n"
            "            border-bottom: 2px solid #E8E4DF;\n"
            "            padding-bottom: 16px;\n"
            "            margin-top: 0;\n"
            "        }\n"
            "        h2 {\n"
            "            font-size: 26px;\n"
            "            color: #2D5A7B;\n"
            "            border-left: 4px solid #5B8A72;\n"
            "            padding: 10px 18px;\n"
            "            background: linear-gradient(90deg, #F0F4F1 0%, transparent 100%);\n"
            "            border-radius: 0 8px 8px 0;\n"
            "        }\n"
            "        h3 {\n"
            "            font-size: 21px;\n"
            "            color: #4A7C59;\n"
            "            position: relative;\n"
            "            padding-left: 18px;\n"
            "        }\n"
            "        h3::before {\n"
            "            content: '';\n"
            "            position: absolute;\n"
            "            left: 0;\n"
            "            top: 50%;\n"
            "            transform: translateY(-50%);\n"
            "            width: 6px;\n"
            "            height: 6px;\n"
            "            background: #7BA05B;\n"
            "            border-radius: 50%;\n"
            "        }\n"
            "        h4 { font-size: 18px; color: #6B5B95; }\n"
            "        h5 { font-size: 16px; color: #8B6914; }\n"
            "        h6 { font-size: 15px; color: #9CA3AF; }\n"
            "        \n"
            "        /* 段落 */\n"
            "        p {\n"
            "            margin: 16px 0;\n"
            "            text-align: justify;\n"
            "            color: #475569;\n"
            "        }\n"
            "        \n"
            "        /* 行内代码 - 柔和的暖灰 */\n"
            "        code {\n"
            "            background: #F3F0EC;\n"
            "            color: #7C6F64;\n"
            "            padding: 3px 8px;\n"
            "            border-radius: 6px;\n"
            "            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;\n"
            "            font-size: 13px;\n"
            "            font-weight: 500;\n"
            "            border: 1px solid #E8E4DF;\n"
            "        }\n"
            "        \n"
            "        /* 代码块通用样式 */\n"
            "        pre {\n"
            "            padding: 24px 28px;\n"
            "            border-radius: 12px;\n"
            "            overflow-x: auto;\n"
            "            margin: 24px 0;\n"
            "            box-shadow: 0 4px 20px rgba(0,0,0,0.1);\n"
            "            position: relative;\n"
            "        }\n"
            "        pre::before {\n"
            "            content: '';\n"
            "            position: absolute;\n"
            "            top: 0;\n"
            "            left: 0;\n"
            "            right: 0;\n"
            "            height: 3px;\n"
            "            border-radius: 12px 12px 0 0;\n"
            "        }\n"
            "        pre code {\n"
            "            background: transparent;\n"
            "            padding: 0;\n"
            "            border: none;\n"
            "            font-size: 14px;\n"
            "            line-height: 1.7;\n"
            "            display: block;\n"
            "            margin-top: 20px;\n"
            "            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;\n"
            "        }\n"
            "        \n"
            "        /* SQL 代码块样式 - DBeaver 风格 */\n"
            "        .code-sql, pre.code-sql {\n"
            "            background: #1E1E1E;\n"
            "            color: #D4D4D4;\n"
            "        }\n"
            "        pre.code-sql::before {\n"
            "            background: linear-gradient(90deg, #4A90D9, #569CD6, #4EC9B0);\n"
            "        }\n"
            "        pre.code-sql::after {\n"
            "            content: 'SQL';\n"
            "            position: absolute;\n"
            "            top: 12px;\n"
            "            right: 20px;\n"
            "            font-size: 11px;\n"
            "            color: #569CD6;\n"
            "            font-weight: bold;\n"
            "            letter-spacing: 1px;\n"
            "        }\n"
            "        \n"
            "        /* Shell 代码块样式 - XShell 风格 */\n"
            "        .code-shell, pre.code-shell {\n"
            "            background: #0C0C0C;\n"
            "            color: #CCCCCC;\n"
            "        }\n"
            "        pre.code-shell::before {\n"
            "            background: linear-gradient(90deg, #4EC9B0, #569CD6, #6A9955);\n"
            "        }\n"
            "        pre.code-shell::after {\n"
            "            content: 'SHELL';\n"
            "            position: absolute;\n"
            "            top: 12px;\n"
            "            right: 20px;\n"
            "            font-size: 11px;\n"
            "            color: #4EC9B0;\n"
            "            font-weight: bold;\n"
            "            letter-spacing: 1px;\n"
            "        }\n"
            "        \n"
            "        /* 通用代码块样式 */\n"
            "        .code-generic, pre.code-generic {\n"
            "            background: #2C2926;\n"
            "            color: #E8E4DF;\n"
            "        }\n"
            "        pre.code-generic::before {\n"
            "            background: linear-gradient(90deg, #7BA05B, #5B8A72, #6B5B95);\n"
            "        }\n"
            "        pre.code-generic::after {\n"
            "            content: '● ● ●';\n"
            "            position: absolute;\n"
            "            top: 12px;\n"
            "            left: 20px;\n"
            "            font-size: 10px;\n"
            "            letter-spacing: 6px;\n"
            "            color: #8B7355;\n"
            "        }\n"
            "        \n"
            "        /* Pygments 语法高亮样式 */\n"
            "        .hll { background-color: #49483e }\n"
            "        .c { color: #6A9955; font-style: italic } /* Comment */\n"
            "        .err { color: #F44747 } /* Error */\n"
            "        .k { color: #569CD6; font-weight: bold } /* Keyword */\n"
            "        .o { color: #D4D4D4 } /* Operator */\n"
            "        .cm { color: #6A9955; font-style: italic } /* Comment.Multiline */\n"
            "        .cp { color: #C586C0 } /* Comment.Preproc */\n"
            "        .c1 { color: #6A9955; font-style: italic } /* Comment.Single */\n"
            "        .cs { color: #6A9955; font-style: italic } /* Comment.Special */\n"
            "        .gd { color: #F44747 } /* Generic.Deleted */\n"
            "        .ge { font-style: italic } /* Generic.Emph */\n"
            "        .gr { color: #F44747 } /* Generic.Error */\n"
            "        .gh { color: #FFFFFF } /* Generic.Heading */\n"
            "        .gi { color: #4EC9B0 } /* Generic.Inserted */\n"
            "        .go { color: #D4D4D4 } /* Generic.Output */\n"
            "        .gp { color: #D4D4D4 } /* Generic.Prompt */\n"
            "        .gs { font-weight: bold } /* Generic.Strong */\n"
            "        .gu { color: #FFFFFF } /* Generic.Subheading */\n"
            "        .gt { color: #F44747 } /* Generic.Traceback */\n"
            "        .kc { color: #569CD6; font-weight: bold } /* Keyword.Constant */\n"
            "        .kd { color: #569CD6; font-weight: bold } /* Keyword.Declaration */\n"
            "        .kn { color: #C586C0 } /* Keyword.Namespace */\n"
            "        .kp { color: #569CD6 } /* Keyword.Pseudo */\n"
            "        .kr { color: #569CD6; font-weight: bold } /* Keyword.Reserved */\n"
            "        .kt { color: #4EC9B0 } /* Keyword.Type */\n"
            "        .ld { color: #CE9178 } /* Literal.Date */\n"
            "        .m { color: #B5CEA8 } /* Literal.Number */\n"
            "        .s { color: #CE9178 } /* Literal.String */\n"
            "        .na { color: #9CDCFE } /* Name.Attribute */\n"
            "        .nb { color: #4EC9B0 } /* Name.Builtin */\n"
            "        .nc { color: #4EC9B0 } /* Name.Class */\n"
            "        .no { color: #569CD6 } /* Name.Constant */\n"
            "        .nd { color: #DCDCAA } /* Name.Decorator */\n"
            "        .ni { color: #D4D4D4 } /* Name.Entity */\n"
            "        .ne { color: #4EC9B0 } /* Name.Exception */\n"
            "        .nf { color: #DCDCAA } /* Name.Function */\n"
            "        .nl { color: #9CDCFE } /* Name.Label */\n"
            "        .nn { color: #4EC9B0 } /* Name.Namespace */\n"
            "        .nt { color: #569CD6 } /* Name.Tag */\n"
            "        .nv { color: #9CDCFE } /* Name.Variable */\n"
            "        .ow { color: #C586C0 } /* Operator.Word */\n"
            "        .w { color: #D4D4D4 } /* Text.Whitespace */\n"
            "        .mb { color: #B5CEA8 } /* Literal.Number.Bin */\n"
            "        .mf { color: #B5CEA8 } /* Literal.Number.Float */\n"
            "        .mh { color: #B5CEA8 } /* Literal.Number.Hex */\n"
            "        .mi { color: #B5CEA8 } /* Literal.Number.Integer */\n"
            "        .mo { color: #B5CEA8 } /* Literal.Number.Oct */\n"
            "        .sb { color: #CE9178 } /* Literal.String.Backtick */\n"
            "        .sc { color: #CE9178 } /* Literal.String.Char */\n"
            "        .sd { color: #6A9955 } /* Literal.String.Doc */\n"
            "        .s2 { color: #CE9178 } /* Literal.String.Double */\n"
            "        .se { color: #D7BA7D } /* Literal.String.Escape */\n"
            "        .sh { color: #CE9178 } /* Literal.String.Heredoc */\n"
            "        .si { color: #CE9178 } /* Literal.String.Interpol */\n"
            "        .sx { color: #CE9178 } /* Literal.String.Other */\n"
            "        .sr { color: #D16969 } /* Literal.String.Regex */\n"
            "        .s1 { color: #CE9178 } /* Literal.String.Single */\n"
            "        .ss { color: #CE9178 } /* Literal.String.Symbol */\n"
            "        .bp { color: #4EC9B0 } /* Name.Builtin.Pseudo */\n"
            "        .vc { color: #9CDCFE } /* Name.Variable.Class */\n"
            "        .vg { color: #9CDCFE } /* Name.Variable.Global */\n"
            "        .vi { color: #9CDCFE } /* Name.Variable.Instance */\n"
            "        .il { color: #B5CEA8 } /* Literal.Number.Integer.Long */\n"
            "        /* 引用块 - 淡雅的蓝色 */\n"
            "        blockquote {\n"
            "            margin: 24px 0;\n"
            "            padding: 18px 24px;\n"
            "            background: #F8FAFC;\n"
            "            border-left: 4px solid #7EB5D6;\n"
            "            border-radius: 0 10px 10px 0;\n"
            "            color: #4A5568;\n"
            "            font-style: italic;\n"
            "        }\n"
            "        blockquote p { margin: 8px 0; color: #556B6D; }\n"
            "        blockquote p:first-child { margin-top: 0; }\n"
            "        blockquote p:last-child { margin-bottom: 0; }\n"
            "        \n"
            "        /* 列表样式 - 自然色调 */\n"
            "        ul, ol {\n"
            "            margin: 18px 0;\n"
            "            padding-left: 28px;\n"
            "        }\n"
            "        ul {\n"
            "            list-style: none;\n"
            "            padding-left: 24px;\n"
            "        }\n"
            "        ul li {\n"
            "            position: relative;\n"
            "            margin: 10px 0;\n"
            "            padding-left: 22px;\n"
            "            color: #475569;\n"
            "        }\n"
            "        ul li::before {\n"
            "            content: '';\n"
            "            position: absolute;\n"
            "            left: 0;\n"
            "            top: 10px;\n"
            "            width: 8px;\n"
            "            height: 8px;\n"
            "            background: #7BA05B;\n"
            "            border-radius: 50%;\n"
            "        }\n"
            "        ol {\n"
            "            counter-reset: item;\n"
            "            list-style: none;\n"
            "        }\n"
            "        ol li {\n"
            "            position: relative;\n"
            "            margin: 10px 0;\n"
            "            padding-left: 32px;\n"
            "            color: #475569;\n"
            "        }\n"
            "        ol li::before {\n"
            "            counter-increment: item;\n"
            "            content: counter(item);\n"
            "            position: absolute;\n"
            "            left: 0;\n"
            "            top: 2px;\n"
            "            width: 22px;\n"
            "            height: 22px;\n"
            "            background: #5B8A72;\n"
            "            color: white;\n"
            "            font-size: 12px;\n"
            "            font-weight: 600;\n"
            "            border-radius: 50%;\n"
            "            display: flex;\n"
            "            align-items: center;\n"
            "            justify-content: center;\n"
            "        }\n"
            "        \n"
            "        /* 链接 - 优雅的蓝色 */\n"
            "        a {\n"
            "            color: #2D5A7B;\n"
            "            text-decoration: none;\n"
            "            font-weight: 500;\n"
            "            border-bottom: 1px solid transparent;\n"
            "            transition: all 0.2s ease;\n"
            "        }\n"
            "        a:hover {\n"
            "            color: #1E3A5F;\n"
            "            border-bottom-color: #2D5A7B;\n"
            "        }\n"
            "        \n"
            "        /* 图片 - 柔和的阴影 */\n"
            "        img {\n"
            "            max-width: 100%;\n"
            "            height: auto;\n"
            "            border-radius: 10px;\n"
            "            margin: 24px 0;\n"
            "            box-shadow: 0 8px 30px rgba(0,0,0,0.08);\n"
            "            display: block;\n"
            "        }\n"
            "        \n"
            "        /* 表格 - 温暖的大地色系 */\n"
            "        table {\n"
            "            width: 100%;\n"
            "            border-collapse: separate;\n"
            "            border-spacing: 0;\n"
            "            margin: 24px 0;\n"
            "            border-radius: 10px;\n"
            "            overflow: hidden;\n"
            "            box-shadow: 0 4px 12px rgba(0,0,0,0.05);\n"
            "            border: 1px solid #E8E4DF;\n"
            "        }\n"
            "        th {\n"
            "            background: #F5F2EE;\n"
            "            color: #4A5568;\n"
            "            font-weight: 600;\n"
            "            padding: 14px 18px;\n"
            "            text-align: left;\n"
            "            border-bottom: 2px solid #E8E4DF;\n"
            "        }\n"
            "        td {\n"
            "            padding: 12px 18px;\n"
            "            border-bottom: 1px solid #F0EDE8;\n"
            "            background-color: #FFFFFF;\n"
            "            color: #475569;\n"
            "        }\n"
            "        tr:last-child td {\n"
            "            border-bottom: none;\n"
            "        }\n"
            "        tr:nth-child(even) td {\n"
            "            background-color: #FDFCFB;\n"
            "        }\n"
            "        tr:hover td {\n"
            "            background-color: #F8F6F3;\n"
            "        }\n"
            "        \n"
            "        /* 分割线 - 柔和渐变 */\n"
            "        hr {\n"
            "            border: none;\n"
            "            height: 1px;\n"
            "            background: linear-gradient(90deg, transparent, #D1CFC9, #B8B5AE, #D1CFC9, transparent);\n"
            "            margin: 36px 0;\n"
            "        }\n"
            "        \n"
            "        /* 强调文字 - 温暖的色调 */\n"
            "        strong {\n"
            "            color: #8B4513;\n"
            "            font-weight: 600;\n"
            "        }\n"
            "        em {\n"
            "            color: #6B5B95;\n"
            "            font-style: italic;\n"
            "        }\n"
            "        \n"
            "        /* 删除线 */\n"
            "        del {\n"
            "            color: #9CA3AF;\n"
            "            text-decoration: line-through;\n"
            "            text-decoration-color: #D1CFC9;\n"
            "        }\n"
            "        \n"
            "        /* 任务列表 */\n"
            "        input[type=\"checkbox\"] {\n"
            "            width: 18px;\n"
            "            height: 18px;\n"
            "            margin-right: 10px;\n"
            "            accent-color: #5B8A72;\n"
            "            cursor: pointer;\n"
            "        }\n"
            "        \n"
            "        /* 滚动条 - 自然风格 */\n"
            "        ::-webkit-scrollbar {\n"
            "            width: 10px;\n"
            "            height: 10px;\n"
            "        }\n"
            "        ::-webkit-scrollbar-track {\n"
            "            background: #F5F2EE;\n"
            "        }\n"
            "        ::-webkit-scrollbar-thumb {\n"
            "            background: #D1CFC9;\n"
            "            border-radius: 5px;\n"
            "        }\n"
            "        ::-webkit-scrollbar-thumb:hover {\n"
            "            background: #B8B5AE;\n"
            "        }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "<div id=\"md-content\">\n"
            + html_body + "\n"
            "</div>\n"
            "</body>\n"
            "</html>"
        )
        
        return html_template
        
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
            
            # 根据当前模式刷新预览
            current_mode = self.content_stack.currentIndex()
            if current_mode == 1:  # 预览模式
                self._update_preview()
            elif current_mode == 2:  # 分屏模式
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
            # 确保父目录存在
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
