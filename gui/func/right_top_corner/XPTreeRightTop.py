
import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTreeWidget,
    QTreeWidgetItem, QStyleFactory, QHeaderView, QAbstractItemView,
    QStyledItemDelegate, QStyle
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QPainter
from PySide6.QtCore import Qt, Slot, QUrl, Signal, QRect
import sys
import os
from gui.func.singel_pkg.single_manager import sm
from gui.func.utils.json_utils import JsonEditor
from PySide6.QtCore import QTimer
from gui.func.utils.file_loader import file_loader
from gui.func.utils.tools_utils import scan_supported_files

def format_time(ts):
    """格式化时间戳"""
    if ts is None:
        return "-"
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "-"


def get_file_times(path):
    """获取文件的创建时间和修改时间"""
    try:
        stat = os.stat(path)
        return stat.st_ctime, stat.st_mtime
    except:
        return None, None


class RowSelectionDelegate(QStyledItemDelegate):
    """自定义委托，绘制整行选中背景"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selection_color = QColor("#F3F4F6")  # 淡灰色选中背景
    
    def paint(self, painter, option, index):
        # 获取树控件
        tree = self.parent()
        if tree and isinstance(tree, QTreeWidget):
            # 检查是否选中
            item = tree.itemFromIndex(index)
            if item and item.isSelected():
                # 只在第一列绘制整行背景
                if index.column() == 0:
                    # 获取整行的矩形区域
                    row_rect = self._get_row_rect(tree, item)
                    if row_rect:
                        painter.save()
                        # painter.setRenderHint(painter.Antialiasing)
                        painter.setBrush(self._selection_color)
                        # painter.setPen(Qt.NoPen)
                        painter.drawRoundedRect(row_rect, 4, 4)
                        painter.restore()
        
        # 调用父类绘制内容
        super().paint(painter, option, index)
    
    def _get_row_rect(self, tree, item):
        """获取整行的矩形区域"""
        try:
            rect = tree.visualItemRect(item)
            header = tree.header()
            total_width = header.length()
            row_rect = QRect(
                0,
                rect.top(),
                total_width,
                rect.height()
            )
            return row_rect
        except:
            return None


class XPTreeRightTop(QWidget):
    # 信号定义
    open_markdown_editor = Signal(str)  # 打开 Markdown 编辑器
    open_mindmap_editor = Signal(str)   # 打开思维导图编辑器
    
    def __init__(self, path, selected_path=None, rich_text_edit=None, parent=None):
        super().__init__(parent)
        self.custom_path = os.path.expanduser(path)
        self.selected_path = os.path.expanduser(selected_path) if selected_path else None
        self.rich_text_edit = rich_text_edit
        
        # 需要加载的四种格式
        self.supported_exts = ['attachfile_pdf', 'attachfile_docx', 'attachfile_txt', 'attachfile_epub']

        # 图标资源
        self.folder_closed_icon = QIcon(QPixmap(":images/folder-orange.png"))
        self.folder_open_icon = QIcon(QPixmap(":images/folder-orange-open.png"))
        self.file_icon = QIcon(QPixmap(":images/note-violet.png"))
        self.markdown_icon = QIcon(QPixmap(":images/markdown.png"))
        self.mindmap_icon = QIcon(QPixmap(":images/mindmap.png"))  # 思维导图图标
        self.attach_file = QIcon(QPixmap(":images/attach-file.png"))
        self.trash_icon = QIcon(QPixmap(":images/garbage.png"))

        self.tree = None
        self.header_widget = None
        self.setup_ui()

        QTimer.singleShot(100, lambda: self.select_path_item(self.selected_path)) if self.selected_path else None

        # 确保 tree 已初始化和填充
        if self.selected_path:
            self.select_path_item(self.selected_path)

    def populate_tree(self, parent_item, path):
        """填充树结构，支持 dir、file、markdown、附件类型"""
        try:
            items = []
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                # 判断这个文件夹是不是文件 读取它下面的json配置
                editor = JsonEditor()
                # 读取detail_info的信息
                detail_info = editor.read_file_metadata_infos(full_path)
                content_type = '0'
                order_dir = 0
                created_time = None
                modified_time = None
                
                if detail_info:
                    content_type = detail_info.get('content_type', None)
                    order_dir = detail_info.get('order', 0)
                    created_time = detail_info.get('created_time', None)
                    modified_time = detail_info.get('updated_time', None)
                
                # 如果没有时间信息，使用文件系统时间
                if created_time is None or modified_time is None:
                    fs_created, fs_modified = get_file_times(full_path)
                    if created_time is None:
                        created_time = fs_created
                    if modified_time is None:
                        modified_time = fs_modified
                
                # 跳过 data 文件夹
                if name == 'data':
                    continue
                    
                if 'dir' == content_type:
                    # 文件夹类型
                    folder_item = QTreeWidgetItem()
                    self.set_item_icon(folder_item, content_type, 'collapsed', detail_info)
                    folder_item.setFont(0, QFont("Microsoft YaHei", 12))
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    folder_item.setText(1, format_time(created_time))
                    folder_item.setText(2, format_time(modified_time))
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    # 懒加载标记项
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())
                        
                elif content_type == "file":
                    # 普通文件类型
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, os.path.splitext(name)[0])
                    folder_item.setText(1, format_time(created_time))
                    folder_item.setText(2, format_time(modified_time))
                    folder_item.setIcon(0, self.file_icon)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    # 也允许子文件结构（懒加载子节点）
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())
                        
                elif content_type == "markdown":
                    # Markdown 文件类型
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    folder_item.setText(1, format_time(created_time))
                    folder_item.setText(2, format_time(modified_time))
                    folder_item.setIcon(0, self.markdown_icon)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())
                
                elif content_type == "mindmap":
                    # 思维导图文件类型
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    folder_item.setText(1, format_time(created_time))
                    folder_item.setText(2, format_time(modified_time))
                    # 使用思维导图专用图标，如果没有则使用markdown图标
                    folder_item.setIcon(0, self.mindmap_icon)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())
                        
                elif content_type and content_type.find('attachfile') != -1:
                    # 附件类型
                    folder_item = QTreeWidgetItem()
                    folder_item.setData(0, Qt.UserRole, full_path)
                    folder_item.setData(0, Qt.UserRole + 2, order_dir)
                    folder_item.setText(0, name)
                    folder_item.setText(1, format_time(created_time))
                    folder_item.setText(2, format_time(modified_time))
                    folder_item.setIcon(0, self.attach_file)
                    # 加入到集合
                    items.append((folder_item, order_dir))
                    if detail_info and detail_info.get('has_children', False):
                        folder_item.addChild(QTreeWidgetItem())

            # 按 order 排序
            items.sort(key=lambda x: x[1])
            for item, _ in items:
                parent_item.addChild(item)

        except PermissionError:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["名称", "创建时间", "修改时间"])
        
        # 设置整行选中
        self.tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.setAlternatingRowColors(False)
        # 隐藏根节点的展开/折叠指示器
        self.tree.setRootIsDecorated(True)

        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 200)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, 150)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        
        style = QStyleFactory.create("Fusion")
        if style:
            self.tree.setStyle(style)

        self.tree.itemExpanded.connect(self.handle_item_expanded)
        self.tree.itemCollapsed.connect(self.handle_item_collapsed)

        layout.addWidget(self.tree)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.setItemDelegate(RowSelectionDelegate(self.tree))
        '''自定义样式'''
        self.tree.setStyleSheet(QTREEW_WIDGET_STYLE)

        # 左键点击事件
        self.tree.itemClicked.connect(self.on_item_clicked)

        if os.path.exists(self.custom_path):
            root = QTreeWidgetItem(self.tree)
            notebook_name = os.path.basename(self.custom_path)
            root.setText(0, notebook_name)
            # 获取创建时间和更新时间
            json_editor = JsonEditor()
            detail_infos = json_editor.read_file_metadata_infos(self.custom_path)
            create_time = detail_infos.get('created_time', None) if detail_infos else None
            modified_time = detail_infos.get('updated_time', None) if detail_infos else None
            
            # 如果没有时间信息，使用文件系统时间
            if create_time is None or modified_time is None:
                fs_created, fs_modified = get_file_times(self.custom_path)
                if create_time is None:
                    create_time = fs_created
                if modified_time is None:
                    modified_time = fs_modified
            
            root.setText(1, format_time(create_time))
            root.setText(2, format_time(modified_time))
            root.setIcon(0, self.folder_closed_icon)
            font = QFont("Segoe UI", 12)
            font.setBold(True)
            root.setFont(0, font)
            root.setData(0, Qt.UserRole, self.custom_path)
            root.addChild(QTreeWidgetItem())
            root.setExpanded(True)

        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(False)

        if self.selected_path:
            self.select_item_by_path(self.selected_path)

    def select_item_by_path(self, target_path):
        def recurse(parent):
            for i in range(parent.childCount()):
                item = parent.child(i)
                item_path = item.data(0, Qt.UserRole)
                if item_path == target_path:
                    self.tree.setCurrentItem(item)
                    self.tree.scrollToItem(item)
                    return True
                if recurse(item):
                    item.setExpanded(True)
                    return True
            return False

        for i in range(self.tree.topLevelItemCount()):
            top_item = self.tree.topLevelItem(i)
            if recurse(top_item):
                break

    def handle_item_expanded(self, item):
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        detail_info = editor.read_file_metadata_infos(path)
        self.set_item_icon(item, content_type, 'expanded', detail_info)

        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.takeChild(0)
            if path:
                self.populate_tree(item, path)

    def handle_item_collapsed(self, item):
        path = item.data(0, Qt.UserRole)
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(path)
        detail_info = editor.read_file_metadata_infos(path)
        self.set_item_icon(item, content_type, 'collapsed', detail_info)

    def set_item_icon(self, item, content_type, exps, detail_infos):
        """设置项目图标"""
        if content_type == "dir":
            if exps == 'expanded':
                icon_path = detail_infos.get('open_dir_icon', ':images/folder-orange-open.png') if detail_infos else ':images/folder-orange-open.png'
            else:
                icon_path = detail_infos.get('close_dir_icon', ':images/folder-orange.png') if detail_infos else ':images/folder-orange.png'
            item.setIcon(0, QIcon(QPixmap(icon_path)))
        elif content_type == "file":
            icon_path = detail_infos.get('close_dir_icon', ':images/note-violet.png') if detail_infos else ':images/note-violet.png'
            item.setIcon(0, QIcon(QPixmap(icon_path)))
        elif content_type == "markdown":
            item.setIcon(0, self.markdown_icon)
        elif content_type == "mindmap":
            item.setIcon(0, self.mindmap_icon)
        elif content_type and content_type.find('attachfile') != -1:
            item.setIcon(0, self.attach_file)
        else:
            item.setIcon(0, self.file_icon)

    def select_path_item(self, path):
        def recursive_search(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.data(0, Qt.UserRole) == path:
                    self.tree.setCurrentItem(child)
                    self.tree.scrollToItem(child)
                    return True
                if recursive_search(child):
                    return True
            return False

        root = self.tree.invisibleRootItem()
        recursive_search(root)

    '''
    左键点击的方法实现
    '''
    def on_item_clicked(self, item):
        # 这个是在点击的时候将树状图给展开和合并
        if item.childCount() > 0:
            if item.isExpanded():
                item.setExpanded(False)
                self.handle_item_collapsed(item)
            else:
                item.setExpanded(True)
                self.handle_item_expanded(item)

        file_path = item.data(0, Qt.UserRole)
        
        editor = JsonEditor()
        content_type = editor.read_notebook_if_dir(file_path)
        
        # 处理 Markdown 文件类型
        if content_type == "markdown":
            self.open_markdown_editor.emit(file_path)
            return
        
        # 处理思维导图文件类型
        if content_type == "mindmap":
            self.open_mindmap_editor.emit(file_path)
            return
        
        # 触发这个更新富文本框的信号
        sm.change_web_engine_2_richtext_signal.emit()
        
        # 这个是发送地址给main那边 在那边自动保存的时候使用
        sm.send_current_file_path_2_main_richtext_signal.emit(file_path, 'right_top_cor')

        # 支持加载的类型：pdf、docx、txt、epub
        if content_type in self.supported_exts:
            # 扫描这个目录下的文件然后找到符合文件名字的路径
            exts_file_path = scan_supported_files(file_path, self.supported_exts)
            # 加载支持的文件类型
            loader_ = file_loader(exts_file_path, self.rich_text_edit)
            loader_.load_file()

        if content_type == "file" and self.rich_text_edit:
            note_path = os.path.join(file_path, ".note.html")
            if os.path.exists(note_path):
                with open(note_path, "r", encoding="utf-8") as f:
                    html = f.read()
                # 必须先设置 baseUrl
                base_url = QUrl.fromLocalFile(os.path.dirname(note_path) + os.sep)
                self.rich_text_edit.document().setBaseUrl(base_url)
                # 设置内容
                self.rich_text_edit.setHtml(html)


'''树状图样式 - 柔和自然风格'''
QTREEW_WIDGET_STYLE = """
    QTreeWidget {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        background-color: #FFFFFF;
        padding: 2px;
        font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
        font-size: 12px;
        outline: none;
    }
    QTreeWidget::item {
        padding: 2px 2px;
        border-radius: 4px;
        margin: 0px 1px;
        background-color: transparent;
        border: none;
    }
    QTreeWidget::item:selected {
        background-color: #E5E7EB;
        color: #111827;
    }
    QTreeWidget::item:hover {
        background-color: #F3F4F6;
    }
    QTreeWidget::item:selected:hover {
        background-color: #D1D5DB;
    }
    QHeaderView::section {
        background-color: #FAFAF9;
        color: #6B7280;
        font-weight: 500;
        font-size: 11px;
        padding: 5px 6px;
        min-height: 18px;
        border: none;
        border-bottom: 1px solid #E5E7EB;
        border-right: 1px solid #E5E7EB;
    }
    QHeaderView::section:last {
        border-right: none;
    }

    QTreeView::branch {
        background: transparent;
    }
    QTreeView::branch:has-children:!has-siblings:closed,
    QTreeView::branch:closed:has-children {
        image: url(:images/plus-square.svg);
    }
    QTreeView::branch:open:has-children:!has-siblings,
    QTreeView::branch:open:has-children {
        image: url(:images/minus-square.svg);
    }
"""

def main():
    app = QApplication(sys.argv)
    # 示例
    widget = XPTreeRightTop("/Users/echo/Desktop/temp/test",
                            selected_path="/Users/echo/Desktop/temp/test/新建文件/新建文件/多余的名字")
    widget.resize(700, 500)
    widget.setWindowTitle(f"目录树：{widget.custom_path}")
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
