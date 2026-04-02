import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPolygon
from PySide6.QtCore import Qt, QPoint

def generate_tree_icons(color_hex="#555555", size=20):
    app = QApplication.instance() or QApplication(sys.argv)
    color = QColor(color_hex)
    mid = size // 2

    # Helper to setup painter
    def get_painter(pix):
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(color, 1, Qt.DotLine))
        return p

    # 1. vline.png (Vertical Line)
    vline = QPixmap(size, size)
    vline.fill(Qt.transparent)
    painter = get_painter(vline)
    painter.drawLine(mid, 0, mid, size)
    painter.end()
    vline.save("vline.png")

    # 2. branch-more.png (T-shape)
    more = QPixmap(size, size)
    more.fill(Qt.transparent)
    painter = get_painter(more)
    painter.drawLine(mid, 0, mid, size)
    painter.drawLine(mid, mid, size, mid)
    painter.end()
    more.save("branch-more.png")

    # 3. branch-end.png (L-shape)
    end = QPixmap(size, size)
    end.fill(Qt.transparent)
    painter = get_painter(end)
    painter.drawLine(mid, 0, mid, mid)
    painter.drawLine(mid, mid, size, mid)
    painter.end()
    end.save("branch-end.png")


    print("Successfully generated: vline, branch-more, branch-end, branch-closed, branch-open")

if __name__ == "__main__":
    generate_tree_icons("#888888") # Change this hex to your preferred line color
