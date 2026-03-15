"""
思维导图编辑器组件 - XMind 风格优化版
支持创建、编辑、保存思维导图
"""
import os
import json
import math

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem,
    QGraphicsPathItem, QInputDialog, QMessageBox, QFileDialog,
    QApplication, QMenu, QGraphicsProxyWidget, QLineEdit
)
from PySide6.QtGui import (
    QPen, QBrush, QColor, QFont, QPainter, QPainterPath, 
    QKeyEvent, QMouseEvent, QWheelEvent, QTransform,
    QAction, QCursor, QLinearGradient, QRadialGradient, QFontMetrics,
    QTextCursor
)
from PySide6.QtCore import (
    Qt, QRectF, QPointF, Signal, Slot, QMimeData, QDataStream,
    QByteArray, QIODevice, QLineF
)


class MindMapNode(QGraphicsRectItem):
    """思维导图节点 - XMind 风格优化版"""
    
    # 主题配色方案
    THEME_COLORS = {
        'root': {
            'bg': QColor("#FF6B6B"),
            'bg_gradient': [QColor("#FF6B6B"), QColor("#EE5A5A")],
            'border': QColor("#E05555"),
            'text': QColor("#FFFFFF"),
            'shadow': QColor(255, 107, 107, 80)
        },
        'level1': {
            'bg': QColor("#4ECDC4"),
            'bg_gradient': [QColor("#4ECDC4"), QColor("#3DBDB5")],
            'border': QColor("#3AA89F"),
            'text': QColor("#FFFFFF"),
            'shadow': QColor(78, 205, 196, 60)
        },
        'level2': {
            'bg': QColor("#45B7D1"),
            'bg_gradient': [QColor("#45B7D1"), QColor("#3AA0B8")],
            'border': QColor("#2E8AA0"),
            'text': QColor("#FFFFFF"),
            'shadow': QColor(69, 183, 209, 50)
        },
        'level3': {
            'bg': QColor("#96CEB4"),
            'bg_gradient': [QColor("#96CEB4"), QColor("#7AB8A0")],
            'border': QColor("#5FA085"),
            'text': QColor("#FFFFFF"),
            'shadow': QColor(150, 206, 180, 40)
        },
        'default': {
            'bg': QColor("#F8F9FA"),
            'bg_gradient': [QColor("#FFFFFF"), QColor("#F1F3F4")],
            'border': QColor("#DADCE0"),
            'text': QColor("#3C4043"),
            'shadow': QColor(0, 0, 0, 30)
        },
        'selected': {
            'bg': QColor("#FFE066"),
            'bg_gradient': [QColor("#FFE066"), QColor("#FFD43B")],
            'border': QColor("#FCC419"),
            'text': QColor("#212529"),
            'shadow': QColor(255, 224, 102, 100)
        }
    }
    
    text_changed = Signal()  # 文本变化信号
    
    def __init__(self, text="新建节点", parent=None, node_id=None, level=0):
        super().__init__(parent)
        self.node_id = node_id or id(self)
        self.text = text
        self.children_nodes = []
        self.parent_node = None
        self.level = level
        self.collapsed = False
        
        # 样式设置 - 更紧凑的间距
        self.padding_x = 12
        self.padding_y = 6
        self.corner_radius = 8
        self.min_width = 60
        self.min_height = 28
        
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # 创建文本项
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setDefaultTextColor(self.get_theme_color('text'))
        font = self.get_font_by_level()
        self.text_item.setFont(font)
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        
        # 连接文本变化信号
        self.text_item.document().contentsChanged.connect(self.on_text_changed)
        
        self.update_text(text)
        
    def get_theme_color(self, key):
        """获取主题颜色"""
        if self.isSelected():
            return self.THEME_COLORS['selected'][key]
        
        if self.level == 0:
            return self.THEME_COLORS['root'][key]
        elif self.level == 1:
            return self.THEME_COLORS['level1'][key]
        elif self.level == 2:
            return self.THEME_COLORS['level2'][key]
        elif self.level == 3:
            return self.THEME_COLORS['level3'][key]
        else:
            return self.THEME_COLORS['default'][key]
    
    def get_font_by_level(self):
        """根据层级获取字体 - 更紧凑的尺寸"""
        font = QFont("Microsoft YaHei", 10)
        if self.level == 0:
            font.setPointSize(14)
            font.setWeight(QFont.Bold)
        elif self.level == 1:
            font.setPointSize(12)
            font.setWeight(QFont.Bold)
        elif self.level == 2:
            font.setPointSize(11)
            font.setWeight(QFont.Medium)
        else:
            font.setPointSize(10)
            font.setWeight(QFont.Normal)
        return font
        
    def update_text(self, text):
        """更新节点文本"""
        self.text = text
        self.text_item.setPlainText(text)
        self.text_item.setDefaultTextColor(self.get_theme_color('text'))
        self.adjust_size()
        
    def adjust_size(self):
        """根据文本内容调整节点大小"""
        text_rect = self.text_item.boundingRect()
        
        # 计算新的尺寸，确保不小于最小值
        new_width = max(text_rect.width() + self.padding_x * 2, self.min_width)
        new_height = max(text_rect.height() + self.padding_y * 2, self.min_height)
        
        rect = QRectF(
            -new_width / 2,
            -new_height / 2,
            new_width,
            new_height
        )
        self.setRect(rect)
        self.text_item.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
        self.update()
        
    def on_text_changed(self):
        """文本编辑时实时调整大小"""
        if self.text_item.textInteractionFlags() & Qt.TextEditorInteraction:
            # 正在编辑中，实时调整大小
            self.adjust_size()
            # 通知场景更新连接线
            if self.scene():
                self.scene().update_connections()
                self.scene().content_changed.emit()
        
    def paint(self, painter, option, widget=None):
        """自定义绘制 - XMind 风格"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        
        # 绘制阴影
        shadow_color = self.get_theme_color('shadow')
        shadow_rect = rect.translated(1, 2)
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(shadow_rect, self.corner_radius, self.corner_radius)
        painter.fillPath(shadow_path, QBrush(shadow_color))
        
        # 绘制渐变背景
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        colors = self.get_theme_color('bg_gradient')
        gradient.setColorAt(0, colors[0])
        gradient.setColorAt(1, colors[1])
        
        path = QPainterPath()
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制边框
        border_color = self.get_theme_color('border')
        pen_width = 2 if self.level <= 1 else 1
        painter.setPen(QPen(border_color, pen_width))
        painter.drawPath(path)
        
        # 如果是选中状态，绘制高亮边框
        if self.isSelected():
            highlight_path = QPainterPath()
            highlight_rect = rect.adjusted(-2, -2, 2, 2)
            highlight_path.addRoundedRect(highlight_rect, self.corner_radius + 1, self.corner_radius + 1)
            painter.setPen(QPen(QColor("#FFD43B"), 2))
            painter.drawPath(highlight_path)
        
    def itemChange(self, change, value):
        """项目变化处理"""
        if change == QGraphicsItem.ItemSelectedChange:
            self.text_item.setDefaultTextColor(self.get_theme_color('text'))
            self.update()
        elif change == QGraphicsItem.ItemPositionChange:
            if self.scene():
                self.scene().update_connections()
        return super().itemChange(change, value)
        
    def mouseDoubleClickEvent(self, event):
        """双击编辑文本"""
        if event.button() == Qt.LeftButton:
            self.start_editing()
        super().mouseDoubleClickEvent(event)
        
    def start_editing(self):
        """开始编辑文本"""
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setFocus()
        cursor = self.text_item.textCursor()
        cursor.select(QTextCursor.Document)
        self.text_item.setTextCursor(cursor)
        
    def stop_editing(self):
        """停止编辑文本"""
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        new_text = self.text_item.toPlainText()
        if new_text != self.text:
            self.text = new_text
            self.adjust_size()
            if self.scene():
                self.scene().content_changed.emit()
        
    def focusOutEvent(self, event):
        """失去焦点时停止编辑"""
        self.stop_editing()
        super().focusOutEvent(event)
        
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() == Qt.ShiftModifier:
                # Shift+Enter 插入换行
                super().keyPressEvent(event)
            else:
                # Enter 结束编辑
                self.stop_editing()
                self.clearFocus()
        elif event.key() == Qt.Key_Escape:
            # Escape 取消编辑，恢复原文本
            self.text_item.setPlainText(self.text)
            self.adjust_size()
            self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
            self.clearFocus()
        else:
            super().keyPressEvent(event)
        
    def add_child(self, child_node):
        """添加子节点"""
        self.children_nodes.append(child_node)
        child_node.parent_node = self
        child_node.level = self.level + 1
        # 更新子节点字体
        child_node.text_item.setFont(child_node.get_font_by_level())
        child_node.update_text(child_node.text)
        
    def remove_child(self, child_node):
        """移除子节点"""
        if child_node in self.children_nodes:
            self.children_nodes.remove(child_node)
            child_node.parent_node = None
            
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.node_id,
            "text": self.text,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "level": self.level,
            "collapsed": self.collapsed,
            "children": [child.to_dict() for child in self.children_nodes]
        }
        
    @classmethod
    def from_dict(cls, data, parent=None):
        """从字典创建节点"""
        node = cls(
            text=data.get("text", "节点"), 
            parent=parent, 
            node_id=data.get("id"),
            level=data.get("level", 0)
        )
        node.setPos(data.get("x", 0), data.get("y", 0))
        node.collapsed = data.get("collapsed", False)
        return node


class MindMapScene(QGraphicsScene):
    """思维导图画布场景 - XMind 风格"""
    
    node_selected = Signal(object)  # 节点选中信号
    content_changed = Signal()  # 内容变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_node = None
        self.connections = []
        self.setSceneRect(-3000, -3000, 6000, 6000)
        
        # 设置背景 - 类似 XMind 的网格背景
        self.setBackgroundBrush(QBrush(QColor("#F5F7FA")))
        self.grid_enabled = True
        self.grid_size = 20
        
    def drawBackground(self, painter, rect):
        """绘制背景网格"""
        super().drawBackground(painter, rect)
        
        if not self.grid_enabled:
            return
            
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # 绘制点状网格
        pen = QPen(QColor("#E1E4E8"))
        pen.setWidth(1)
        painter.setPen(pen)
        
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        for x in range(left, int(rect.right()), self.grid_size):
            for y in range(top, int(rect.bottom()), self.grid_size):
                painter.drawPoint(x, y)
        
    def set_root_node(self, node, auto_layout=True, is_new_mindmap=False):
        """设置根节点
        
        Args:
            node: 根节点
            auto_layout: 是否自动布局（加载已有数据时设为False）
            is_new_mindmap: 是否是新创建的思维导图（用于决定是否强制居中根节点）
        """
        self.root_node = node
        self.addItem(node)
        if auto_layout:
            self.update_layout(force_center_root=is_new_mindmap)
        else:
            # 只更新连接线，保留节点位置
            self.update_connections()
        
    def add_node(self, parent_node=None, text="新建节点"):
        """添加新节点"""
        if parent_node is None:
            parent_node = self.root_node
            
        if parent_node is None:
            # 创建根节点 - 这是新创建的思维导图
            node = MindMapNode(text, level=0)
            self.set_root_node(node, auto_layout=True, is_new_mindmap=True)
        else:
            # 创建子节点
            node = MindMapNode(text, level=parent_node.level + 1)
            # 计算新节点位置
            pos = self._calculate_new_node_position(parent_node)
            node.setPos(pos)
            parent_node.add_child(node)
            self.addItem(node)
            self.update_connections()
            
        self.content_changed.emit()
        return node
        
    def _calculate_new_node_position(self, parent_node):
        """计算新节点的最佳位置"""
        children = parent_node.children_nodes
        if not children:
            # 第一个子节点
            return QPointF(parent_node.pos().x() + 250, parent_node.pos().y())
        
        # 找到最下方的子节点
        bottom_child = max(children, key=lambda c: c.pos().y())
        return QPointF(bottom_child.pos().x(), bottom_child.pos().y() + 80)
        
    def delete_node(self, node):
        """删除节点"""
        if node == self.root_node:
            QMessageBox.warning(None, "警告", "不能删除根节点")
            return
            
        # 递归删除子节点
        for child in node.children_nodes[:]:
            self.delete_node(child)
            
        # 从父节点中移除
        if node.parent_node:
            node.parent_node.remove_child(node)
            
        self.removeItem(node)
        self.update_connections()
        self.content_changed.emit()
        
    def update_layout(self, force_center_root=False):
        """更新布局 - 使用 XMind 风格的自动布局
        
        Args:
            force_center_root: 是否强制将根节点移动到中心位置（仅用于新创建的思维导图）
        """
        if self.root_node:
            # 仅在新创建思维导图时，确保根节点在合理的位置
            if force_center_root:
                root_pos = self.root_node.pos()
                if abs(root_pos.x()) < 10 and abs(root_pos.y()) < 10:
                    # 根节点在原点附近，设置到场景中心偏左
                    self.root_node.setPos(-200, 0)
            
            self._auto_layout(self.root_node)
            self.update_connections()
            
    def _auto_layout(self, node, direction=1):
        """自动布局算法 - XMind 风格紧凑布局（修复版）"""
        if not node:
            return
            
        if node.collapsed or not node.children_nodes:
            return
            
        children = node.children_nodes
        if not children:
            return
            
        level = node.level
        
        # 根据层级确定水平间距 - 更紧凑
        horizontal_gap = 180 - level * 25
        if horizontal_gap < 100:
            horizontal_gap = 100
            
        vertical_gap = 50  # 减小垂直间距
        
        # 递归先布局所有子节点的子节点，获取它们的高度
        child_heights = []
        for child in children:
            height = self._get_subtree_height(child)
            child_heights.append(height)
        
        # 计算总高度
        total_height = sum(child_heights) + (len(children) - 1) * vertical_gap
        
        # 计算起始 Y 位置
        current_y = node.pos().y() - total_height / 2
        
        for i, child in enumerate(children):
            if not child:  # 安全检查
                continue
            child_height = child_heights[i]
            # 计算子节点位置 - 子节点中心对齐
            new_x = node.pos().x() + horizontal_gap * direction
            new_y = current_y + child_height / 2
            
            child.setPos(new_x, new_y)
            
            # 递归布局子节点
            self._auto_layout(child, direction)
            
            current_y += child_height + vertical_gap
            
    def _get_subtree_height(self, node):
        """获取子树的高度"""
        if not node:
            return 40
            
        if node.collapsed or not node.children_nodes:
            return max(node.rect().height() if node.rect() else 40, 40)
        
        total_height = 0
        vertical_gap = 50
        
        for i, child in enumerate(node.children_nodes):
            if not child:
                continue
            child_height = self._get_subtree_height(child)
            total_height += child_height
            if i < len(node.children_nodes) - 1:
                total_height += vertical_gap
        
        return max(total_height, max(node.rect().height() if node.rect() else 40, 40))
            
    def update_connections(self):
        """更新连接线 - XMind 风格曲线"""
        # 清除旧连接线
        for line in self.connections:
            self.removeItem(line)
        self.connections.clear()
        
        # 绘制新连接线
        if self.root_node:
            self._draw_xmind_connections(self.root_node)
            
    def _draw_xmind_connections(self, node):
        """绘制 XMind 风格的连接线"""
        if node.collapsed:
            return
            
        for child in node.children_nodes:
            path = self._create_connection_path(node, child)
            
            # 创建路径项
            path_item = QGraphicsPathItem(path)
            
            # 根据层级设置线条样式
            if node.level == 0:
                pen = QPen(QColor("#CED4DA"), 3)
            elif node.level == 1:
                pen = QPen(QColor("#DEE2E6"), 2.5)
            else:
                pen = QPen(QColor("#E9ECEF"), 2)
                
            pen.setCapStyle(Qt.RoundCap)
            path_item.setPen(pen)
            
            # 将连接线放在节点后面
            path_item.setZValue(-1)
            self.addItem(path_item)
            self.connections.append(path_item)
            
            # 递归绘制子节点连接
            self._draw_xmind_connections(child)
            
    def _create_connection_path(self, parent, child):
        """创建 XMind 风格的连接路径 - 优化版"""
        path = QPainterPath()
        
        # 获取连接点 - 使用当前位置计算
        parent_pos = parent.pos()
        child_pos = child.pos()
        parent_rect = parent.rect()
        child_rect = child.rect()
        
        # 父节点右侧中心点（考虑节点中心偏移）
        start = QPointF(
            parent_pos.x() + parent_rect.width() / 2,
            parent_pos.y()
        )
        # 子节点左侧中心点
        end = QPointF(
            child_pos.x() - child_rect.width() / 2,
            child_pos.y()
        )
        
        # 计算控制点 - XMind 风格的平滑曲线
        dx = end.x() - start.x()
        
        # 控制点偏移量 - 根据距离动态调整
        ctrl_offset = max(abs(dx) * 0.5, 50)
        
        ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
        ctrl2 = QPointF(end.x() - ctrl_offset, end.y())
        
        path.moveTo(start)
        path.cubicTo(ctrl1, ctrl2, end)
        
        return path
        
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        super().mousePressEvent(event)
        item = self.itemAt(event.scenePos(), QTransform())
        if isinstance(item, MindMapNode):
            self.node_selected.emit(item)
        else:
            # 点击空白处，取消所有选中
            for node in self.selectedItems():
                node.setSelected(False)
            
    def contextMenuEvent(self, event):
        """右键菜单"""
        item = self.itemAt(event.scenePos(), QTransform())
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Microsoft YaHei UI', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 6px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #F0F0F0;
                color: #000000;
            }
            QMenu::separator {
                height: 1px;
                background: #E0E0E0;
                margin: 6px 12px;
            }
        """)
        
        if isinstance(item, MindMapNode):
            add_child_action = menu.addAction("🌿 添加子节点")
            add_sibling_action = menu.addAction("🌱 添加兄弟节点")
            menu.addSeparator()
            delete_action = menu.addAction("🗑 删除节点")
            menu.addSeparator()
            edit_action = menu.addAction("✏️ 编辑文本")
            
            action = menu.exec(event.screenPos())
            
            if action == add_child_action:
                self.add_node(item)
            elif action == add_sibling_action:
                if item.parent_node:
                    sibling = self.add_node(item.parent_node)
                    if sibling:
                        sibling.setPos(item.pos().x(), item.pos().y() + 80)
                        self.update_connections()
            elif action == delete_action:
                self.delete_node(item)
            elif action == edit_action:
                item.text_item.setFocus()
        else:
            add_root_action = menu.addAction("🌳 添加根节点")
            action = menu.exec(event.screenPos())
            
            if action == add_root_action:
                self.add_node(text="中心主题")
                
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Tab:
            # Tab 键添加子节点
            selected = self.selectedItems()
            if selected and isinstance(selected[0], MindMapNode):
                self.add_node(selected[0])
            event.accept()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter 键添加兄弟节点
            selected = self.selectedItems()
            if selected and isinstance(selected[0], MindMapNode):
                node = selected[0]
                if node.parent_node:
                    sibling = self.add_node(node.parent_node)
                    if sibling:
                        sibling.setPos(node.pos().x(), node.pos().y() + 80)
                        self.update_connections()
            event.accept()
        elif event.key() == Qt.Key_Delete:
            # Delete 键删除节点
            selected = self.selectedItems()
            if selected and isinstance(selected[0], MindMapNode):
                self.delete_node(selected[0])
            event.accept()
        else:
            super().keyPressEvent(event)
                
    def to_dict(self):
        """导出为字典"""
        if self.root_node:
            return self.root_node.to_dict()
        return {}
        
    def from_dict(self, data, apply_layout=False, is_new_mindmap=False):
        """从字典导入
        
        Args:
            data: 思维导图数据字典
            apply_layout: 是否重新应用自动布局（默认False，保留保存的位置）
            is_new_mindmap: 是否是新创建的思维导图（用于决定是否强制居中根节点）
        """
        print(f"[MindMapScene] from_dict called with data: {data}")
        
        # 先重置根节点，再清除场景
        self.root_node = None
        self.connections.clear()
        self.clear()
        
        print(f"[MindMapScene] Scene cleared, items count: {len(self.items())}")
        
        if data:
            # 加载时传递 is_loading=True，保留保存的位置
            self._build_tree(data, is_loading=True, is_new_mindmap=is_new_mindmap)
            print(f"[MindMapScene] Tree built, root_node: {self.root_node}")
            
            if apply_layout:
                # 只有明确要求时才应用自动布局
                self.update_layout(force_center_root=is_new_mindmap)
            else:
                # 使用保存的位置，只更新连接线
                self.update_connections()
            
            # 居中显示根节点
            if self.root_node and self.views():
                self.views()[0].centerOn(self.root_node)
        else:
            print("[MindMapScene] No data to load!")
            
    def _build_tree(self, data, parent=None, is_loading=False, is_new_mindmap=False):
        """递归构建树
        
        Args:
            data: 节点数据字典
            parent: 父节点
            is_loading: 是否是加载已有数据（True时保留位置）
            is_new_mindmap: 是否是新创建的思维导图
        """
        print(f"[MindMapScene] _build_tree: text={data.get('text')}, parent={parent}")
        node = MindMapNode.from_dict(data, parent)
        
        if parent is None:
            # 根节点：加载时不自动布局，新创建时应用布局并居中
            self.set_root_node(node, auto_layout=not is_loading, is_new_mindmap=is_new_mindmap)
            print(f"[MindMapScene] Set root_node: {node}, text: {node.text}")
        else:
            parent.add_child(node)
            self.addItem(node)
            print(f"[MindMapScene] Added child node: {node.text}")
            
        for child_data in data.get("children", []):
            self._build_tree(child_data, node, is_loading, is_new_mindmap)
            
        return node


