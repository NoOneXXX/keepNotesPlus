import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QRect


def generate_shifted_up_icons():
    app = QApplication.instance() or QApplication(sys.argv)

    # 画布尺寸：宽15，高25
    W, H = 15, 25

    # 颜色定义
    MAGENTA = QColor("#FF00FF")  # 方框和符号
    WHITE = QColor("#FFFFFF")  # 内部背景
    CYAN = QColor("#00E5C0")  # 顶部虚线

    def draw_pixel_icon(mode="plus"):
        pix = QPixmap(W, H)
        pix.fill(Qt.transparent)
        p = QPainter(pix)

        # 禁用抗锯齿，确保物理像素对齐
        p.setRenderHint(QPainter.Antialiasing, False)

        # 1. 绘制顶部虚线 (中心列 x=7)
        p.setPen(CYAN)
        # 虚线绘制到 y=7
        for y in range(0, 8, 2):
            p.drawPoint(7, y)

        # 2. 定义方框尺寸 (11x11)
        # bx=2 保持左右居中
        # by=8 将整体位置再次向上移动2个像素
        bx, by, bs = 2, 8, 11

        # 填充白色背景
        p.fillRect(QRect(bx, by, bs, bs), WHITE)

        # 3. 绘制 1 像素洋红边框
        p.setPen(MAGENTA)
        p.setBrush(Qt.NoBrush)
        p.drawRect(bx, by, bs - 1, bs - 1)

        # 4. 绘制内部符号 (中心点随方框同步上移2像素)
        # 原 cy=15 -> 现 cy=13
        cx, cy = 7, 13

        p.setPen(MAGENTA)
        if mode == "plus":
            # 十字：长度为 5
            p.drawLine(cx - 2, cy, cx + 2, cy)
            p.drawLine(cx, cy - 2, cx, cy + 2)
        else:
            # 减号
            p.drawLine(cx - 2, cy, cx + 2, cy)

        p.end()
        return pix

    # 执行保存
    draw_icon_plus = draw_pixel_icon("plus")
    draw_icon_plus.save("branch-closed.png")

    draw_icon_minus = draw_pixel_icon("minus")
    draw_icon_minus.save("branch-open.png")

    print("整体上移版已生成：方框起始位置 y=8，内部符号中心 y=13。")


if __name__ == "__main__":
    generate_shifted_up_icons()