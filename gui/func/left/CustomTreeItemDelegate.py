from PySide6.QtWidgets import QStyledItemDelegate, QLineEdit, QStyle
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtCore import Qt, QRect

'''
这个是控制左边的树的边框高度，并支持根节点路径灰色显示
'''
class CustomTreeItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setMinimumHeight(23)  # 关键：设置更高高度
        editor.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 0px;
                border: 1px solid #3A8EDB;
                border-radius: 6px;
                background-color: white;
            }
        """)
        return editor
    
    def paint(self, painter, option, index):
        # 检查是否是根节点（笔记本名称）
        tree = self.parent()
        if tree:
            item = tree.itemFromIndex(index)
            if item and item.parent() is None:  # 根节点
                # 获取存储的路径信息
                path_text = item.data(0, Qt.UserRole + 3)
                if path_text:
                    # 先绘制默认内容（名称和图标）
                    super().paint(painter, option, index)
                    
                    # 然后绘制路径（灰色）
                    painter.save()
                    
                    # 获取项的视觉矩形
                    item_rect = tree.visualItemRect(item)
                    name_text = item.text(0)
                    
                    # 使用项的字体
                    font = item.font(0)
                    painter.setFont(font)
                    fm = painter.fontMetrics()
                    name_width = fm.horizontalAdvance(name_text)
                    
                    # 绘制路径文本
                    path_color = QColor("#9CA3AF")  # 灰色
                    painter.setPen(QPen(path_color))
                    
                    # 使用较小的字体显示路径
                    path_font = QFont(font)
                    path_font.setBold(False)
                    path_font.setPointSize(10)
                    painter.setFont(path_font)
                    
                    # 路径位置：在名称后面
                    path_x = item_rect.left() + name_width + 26  # 26 = 图标宽度 + 间距
                    path_y = item_rect.top() + (item_rect.height() + painter.fontMetrics().ascent() - painter.fontMetrics().descent()) // 2
                    
                    painter.drawText(path_x, path_y, path_text)
                    painter.restore()
                    return
        
        # 默认绘制
        super().paint(painter, option, index)
