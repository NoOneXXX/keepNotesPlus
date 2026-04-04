import os
import sys
import traceback
import time
from datetime import datetime
from gui.func.left.file_encryption.encryption_data import  FolderDecryptor
from gui.func.left.file_encryption.DecryptPasswordDialog import DecryptPasswordDialog, DecryptSuccessDialog

# 辅助函数：获取资源文件路径（兼容开发环境和 Nuitka 打包环境）
def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 Nuitka 打包后的环境"""
    # 检查是否在 Nuitka 打包环境中
    if hasattr(sys, 'frozen') or getattr(sys, '_MEIPASS', None):
        # Nuitka 打包后的环境，使用可执行文件所在目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境，使用当前文件所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# 启动日志函数 - 用于捕获打包后的启动错误
def write_startup_log(message, level="INFO"):
    """写入启动日志到文件"""
    try:
        log_dir = get_resource_path("logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "startup.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except Exception as e:
        pass  # 忽略日志写入错误

def log_exception(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    write_startup_log(error_msg, "ERROR")
    # 显示错误对话框
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(None, "启动错误", f"程序启动失败:\n{str(exc_value)}\n\n详细信息请查看 logs/startup.log")
    except:
        pass

# 设置全局异常处理器
sys.excepthook = log_exception

write_startup_log("=== 程序启动 ===")
write_startup_log(f"Python 版本: {sys.version}")
write_startup_log(f"工作目录: {os.getcwd()}")
write_startup_log(f"sys.executable: {sys.executable}")
write_startup_log(f"sys.frozen: {getattr(sys, 'frozen', False)}")

try:
    from PySide6.QtWebEngineCore import QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView
    write_startup_log("PySide6 QtWebEngine 导入成功")
except Exception as e:
    write_startup_log(f"PySide6 QtWebEngine 导入失败: {e}", "ERROR")
    raise

try:
    from gui.func.utils.json_utils import JsonEditor
    from gui.func.utils.read_pdf_epud_txt_word_type.read_pdf import PDFPreviewer
    from gui.func.utils.read_pdf_epud_txt_word_type.read_docx import read_word
    write_startup_log("工具模块导入成功")
except Exception as e:
    write_startup_log(f"工具模块导入失败: {e}", "ERROR")
    raise

try:
    # Import the resource file to register the resources
    # 这个文件的引用不能删除 否则下面的图片就会找不到文件
    from gui.ui import resource_rc
    write_startup_log("Qt资源文件导入成功")
except Exception as e:
    write_startup_log(f"Qt资源文件导入失败: {e}", "ERROR")
    raise

from PySide6.QtCore import QSize, Qt, QtMsgType, qInstallMessageHandler, Slot, QUrl, QTimer
from PySide6.QtGui import QAction, QActionGroup, QFont, QIcon, QKeySequence, QTextCharFormat, QTextDocument, QImage
from PySide6.QtPrintSupport import QPrintDialog
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QWidget,
    QColorDialog,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QSizePolicy, QFrame, QTreeWidgetItem, QTableWidgetItem, QVBoxLayout, QStackedWidget
)

# Import the generated UI class from ui_main_window.py
from gui.ui.ui_main_window import Ui_MainWindow
from gui.func.left.XPNotebookTree import XPNotebookTree
from gui.func.right_top_corner.XPTreeRightTop import XPTreeRightTop
from gui.func.right_bottom_corner.RichTextEdit import RichTextEdit
from gui.func.right_bottom_corner.MarkdownEditor import MarkdownEditor
from gui.func.right_bottom_corner.MindMapEditor import MindMapEditor
from gui.func.top_menu.file_action import FileActions
from gui.func.settings.settings_page import SettingsDialog
from gui.func.singel_pkg.single_manager import sm
from gui.func.utils.constants import FONT_SIZES
try:
    import sip
except ImportError:
    sip = None
from gui.func.under_top_menu.color_picker import ColorPickerTool
import shutil
from urllib.parse import quote
from gui.func.utils import logger

# Custom Qt message handler for debugging
def qt_message_handler(msg_type: QtMsgType, context, msg: str):
    print(f"Qt Message [{msg_type}]: {msg} ({context.file}:{context.line})")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # 创建占位框（仅初始化时显示）
        self.placeholder_frame = QFrame()
        self.placeholder_frame.setMinimumWidth(200)
        self.placeholder_frame.setFrameShape(QFrame.StyledPanel)
        self.placeholder_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 100);  /* 白色半透明遮罩 */
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-image: url(:images/grandidier.jpg);
                background-repeat: no-repeat;
                background-position: center;
                background-origin: content;
            }
        """)

        # 加入左侧 verticalLayout（树位置）
        self.ui.verticalLayout.addWidget(self.placeholder_frame)

        # 绑定这个展示树状图的方法
        sm.left_tree_structure_rander_after_create_new_notebook_signal.connect(self.xp_tree_widget_)

        # 绑定又上角-------------------------------------------
        self.ui.noteTreeContainer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置 layout，如果没有则添加
        if self.ui.noteTreeContainer.layout() is None:
            self.layout = QVBoxLayout(self.ui.noteTreeContainer)
        else:
            self.layout = self.ui.noteTreeContainer.layout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # 必须加
        self.layout.setSpacing(0)
        # 清除旧内容
        for i in reversed(range(self.layout.count())):
            item = self.layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        # 加载 XPNotebookTree 右上角的树
        tree = XPTreeRightTop("")
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 设置扩展策略
        self.layout.addWidget(tree)
        # 绑定又上角-----------------结束--------------------------

        # 用来接收富文本框的路径
        self.richtext_saved_path = None
        sm.send_current_file_path_2_main_richtext_signal.connect(self.receiver_path)
        # Create editor using RichTextEdit
        # 富文本框
        self.rich_text_editor = RichTextEdit(self)
        # 监听文件改动 只要文件改动就进行保存
        self.rich_text_editor.textChanged.connect(self.auto_save_note)
        self.rich_text_editor.selectionChanged.connect(self.update_format)

        # 预创建 Markdown 编辑器（避免第一次打开时闪烁）
        self.markdown_editor = MarkdownEditor(self)
        self.markdown_editor.hide()
        # 连接 Markdown 编辑器的自动保存信号（在初始化时连接，避免首次创建文件时丢失）
        self.markdown_editor.content_changed.connect(self.auto_save_markdown)

        # 预创建思维导图编辑器
        self.mindmap_editor = MindMapEditor(self)
        self.mindmap_editor.hide()
        self.mindmap_editor.content_changed.connect(self.auto_save_mindmap)

        # 使用堆叠窗口管理多个编辑器
        self.editor_stack = QStackedWidget()
        self.editor_stack.addWidget(self.rich_text_editor)  # 索引 0
        self.editor_stack.addWidget(self.markdown_editor)   # 索引 1
        self.editor_stack.addWidget(self.mindmap_editor)    # 索引 2

        # Add editor stack to noteContentTable
        self.ui.noteContentTable.setCellWidget(0, 0, self.editor_stack)
        # default editor is rich text editor
        self.current_editor = self.rich_text_editor  # 默认
        self.current_editor_type = "richtext"  # 当前编辑器类型
        # 方法绑定 渲染pdf的时候转换引擎
        sm.send_pdf_path_2_main_signal.connect(self.replace_rictEditor_2_QWebEngineView)
        # 当pdf那边转换的了渲染引擎后 要重新换回来
        sm.change_web_engine_2_richtext_signal.connect(self.change_2_rich_text_editor)
        # Adjust table size
        self.ui.noteContentTable.setRowHeight(0, self.ui.noteContentTable.height())
        self.ui.noteContentTable.setColumnWidth(0, self.ui.noteContentTable.width())

        # Ensure the table resizes with the window
        self.ui.noteContentTable.horizontalHeader().setStretchLastSection(True)
        self.ui.noteContentTable.verticalHeader().setStretchLastSection(True)

        # Ensure the cell widget (RichTextEdit) fits perfectly
        self.ui.noteContentTable.setRowHeight(0, self.ui.noteContentTable.height())
        self.ui.noteContentTable.setColumnWidth(0, self.ui.noteContentTable.width())
        # Remove any default margins in the table
        self.ui.noteContentTable.setContentsMargins(0, 0, 0, 0)
        self.path = None

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # 初始化功能类
        self.file_actions = FileActions(self)  # 传入 self 以便弹窗等能绑定主窗口
        
        # File 菜单样式 - 现代优雅风格
        self.ui.menuFile.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 6px;
                font-size: 14px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 8px 32px 8px 12px;
                border-radius: 6px;
                color: #334155;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #EFF6FF;
                color: #2563EB;
            }
            QMenu::item:disabled {
                color: #94A3B8;
            }
            QMenu::icon {
                padding-left: 8px;
                margin-left: 0px;
            }
            QMenu::separator {
                height: 1px;
                background: #E2E8F0;
                margin: 6px 12px;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                margin-left: 8px;
            }
        """)

        # 创建笔记
        self.ui.menuFile.addAction(self.file_actions.create_file_action())
        # 打开笔记
        self.ui.menuFile.addAction(self.file_actions.open_notebook_action())
        # 打开最近的笔记本
        self.ui.menuFile.addAction(self.file_actions.open_recent_notebook_action())
        
        # 分隔线
        self.ui.menuFile.addSeparator()

        save_file_action = QAction(
            QIcon(":/images/disk.png"), "保存", self
        )
        save_file_action.setStatusTip("保存当前页面")
        save_file_action.setShortcut(QKeySequence.StandardKey.Save)
        save_file_action.triggered.connect(self.file_save)
        self.ui.menuFile.addAction(save_file_action)

        saveas_file_action = QAction(
            QIcon(":/images/disk--pencil.png"),
            "另存为...",
            self,
        )
        saveas_file_action.setStatusTip("保存到指定文件")
        saveas_file_action.triggered.connect(self.file_saveas)
        self.ui.menuFile.addAction(saveas_file_action)
        
        # 分隔线
        self.ui.menuFile.addSeparator()

        print_action = QAction(
            QIcon(":/images/printer.png"),
            "打印...",
            self,
        )
        print_action.setStatusTip("打印当前页面")
        print_action.setShortcut(QKeySequence.StandardKey.Print)
        print_action.triggered.connect(self.file_print)
        self.ui.menuFile.addAction(print_action)

        # 分隔线
        self.ui.menuFile.addSeparator()
        
        # 设置按钮
        settings_action = QAction(
            "⚙ 设置",
            self,
        )
        settings_action.setStatusTip("打开设置页面")
        settings_action.triggered.connect(self.open_settings)
        self.ui.menuFile.addAction(settings_action)


        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction(
            QIcon(":/images/arrow-curve-180-left.png"),
            "Undo",
            self,
        )
        undo_action.setStatusTip("Undo last change")
        undo_action.triggered.connect(self.rich_text_editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction(
            QIcon(":/images/arrow-curve.png"),
            "Redo",
            self,
        )
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.rich_text_editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(":/images/scissors.png"), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.rich_text_editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(
            QIcon(":/images/document-copy.png"),
            "Copy",
            self,
        )
        copy_action.setStatusTip("Copy selected text")
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.rich_text_editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(
            QIcon(":/images/clipboard-paste-document-text.png"),
            "Paste",
            self,
        )
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.rich_text_editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)

        select_action = QAction(
            QIcon(":/images/selection-input.png"),
            "Select all",
            self,
        )
        select_action.setStatusTip("Select all text")
        select_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_action.triggered.connect(self.rich_text_editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QAction(
            QIcon(":/images/arrow-continue.png"),
            "Wrap text to window",
            self,
        )
        wrap_action.setStatusTip("Toggle wrap text to window")
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(format_toolbar)
        format_menu = self.menuBar().addMenu("&Format")

        self.fonts = QFontComboBox()
        self.fonts.currentFontChanged.connect(self.rich_text_editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        # Define font sizes locally since constants.FONT_SIZES is unavailable

        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])
        # 设置默认选项为 14
        self.fontsize.setCurrentText("14")
        # 设置富文本初始字体大小为 14
        self.rich_text_editor.setFontPointSize(14)
        self.fontsize.currentTextChanged.connect(
            lambda s: self.rich_text_editor.setFontPointSize(float(s))
        )
        format_toolbar.addWidget(self.fontsize)

        self.bold_action = QAction(
            QIcon(":/images/edit-bold.png"), "Bold", self
        )
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        self.italic_action = QAction(
            QIcon(":/images/edit-italic.png"),
            "Italic",
            self,
        )
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.StandardKey.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self.toggle_italic)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(
            QIcon(":/images/edit-underline.png"),
            "Underline",
            self,
        )
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.StandardKey.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self.toggle_underline)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        # '''颜色选择 '''
        self.color_picker = ColorPickerTool(self.rich_text_editor, self)
        format_toolbar.addWidget(self.color_picker.tool_button)


        format_menu.addSeparator()

        self.alignl_action = QAction(
            QIcon(":/images/edit-alignment.png"),
            "Align left",
            self,
        )
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
        )
        format_toolbar.addAction(self.alignl_action)
        format_menu.addAction(self.alignl_action)

        self.alignc_action = QAction(
            QIcon(":/images/edit-alignment-center.png"),
            "Align center",
            self,
        )
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        )
        format_toolbar.addAction(self.alignc_action)
        format_menu.addAction(self.alignc_action)

        self.alignr_action = QAction(
            QIcon(":/images/edit-alignment-right.png"),
            "Align right",
            self,
        )
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        )
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.alignj_action = QAction(
            QIcon(":/images/edit-alignment-justify.png"),
            "Justify",
            self,
        )
        self.alignj_action.setStatusTip("Justify text")
        self.alignj_action.setCheckable(True)
        self.alignj_action.triggered.connect(
            lambda: self.rich_text_editor.setAlignment(Qt.AlignmentFlag.AlignJustify)
        )
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)

        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)

        color_toolbar = QToolBar("Color")
        color_toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(color_toolbar)
        color_menu = self.menuBar().addMenu("&Format")
        self.bold_action = QAction(
            QIcon(":/images/edit-bold.png"), "Bold", self
        )
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)
        color_toolbar.addAction(self.bold_action)
        color_menu.addAction(self.bold_action)

        # Add search box and button
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_text)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        # Add a spacer widget to push search_widget to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        color_toolbar.addWidget(spacer)
        # color_toolbar.addWidget(search_widget)

        self._format_actions = [
            self.fonts,
            self.fontsize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
        ]

        self.update_format()
        self.update_title()
        
        # 标记窗口已完成初始化，用于控制 resizeEvent 的行为
        # 注意：此标志在 show() 之后才设置为 True，避免初始化期间的 resize 事件导致闪烁
        self._window_initialized = False

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def update_format(self):
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.rich_text_editor.currentFont())
        self.fontsize.setCurrentText(str(int(self.rich_text_editor.fontPointSize())))

        self.italic_action.setChecked(self.rich_text_editor.fontItalic())
        self.underline_action.setChecked(self.rich_text_editor.fontUnderline())
        self.bold_action.setChecked(self.rich_text_editor.fontWeight() == QFont.Weight.Bold)

        self.alignl_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignLeft
        )
        self.alignc_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignCenter
        )
        self.alignr_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignRight
        )
        self.alignj_action.setChecked(
            self.rich_text_editor.alignment() == Qt.AlignmentFlag.AlignJustify
        )

        self.block_signals(self._format_actions, False)
    '''
    修改了富文本的内容 就自动的保存
    '''
    def auto_save_note(self):
        """Auto-save note and ensure all inserted images are saved and displayable."""
        #
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(self.richtext_saved_path)
        if content_type == "file" and self.richtext_saved_path is not None:
            # 写入到对应的文件
            file_path = os.path.join(self.richtext_saved_path, ".note.html")
            self.rich_text_editor.html_file_path = file_path
            self.rich_text_editor.clean_base64_images()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.rich_text_editor.toHtml())
            
            # 更新元数据中的修改时间
            self._update_modified_time(self.richtext_saved_path)



    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.show()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        try:
            with open(path, "rU") as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.rich_text_editor.setText(text)
            self.update_title()

    def file_save(self):
        if self.path is None:
            return self.file_saveas()

        text = (
            self.rich_text_editor.toHtml()
            if os.path.splitext(self.path)[1].lower() in ['.html', '.htm']
            else self.rich_text_editor.toPlainText()
        )

        try:
            with open(self.path, "w") as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save file",
            "",
            "HTML documents (*.html);Text documents (*.txt);All files (*.*)",
        )

        if not path:
            return

        text = (
            self.rich_text_editor.toHtml()
            if os.path.splitext(path)[1].lower() in ['.html', '.htm']
            else self.rich_text_editor.toPlainText()
        )

        try:
            with open(path, "w") as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec():
            self.rich_text_editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle(
            "%s - Megasolid Idiom"
            % (os.path.basename(self.path) if self.path else "Untitled")
        )

    def edit_toggle_wrap(self):
        self.rich_text_editor.setLineWrapMode(1 if self.rich_text_editor.lineWrapMode() == 0 else 0)

    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        weight = QFont.Bold if not cursor.charFormat().font().bold() else QFont.Normal
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        self.rich_text_editor.setTextCursor(cursor)

    def toggle_italic(self):
        """Toggle italic formatting for selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        italic = not cursor.charFormat().fontItalic()
        fmt.setFontItalic(italic)
        cursor.mergeCharFormat(fmt)
        self.rich_text_editor.setTextCursor(cursor)

    def toggle_underline(self):
        """Toggle underline formatting for selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        underline = not cursor.charFormat().fontUnderline()
        fmt.setFontUnderline(underline)
        cursor.mergeCharFormat(fmt)
        self.rich_text_editor.setTextCursor(cursor)

    def change_text_color(self):
        """Change the color of selected text."""
        cursor = self.rich_text_editor.textCursor()
        if not cursor.hasSelection():
            return

        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor.mergeCharFormat(fmt)
            self.rich_text_editor.setTextCursor(cursor)

    def search_text(self):
        """Search for text in the editor."""
        search_text = self.search_input.text()
        if not search_text:
            return

        cursor = self.rich_text_editor.document().find(search_text, self.rich_text_editor.textCursor())
        if not cursor.isNull():
            self.rich_text_editor.setTextCursor(cursor)
        else:
            self.status.showMessage("Text not found", 5000)

    '''
    绑定树状图的结构 当创建了新的笔记的时候就将树状图重新渲染
    '''
    @Slot(str)
    def xp_tree_widget_(self, file_path):
        if self.placeholder_frame is not None:
            try:
                self.ui.verticalLayout.removeWidget(self.placeholder_frame)
                self.placeholder_frame.setParent(None)
                self.placeholder_frame.deleteLater()
            except RuntimeError:
                print("placeholder_frame 已被 Qt 删除，跳过")
            self.placeholder_frame = None

        # self.ui.verticalLayout.removeWidget(self.placeholder_frame)
        # self.placeholder_frame.deleteLater()
        print(file_path)
        # 先清空 verticalLayout 中的旧组件
        self.clear_layout(self.ui.verticalLayout)
        tree_widget = XPNotebookTree(file_path, rich_text_edit=self.rich_text_editor)
        # 保存左侧树控件引用
        self.left_tree_widget = tree_widget
        # 连接 Markdown 编辑器信号
        tree_widget.open_markdown_editor.connect(self.open_markdown_editor)
        # 更新markdown的修改地址
        tree_widget.update_markdown_obj.connect(self.update_markdown_file_path)
        # 连接思维导图编辑器信号
        tree_widget.open_mindmap_editor.connect(self.open_mindmap_editor)
        # 解密文件夹
        tree_widget.unlock_dir_with_password.connect(self.unlock_dir_passwd)
        # 连接文件重命名信号
        tree_widget.file_renamed.connect(self.on_file_renamed)

        self.ui.verticalLayout.addWidget(tree_widget)



    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                # 可能是 layout 或 spacerItem
                child_layout = item.layout()
                if child_layout is not None:
                    self.clear_layout(child_layout)

    def resizeEvent(self, event):
        """Maintain splitter sizes on resize."""
        super().resizeEvent(event)
        # 只在窗口初始化完成后且可见时调整 splitter，避免启动时闪烁
        # 使用标志位确保只在用户手动调整大小时响应，而非初始化时
        if hasattr(self, '_window_initialized') and self.isVisible():
            self.ui.splitter.setSizes([300, self.width() - 300])
            self.ui.verticalSplitter.setSizes([215, self.height() - 215])
    '''
    富文本框的路径接收
    第一个参数判断路径 第二个参数判断树状图的属性 是属于谁的
    '''
    @Slot(str, str)
    def receiver_path(self,path_, flag):
        self.richtext_saved_path = path_
        # 右上角的数据渲染
        # 获取父目录 只有左侧的树状图点击的时候才会显示 右上角的结构 防止右上角的点击出现循环
        if 'left' == flag:
            # 清空 noteTreeContainer 中旧的 XPNotebookTree（右上角）
            self.clear_layout(self.layout)
            tree = XPTreeRightTop(path_,rich_text_edit=self.rich_text_editor)
            tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  #  设置扩展策略
            # 连接 Markdown 编辑器信号
            tree.open_markdown_editor.connect(self.open_markdown_editor)
            # 连接思维导图编辑器信号
            tree.open_mindmap_editor.connect(self.open_mindmap_editor)
            self.layout.addWidget(tree)

    # 动态的加载pdf
    @Slot(str)
    def replace_rictEditor_2_QWebEngineView(self, file_path):
        # 先切换回富文本编辑器（隐藏堆叠窗口）
        self.change_2_rich_text_editor()
        
        #获取后缀
        webview = None
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            previewer = PDFPreviewer()
            webview = previewer.get_webview(file_path)
        else:
            # 这个是渲染word文件
            docx_ = read_word(file_path)
            webview = docx_.render_word_to_webview()

        # 替换 UI 中组件 - 需要替换堆叠窗口本身
        self.ui.noteContentTable.removeCellWidget(0, 0)
        self.ui.noteContentTable.setCellWidget(0, 0, webview)
        self.ui.noteContentTable.setRowHeight(0, self.ui.noteContentTable.height())
        self.ui.noteContentTable.setColumnWidth(0, self.ui.noteContentTable.width())
        self.current_editor = webview
        self.current_editor_type = "webview"

    @Slot()
    def change_2_rich_text_editor(self):
        # 如果当前是 Markdown 编辑器，先保存
        if self.current_editor_type == "markdown" and self.markdown_editor and self.markdown_editor.md_file_path:
            current_md_path = self.markdown_editor.md_file_path
            logger.info(f"切换到富文本编辑器前保存 Markdown 文件: {current_md_path}")
            save_result = self.markdown_editor.save_file()
            if not save_result:
                logger.error(f"保存 Markdown 文件失败: {current_md_path}")
        
        # 如果当前是思维导图编辑器，先保存
        if self.current_editor_type == "mindmap" and self.mindmap_editor and self.mindmap_editor.mindmap_file_path:
            self.mindmap_editor.save_file()
        
        # 切换到富文本编辑器（只是切换堆叠窗口索引，无闪烁）
        self.editor_stack.setCurrentIndex(0)
        self.current_editor = self.rich_text_editor
        self.current_editor_type = "richtext"
        
        # 回传这个组件给file_load 用来更新他们的组件
        sm.received_rich_text_signal.emit(self.rich_text_editor)

        # 回传这个参数给left 左侧的树点击事件
        sm.received_rich_text_2_left_click_signal.emit(self.rich_text_editor)

    @Slot(str, str)
    def on_file_renamed(self, old_path, new_path):
        """处理文件重命名事件，更新编辑器路径"""
        # 检查当前是否是 Markdown 编辑器
        if self.current_editor_type == "markdown" and self.markdown_editor:
            # 获取旧的 Markdown 文件路径
            old_md_path = os.path.join(old_path, "document.md")
            # 获取新的 Markdown 文件路径
            new_md_path = os.path.join(new_path, "document.md")
            
            # 如果当前编辑的文件是被重命名的文件，更新编辑器路径
            if self.markdown_editor.md_file_path == old_md_path:
                logger.info(f"文件重命名，更新 Markdown 编辑器路径: {old_md_path} -> {new_md_path}")
                self.markdown_editor.set_file_path(new_md_path)
                self.path = new_md_path
                self.update_title()
        
        # 检查当前是否是思维导图编辑器
        if self.current_editor_type == "mindmap" and self.mindmap_editor:
            # 获取旧的思维导图文件路径
            old_mindmap_path = os.path.join(old_path, "mindmap.json")
            # 获取新的思维导图文件路径
            new_mindmap_path = os.path.join(new_path, "mindmap.json")
            
            # 如果当前编辑的文件是被重命名的文件，更新编辑器路径
            if self.mindmap_editor.mindmap_file_path == old_mindmap_path:
                logger.info(f"文件重命名，更新思维导图编辑器路径: {old_mindmap_path} -> {new_mindmap_path}")
                self.mindmap_editor.set_file_path(new_mindmap_path)
                self.path = new_mindmap_path
                self.update_title()

    @Slot(str)
    def update_markdown_file_path(self, file_path):
        """更新 Markdown 文件路径"""
        full_file_path = None
        import os
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(file_path)
        if content_type == "markdown":
            full_file_path = os.path.join(file_path, "document.md")
            self.markdown_editor.set_file_path(full_file_path)
        elif content_type == "mindmap":
            pass
        else:
            self.richtext_saved_path = file_path
            full_file_path = file_path
        self.path = full_file_path
        self.update_title()

    @Slot(str)
    def open_markdown_editor(self, file_path):
        """打开 Markdown 编辑器"""
        # 获取 Markdown 文件路径
        md_path = os.path.join(file_path, "document.md")
        
        # 如果已经在 Markdown 编辑器，先保存当前文件再加载新文件
        if self.current_editor_type == "markdown":
            # 强制保存当前编辑的内容，不检查 is_modified
            # 使用当前编辑器保存路径，而不是新路径
            current_md_path = self.markdown_editor.md_file_path
            if current_md_path:
                logger.info(f"切换前保存当前 Markdown 文件: {current_md_path}")
                save_result = self.markdown_editor.save_file()
                if not save_result:
                    logger.error(f"保存当前 Markdown 文件失败: {current_md_path}")
            
            # 保存完成后再设置新路径并加载
            self.markdown_editor.set_file_path(md_path)
            if os.path.exists(md_path):
                self.markdown_editor.load_file(md_path)
            else:
                # 如果文件不存在，清空编辑器内容
                self.markdown_editor.editor.clear()
                self.markdown_editor.split_editor.clear()
            self.path = md_path
            self.update_title()
            return
        
        # 从其他编辑器切换过来时，先保存当前编辑器内容
        if self.current_editor_type == "mindmap" and self.mindmap_editor and self.mindmap_editor.mindmap_file_path:
            self.mindmap_editor.save_file()
        elif self.current_editor_type == "richtext" and self.richtext_saved_path:
            self.auto_save_note()
        
        # 切换到 Markdown 编辑器（只是切换堆叠窗口索引，无闪烁）
        self.markdown_editor.set_file_path(md_path)
        if os.path.exists(md_path):
            self.markdown_editor.load_file(md_path)
        else:
            # 如果文件不存在，清空编辑器内容
            self.markdown_editor.editor.clear()
            self.markdown_editor.split_editor.clear()
        
        # 切换堆叠窗口索引
        self.editor_stack.setCurrentIndex(1)
        self.current_editor = self.markdown_editor
        self.current_editor_type = "markdown"
        
        # 更新标题
        self.path = md_path
        self.update_title()
    
    def auto_save_markdown(self):
        """自动保存 Markdown 文件"""
        if hasattr(self, 'markdown_editor') and self.markdown_editor:
            # 使用编辑器当前的文件路径保存
            current_md_path = self.markdown_editor.md_file_path
            if current_md_path:
                logger.debug(f"自动保存 Markdown 文件: {current_md_path}")
                save_result = self.markdown_editor.save_file()
                
                if save_result:
                    # 更新元数据中的修改时间
                    # md 文件在子目录下，需要获取父目录作为笔记路径
                    note_path = os.path.dirname(current_md_path)
                    self._update_modified_time(note_path)
                    self.status.showMessage("已自动保存", 2000)
                else:
                    logger.error(f"自动保存 Markdown 文件失败: {current_md_path}")
                    self.status.showMessage("自动保存失败", 2000)

    @Slot(str)
    def unlock_dir_passwd(self, file_path):
        """解密文件夹"""
        # 1. 弹出对话框 (逻辑已封装在 dialog.accept 中)
        dialog = DecryptPasswordDialog(file_path, self)

        # 只有当解密成功并调用了 super().accept()，这里才会返回 True
        if dialog.exec():
            # 2. 修改文件属性（解密后的后续操作）
            editor = JsonEditor()
            metadata_path = os.path.join(file_path, ".metadata.json")
            detail_info = editor.read_node_infos(file_path)

            content_type = detail_info['node']['detail_info']['content_type']
            detail_info['node']['detail_info']['content_type'] = content_type.replace("lock", "")
            detail_info['node']['detail_info']['tip'] = ""
            editor.writeByData(metadata_path, detail_info)

            # 3. 清理加密文件
            full_item_path = os.path.join(file_path, "encrypted_data.7z")
            if os.path.exists(full_item_path):
                os.remove(full_item_path)

            # 4. 刷新树结构
            if hasattr(self, 'left_tree_widget') and self.left_tree_widget:
                self.left_tree_widget.refresh_tree_by_path(file_path)

            # 5. 显示成功提示
            DecryptSuccessDialog(self).exec()




    @Slot(str)
    def open_mindmap_editor(self, file_path):
        """打开思维导图编辑器"""
        print(f"[MainWindow] open_mindmap_editor called with: {file_path}")
        
        # 获取思维导图文件路径
        mindmap_path = os.path.join(file_path, "mindmap.json")
        print(f"[MainWindow] mindmap_path: {mindmap_path}, exists: {os.path.exists(mindmap_path)}")
        
        # 如果已经在思维导图编辑器，先保存当前文件再加载新文件
        if self.current_editor_type == "mindmap":
            # 强制保存当前编辑的内容，不检查 is_modified
            if self.mindmap_editor.mindmap_file_path:
                self.mindmap_editor.save_file()
            
            self.mindmap_editor.set_file_path(mindmap_path)
            if os.path.exists(mindmap_path):
                self.mindmap_editor.load_file(mindmap_path)
            else:
                # 文件不存在，初始化新思维导图
                self.mindmap_editor.ensure_initialized()
            self.path = mindmap_path
            self.update_title()
            return
        
        # 从其他编辑器切换过来时，先保存当前编辑器内容
        if self.current_editor_type == "markdown" and self.markdown_editor and self.markdown_editor.md_file_path:
            current_md_path = self.markdown_editor.md_file_path
            logger.info(f"切换到思维导图编辑器前保存 Markdown 文件: {current_md_path}")
            save_result = self.markdown_editor.save_file()
            if not save_result:
                logger.error(f"保存 Markdown 文件失败: {current_md_path}")
        elif self.current_editor_type == "richtext" and self.richtext_saved_path:
            self.auto_save_note()
        
        # 切换到思维导图编辑器
        self.mindmap_editor.set_file_path(mindmap_path)
        if os.path.exists(mindmap_path):
            print(f"[MainWindow] Loading existing mindmap file")
            self.mindmap_editor.load_file(mindmap_path)
        else:
            print(f"[MainWindow] No existing mindmap file, initializing new one")
            # 文件不存在，初始化新思维导图
            self.mindmap_editor.ensure_initialized()
        
        # 切换堆叠窗口索引
        self.editor_stack.setCurrentIndex(2)
        self.current_editor = self.mindmap_editor
        self.current_editor_type = "mindmap"
        
        # 更新标题
        self.path = mindmap_path
        self.update_title()
    
    def auto_save_mindmap(self):
        """自动保存思维导图文件"""
        print(f"[MainWindow] auto_save_mindmap called")
        if hasattr(self, 'mindmap_editor') and self.mindmap_editor:
            print(f"[MainWindow] mindmap_file_path: {self.mindmap_editor.mindmap_file_path}")
            # 使用编辑器当前的文件路径保存
            result = self.mindmap_editor.save_file()
            print(f"[MainWindow] save result: {result}")
            
            # 更新元数据中的修改时间
            if self.mindmap_editor.mindmap_file_path:
                note_path = os.path.dirname(self.mindmap_editor.mindmap_file_path)
                self._update_modified_time(note_path)
            
            self.status.showMessage("已自动保存思维导图", 2000)
    
    def _update_modified_time(self, note_path):
        """更新笔记元数据中的修改时间"""
        if not note_path:
            return
        try:
            editor = JsonEditor()
            meta_path = os.path.join(note_path, ".metadata.json")
            if os.path.exists(meta_path):
                metadata = editor.read_node_infos(note_path)
                if metadata and isinstance(metadata, dict):
                    metadata['node']['detail_info']['updated_time'] = int(time.time())
                    editor.writeByData(meta_path, metadata)
        except Exception as e:
            pass  # 忽略更新时间错误

    def closeEvent(self, event):
        """窗口关闭时保存所有未保存的内容"""
        # 保存 Markdown 编辑器内容 - 强制保存当前内容
        if hasattr(self, 'markdown_editor') and self.markdown_editor and self.markdown_editor.md_file_path:
            # 直接调用 save_file，不检查 is_modified，确保内容一定被保存
            current_md_path = self.markdown_editor.md_file_path
            if os.path.exists(current_md_path):
                logger.info(f"窗口关闭前保存 Markdown 文件: {current_md_path}")
                save_result = self.markdown_editor.save_file()
                if not save_result:
                    logger.error(f"窗口关闭时保存 Markdown 文件失败: {current_md_path}")
        
        # 保存思维导图编辑器内容
        if hasattr(self, 'mindmap_editor') and self.mindmap_editor and self.mindmap_editor.mindmap_file_path and os.path.exists(self.mindmap_editor.mindmap_file_path):
            self.mindmap_editor.save_file()
        
        # 保存富文本编辑器内容
        # if self.richtext_saved_path and os.path.exists(self.richtext_saved_path):
        #     self.auto_save_note()
        
        event.accept()


    def open_settings(self):
        """打开设置对话框"""
        # 获取当前笔记本路径
        notebook_path = None
        if hasattr(self, 'file_actions') and self.file_actions:
            if hasattr(self.file_actions, 'path_') and self.file_actions.path_:
                notebook_path = self.file_actions.path_
        
        # 创建并显示设置对话框
        dialog = SettingsDialog(notebook_path, self)
        dialog.exec()



if __name__ == "__main__":
    try:
        write_startup_log("开始创建 QApplication")
        app = QApplication(sys.argv)
        app.setApplicationName("Megasolid Idiom")
        qInstallMessageHandler(qt_message_handler)
        write_startup_log("QApplication 创建成功")
        
        # 增加全局样式
        qss_path = get_resource_path("gui/ui/qss/light.qss")
        write_startup_log(f"样式文件路径: {qss_path}")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
            write_startup_log("样式文件加载成功")
        else:
            write_startup_log(f"警告: 找不到样式文件 {qss_path}", "WARN")

        write_startup_log("开始创建主窗口")
        window = MainWindow()
        write_startup_log("主窗口创建成功")
        
        try:
            logger.info(f'已经启动成功======')
        except:
            pass
        
        # 先设置窗口大小和位置，再显示窗口，避免闪烁
        window.resize(1079, 873)
        window.setGeometry(
            QApplication.primaryScreen().availableGeometry().width() // 2 - 540,
            QApplication.primaryScreen().availableGeometry().height() // 2 - 437,
            1079, 873
        )
        
        # 初始化 splitter 大小，避免显示后再调整导致闪烁
        window.ui.splitter.setSizes([300, 779])
        window.ui.verticalSplitter.setSizes([215, 658])
        
        window.show()
        # 窗口显示后才标记初始化完成，避免启动期间的 resize 事件导致 splitter 闪烁
        window._window_initialized = True
        write_startup_log("窗口显示完成，进入主循环")
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"主程序启动失败: {e}\n{traceback.format_exc()}"
        write_startup_log(error_msg, "ERROR")
        try:
            logger.error(f'main的启动报错信息是:{e}')
        except:
            pass
        # 显示错误对话框
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "启动错误", f"程序启动失败:\n{str(e)}\n\n详细信息请查看 logs/startup.log")
        except:
            pass
