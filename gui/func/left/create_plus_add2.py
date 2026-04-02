import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QRect


def generate_final_fine_tuned_icons():
    app = QApplication.instance() or QApplication(sys.argv)

    # 画布尺寸保持 19x31
    W, H = 19, 31

    # ============================================================
    # 【位置控制中心】 - 你可以根据需要修改下面的数值
    # ============================================================

    # 1. 整体水平偏移量 (增大则整体向右移，缩小则向左移)
    # 当前设为 2，表示在最原始位置基础上向右移动了 2 个像素
    offset_x = 2

    # 2. 整体垂直起始高度 (减小则整体向上移，增大则向下移)
    # 当前设为 11
    offset_y = 10

    # 3. 顶部垂直虚线的横坐标
    # 7 是方框的中心相对位，加上 offset_x 保证虚线永远对齐方框中心
    top_dash_x = 7 + offset_x

    # ============================================================

    # 颜色定义 (保持不变)
    MAGENTA = QColor("#FF00FF")
    WHITE = QColor("#FFFFFF")
    CYAN = QColor("#00E5C0")

    def draw_icon(mode="plus"):
        pix = QPixmap(W, H)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing, False)  # 关闭抗锯齿，保证像素锐利

        # 1. 绘制顶部垂直虚线
        p.setPen(CYAN)
        for y in range(0, offset_y, 2):
            p.drawPoint(top_dash_x, y)

        # 2. 绘制 13x13 大方框
        # bx = 1 (基础边距) + offset_x
        bx, by, bs = 1 + offset_x, offset_y, 13
        p.fillRect(QRect(bx, by, bs, bs), WHITE)
        p.setPen(MAGENTA)
        p.drawRect(bx, by, bs - 1, bs - 1)

        # 3. 内部符号 (cx, cy 是符号的中心点)
        cx, cy = 7 + offset_x, offset_y + 6
        if mode == "plus":
            p.drawLine(cx - 3, cy, cx + 3, cy)  # 横线
            p.drawLine(cx, cy - 3, cx, cy + 3)  # 竖线
        else:
            p.drawLine(cx - 3, cy, cx + 3, cy)  # 减号

        # 4. 右侧水平虚线 (2个点，高度跟随符号中心 cy)
        p.setPen(CYAN)
        # 点的起始位置也随 offset_x 移动
        p.drawPoint(15 + offset_x, cy)
        p.drawPoint(17 + offset_x, cy)

        p.end()
        return pix

    # 保存文件
    draw_icon("plus").save("branch-closed.png")
    draw_icon("minus").save("branch-open.png")

    print(f"图标已生成！当前参数：水平右移 {offset_x}px, 垂直高度 y={offset_y}")


if __name__ == "__main__":
    generate_final_fine_tuned_icons()