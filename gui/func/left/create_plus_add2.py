import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect


def generate_perfect_icons(size=15):
    app = QApplication.instance() or QApplication(sys.argv)

    # --- 推荐的高级配色方案 ---
    main_color = QColor("#FF00FF")  # 边框和符号：深炭灰（清晰、有力）
    bg_color = QColor("#FFFFFF")  # 方框填充：纯白（保证加号对比度最高）
    line_color = QColor("#00E5C0")

    mid = size // 2
    box_size = 8
    offset = box_size // 2

    def draw_box(painter):
        painter.setRenderHint(QPainter.Antialiasing, False)
        # 使用 main_color 画边框，bg_color 填充
        painter.setPen(QPen(main_color, 1, Qt.SolidLine))
        painter.setBrush(bg_color)
        rect = QRect(mid - offset, mid - offset, box_size, box_size)
        painter.drawRect(rect)
        return rect

    # --- 1. 生成 branch-closed.png [+] ---
    closed = QPixmap(size, size)
    closed.fill(Qt.transparent)
    p = QPainter(closed)
    draw_box(p)
    p.setPen(QPen(main_color, 1, Qt.SolidLine))
    p.drawLine(mid - 2, mid, mid + 2, mid)
    p.drawLine(mid, mid - 2, mid, mid + 2)
    p.end()
    closed.save("branch-closed.png")

    # --- 2. 生成 branch-open.png [-] ---
    opened = QPixmap(size, size)
    opened.fill(Qt.transparent)
    p = QPainter(opened)
    draw_box(p)
    p.setPen(QPen(main_color, 1, Qt.SolidLine))
    p.drawLine(mid - 2, mid, mid + 2, mid)
    p.end()
    opened.save("branch-open.png")

    # --- 3. 生成 vline, more, end (使用较浅的 line_color) ---
    def draw_branch(name, type):
        pix = QPixmap(size, size)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        # 这里的线色调淡，让层级结构看起来更轻量
        p.setPen(QPen(line_color, 1, Qt.DotLine))
        if type == "more":
            p.drawLine(mid, 0, mid, size)
            p.drawLine(mid, mid, size, mid)
        elif type == "end":
            p.drawLine(mid, 0, mid, mid)
            p.drawLine(mid, mid, size, mid)
        p.end()
        pix.save(name)


    draw_branch("branch-more.png", "more")
    draw_branch("branch-end.png", "end")

    print(f"Elegant icons generated with Main:{main_color.name()} and Line:{line_color.name()}")


if __name__ == "__main__":
    generate_perfect_icons()
