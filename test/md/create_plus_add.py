import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect


def generate_perfect_icons(color_hex="#000000", size=15):
    # 使用奇数尺寸 (21) 更容易定位物理中心点 (10, 10)
    app = QApplication.instance() or QApplication(sys.argv)
    color = QColor(color_hex)
    mid = size // 2  # 中心点坐标

    # 定义方框大小（9x9 像素）
    box_size = 8  # 边长
    offset = box_size // 2

    def draw_box(painter):
        # 禁用抗锯齿以获得锐利的 1 像素线条
        painter.setRenderHint(QPainter.Antialiasing, False)
        # 画黑色边框，白色填充（为了挡住后面的虚线）
        painter.setPen(QPen(color, 1, Qt.SolidLine))
        painter.setBrush(Qt.white)
        # 矩形左上角坐标计算，确保中心对称
        rect = QRect(mid - offset, mid - offset, box_size, box_size)
        painter.drawRect(rect)
        return rect

    # --- 1. 生成 branch-closed.png [+] ---
    closed = QPixmap(size, size)
    closed.fill(Qt.transparent)
    p = QPainter(closed)
    draw_box(p)
    p.setPen(QPen(color, 1, Qt.SolidLine))
    # 横线：在中心行绘制
    p.drawLine(mid - 2, mid, mid + 2, mid)
    # 竖线：在中心列绘制
    p.drawLine(mid, mid - 2, mid, mid + 2)
    p.end()
    closed.save("branch-closed.png")

    # --- 2. 生成 branch-open.png [-] ---
    opened = QPixmap(size, size)
    opened.fill(Qt.transparent)
    p = QPainter(opened)
    draw_box(p)
    p.setPen(QPen(color, 1, Qt.SolidLine))
    # 仅横线
    p.drawLine(mid - 2, mid, mid + 2, mid)
    p.end()
    opened.save("branch-open.png")

    # --- 3. 生成 vline, more, end (使用深色且不开启抗锯齿) ---
    def draw_branch(name, type):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setPen(QPen(color, 1, Qt.DotLine))
        if type == "vline":
            p.drawLine(mid, 0, mid, size)
        elif type == "more":
            p.drawLine(mid, 0, mid, size)
            p.drawLine(mid, mid, size, mid)
        elif type == "end":
            p.drawLine(mid, 0, mid, mid)
            p.drawLine(mid, mid, size, mid)
        p.end()
        pix.save(name)

    draw_branch("vline.png", "vline")
    draw_branch("branch-more.png", "more")
    draw_branch("branch-end.png", "end")

    print(f"Icons generated at center {mid} with color {color_hex}")


if __name__ == "__main__":
    # 建议使用 #000000 (纯黑) 或 #333333 (深灰)
    generate_perfect_icons("#333333")