class MindMapEditor(QWidget):
    """思维导图编辑器主组件 - XMind 风格"""
    
    content_changed = Signal()  # 内容变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mindmap_file_path = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI - XMind 风格工具栏"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 工具栏 - XMind 风格
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 10, 12, 10)
        toolbar.setSpacing(10)
        
        # 添加子节点按钮
        add_child_btn = QPushButton("🌿 子节点")
        add_child_btn.setToolTip("添加子节点 (Tab)")
        add_child_btn.setStyleSheet(self._get_toolbar_button_style("#4ECDC4"))
        add_child_btn.clicked.connect(self.add_child_node)
        toolbar.addWidget(add_child_btn)
        
        # 添加兄弟节点按钮
        add_sibling_btn = QPushButton("🌱 兄弟节点")
        add_sibling_btn.setToolTip("添加兄弟节点 (Enter)")
        add_sibling_btn.setStyleSheet(self._get_toolbar_button_style("#45B7D1"))
        add_sibling_btn.clicked.connect(self.add_sibling_node)
        toolbar.addWidget(add_sibling_btn)
        
        # 删除节点按钮
        delete_btn = QPushButton("🗑 删除")
        delete_btn.setToolTip("删除节点 (Delete)")
        delete_btn.setStyleSheet(self._get_toolbar_button_style("#FF6B6B"))
        delete_btn.clicked.connect(self.delete_selected_node)
        toolbar.addWidget(delete_btn)
        
        toolbar.addStretch()
        
        # 自动布局按钮
        layout_btn = QPushButton("📐 自动布局")
        layout_btn.setStyleSheet(self._get_toolbar_button_style("#96CEB4"))
        layout_btn.clicked.connect(self.auto_layout)
        toolbar.addWidget(layout_btn)
        
        # 保存按钮
        save_btn = QPushButton("💾 保存")
        save_btn.setStyleSheet(self._get_toolbar_button_style("#FFE066", text_color="#333333"))
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)
        
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E8E8E8;
            }
        """)
        toolbar_widget.setLayout(toolbar)
        layout.addWidget(toolbar_widget)
        
        # 图形视图
        self.view = QGraphicsView()
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        
        # 场景
        self.scene = MindMapScene()
        self.scene.node_selected.connect(self.on_node_selected)
        self.scene.content_changed.connect(self.on_content_changed)
        self.view.setScene(self.scene)
        
        layout.addWidget(self.view)
        
        # 状态栏
        status_widget = QWidget()
        status_widget.setStyleSheet("""
            QWidget {
                background-color: #FAFBFC;
                border-top: 1px solid #E8E8E8;
            }
        """)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(12, 6, 12, 6)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px; font-family: 'Microsoft YaHei UI', sans-serif;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 快捷键提示
        shortcut_label = QLabel("Tab: 添加子节点 | Enter: 添加兄弟节点 | Delete: 删除节点 | 滚轮: 缩放")
        shortcut_label.setStyleSheet("color: #999999; font-size: 11px; font-family: 'Microsoft YaHei UI', sans-serif;")
        status_layout.addWidget(shortcut_label)
        
        layout.addWidget(status_widget)
        
        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 初始化时不创建默认根节点，等待加载或新建时创建
        self._initialized = False
        
    def _get_toolbar_button_style(self, color, text_color="white"):
        """获取工具栏按钮样式"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background-color: {color}E0;
            }}
            QPushButton:pressed {{
                background-color: {color}C0;
            }}
        """
        
    def add_child_node(self):
        """添加子节点"""
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], MindMapNode):
            node = self.scene.add_node(selected[0])
        else:
            # 如果没有选中节点，添加到根节点
            node = self.scene.add_node(self.scene.root_node)
            
        if node:
            node.setSelected(True)
            self.status_label.setText(f"已添加子节点: {node.text}")
            self.content_changed.emit()
            
    def add_sibling_node(self):
        """添加兄弟节点"""
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], MindMapNode):
            node = selected[0]
            if node.parent_node:
                sibling = self.scene.add_node(node.parent_node)
                if sibling:
                    # 放在选中节点下方
                    sibling.setPos(node.pos().x(), node.pos().y() + 80)
                    self.scene.update_connections()
                    sibling.setSelected(True)
                    self.status_label.setText(f"已添加兄弟节点: {sibling.text}")
                    self.content_changed.emit()
            else:
                self.status_label.setText("根节点不能添加兄弟节点")
        else:
            self.status_label.setText("请先选中一个节点")
            
    def delete_selected_node(self):
        """删除选中节点"""
        selected = self.scene.selectedItems()
        if selected and isinstance(selected[0], MindMapNode):
            node = selected[0]
            if node == self.scene.root_node:
                QMessageBox.warning(self, "警告", "不能删除根节点")
                return
            self.scene.delete_node(node)
            self.status_label.setText("已删除节点")
            self.content_changed.emit()
            
    def auto_layout(self):
        """自动布局"""
        if self.scene.root_node:
            # 用户手动触发自动布局时，强制居中根节点
            self.scene.update_layout(force_center_root=True)
            self.status_label.setText("已自动布局")
            # 居中显示根节点
            self.view.centerOn(self.scene.root_node)
            
    def on_node_selected(self, node):
        """节点选中处理"""
        self.status_label.setText(f"选中: {node.text}")
        
    def on_content_changed(self):
        """内容变化处理"""
        self.content_changed.emit()
        
    def set_file_path(self, file_path):
        """设置文件路径"""
        self.mindmap_file_path = file_path
        if file_path:
            self.status_label.setText(f"文件: {os.path.basename(file_path)}")
            
    def ensure_initialized(self):
        """确保编辑器已初始化（有根节点）"""
        if not self._initialized and not self.scene.root_node:
            self.scene.add_node(text="中心主题")
            self._initialized = True
            
    def load_file(self, file_path):
        """加载思维导图文件"""
        try:
            print(f"[MindMapEditor] Loading file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[MindMapEditor] Loaded data: {data}")
            
            # 检查数据是否有效
            if not data or not isinstance(data, dict):
                QMessageBox.critical(self, "加载失败", "思维导图文件格式无效")
                return False
            
            # 检查是否是初始数据（没有子节点且位置在原点）
            is_initial = (
                not data.get("children") and 
                data.get("x", 0) == 0 and 
                data.get("y", 0) == 0
            )
            
            print(f"[MindMapEditor] Before from_dict, root_node: {self.scene.root_node}")
            
            if is_initial:
                # 初始数据：创建节点并应用自动布局，强制居中根节点
                self.scene.from_dict(data, apply_layout=True, is_new_mindmap=True)
                print(f"[MindMapEditor] Applied auto layout for initial data")
            else:
                # 已有数据：保留保存的位置，不强制居中
                self.scene.from_dict(data, apply_layout=False, is_new_mindmap=False)
                print(f"[MindMapEditor] Preserved saved positions")
            
            print(f"[MindMapEditor] After from_dict, root_node: {self.scene.root_node}")
            
            self.set_file_path(file_path)
            self._initialized = True
            
            # 确保视图正确显示
            if self.scene.root_node:
                # 重置视图缩放
                self.view.resetTransform()
                # 居中显示根节点
                self.view.centerOn(self.scene.root_node)
                print(f"[MindMapEditor] Centered on root node at: {self.scene.root_node.pos()}")
            else:
                print("[MindMapEditor] Warning: root_node is None after loading!")
                
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "加载失败", f"思维导图文件格式错误:\n{e}")
            return False
        except Exception as e:
            import traceback
            print(f"[MindMapEditor] Load error: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "加载失败", f"无法加载思维导图文件:\n{e}")
            return False
            
    def save_file(self, file_path=None):
        """保存思维导图文件"""
        print(f"[MindMapEditor] save_file called, file_path={file_path}, mindmap_file_path={self.mindmap_file_path}")
        
        if file_path:
            self.mindmap_file_path = file_path
            
        if not self.mindmap_file_path:
            print("[MindMapEditor] No file path set, cannot save")
            return False
            
        try:
            data = self.scene.to_dict()
            print(f"[MindMapEditor] Saving data: {data}")
            
            # 确保目录存在
            parent_dir = os.path.dirname(self.mindmap_file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                
            with open(self.mindmap_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"[MindMapEditor] File saved successfully: {self.mindmap_file_path}")
            self.status_label.setText(f"已保存: {os.path.basename(self.mindmap_file_path)}")
            return True
        except Exception as e:
            import traceback
            print(f"[MindMapEditor] Save error: {e}\n{traceback.format_exc()}")
            QMessageBox.critical(self, "保存失败", f"无法保存思维导图文件:\n{e}")
            return False
            
    def get_content(self):
        """获取当前内容"""
        return self.scene.to_dict()
        
    def set_content(self, data):
        """设置内容"""
        if isinstance(data, dict):
            self.scene.from_dict(data)
        elif isinstance(data, str):
            try:
                data = json.loads(data)
                self.scene.from_dict(data)
            except:
                pass
                
    def is_modified(self):
        """检查是否有修改（简化实现）"""
        return False
        
    def wheelEvent(self, event):
        """滚轮缩放"""
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.view.scale(1.1, 1.1)
            else:
                self.view.scale(0.9, 0.9)
        else:
            super().wheelEvent(event)
