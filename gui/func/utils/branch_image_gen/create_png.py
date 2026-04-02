import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QPolygon
from PySide6.QtCore import Qt, QPoint

def generate_tree_icons(color_hex="#555555", size=20, vline_height=None):
    app = QApplication.instance() or QApplication(sys.argv)
    color = QColor(color_hex)
    mid = size // 2
    # vline 的高度，默认是 size 的3倍（更长）
    vline_h = vline_height if vline_height else size * 3
    
    # 获取输出目录路径：gui/images/branch/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.normpath(os.path.join(current_dir, "../../../images/branch"))
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # Helper to setup painter
    def get_painter(pix):
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        # 使用自定义点状线：1像素实线 + 2像素空白，形成明显的点状效果
        pen = QPen(color, 2)
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([1, 2])  # 1像素点，2像素间隔
        p.setPen(pen)
        return p

    # 1. vline.png (Vertical Line) - 增加高度
    vline = QPixmap(size, vline_h)
    vline.fill(Qt.transparent)
    painter = get_painter(vline)
    painter.drawLine(mid, 0, mid, vline_h)
    painter.end()
    vline.save(os.path.join(output_dir, "vline.png"))

    # 2. branch-more.png (T-shape) - 竖线与vline对齐，横线位置调整
    branch_width = size * 2  # 宽度40像素
    more = QPixmap(branch_width, vline_h)
    more.fill(Qt.transparent)
    painter = get_painter(more)
    
    # 竖线位置调整：vline的竖线在mid=10，branch的竖线需要往右移动才能对齐
    # 增加vline_offset值可以让竖线往右移动，与vline.png的竖线对齐
    vline_offset = 11  # 竖线向右偏移2像素，与vline对齐
    painter.drawLine(mid + vline_offset, 0, mid + vline_offset, vline_h)  # 竖线（全高）
    
    # 横线位置调整：增加hline_offset值可以让横线往下移动，与右边文件图标对齐
    hline_offset = 15  # 横线向下偏移2像素，与文件图标对齐
    painter.drawLine(mid + vline_offset, mid + hline_offset, branch_width - 2, mid + hline_offset)  # 横线
    painter.end()
    more.save(os.path.join(output_dir, "branch-more.png"))

    # 3. branch-end.png (L-shape) - 独立参数配置，可单独调试
    # branch-end 图片宽度设置：控制整个图片的宽度
    end_width = size * 2  # 宽度40像素，可独立调整
    
    end = QPixmap(end_width, vline_h)
    end.fill(Qt.transparent)
    painter = get_painter(end)
    
    # ========== branch-end 竖线位置调整参数 ==========
    # end_vline_offset: 控制竖线左右位置
    # 增大数值 → 竖线向右移动
    # 减小数值 → 竖线向左移动
    end_vline_offset = 11  # 竖线向右偏移11像素
    
    # ========== branch-end 横线位置调整参数 ==========
    # end_hline_offset: 控制横线上下位置
    # 增大数值 → 横线向下移动
    # 减小数值 → 横线向上移动
    end_hline_offset = 25  # 横线向下偏移15像素
    
    # ========== branch-end 横线长度调整参数 ==========
    # end_hline_length: 控制横线终点位置（横线长度）
    # 增大数值 → 横线变长（向右延伸更多）
    # 减小数值 → 横线变短
    # 当前值 end_width - 2 表示横线距离右边缘2像素处结束
    end_hline_length = end_width - 1  # 横线长度：从竖线位置延伸到此处
    
    # 绘制竖线：从顶部延伸到横线位置
    painter.drawLine(
        mid + end_vline_offset, 0,  # 起点：顶部，x坐标 = mid + 偏移量
        mid + end_vline_offset, mid + end_hline_offset  # 终点：横线位置
    )
    
    # 绘制横线：从竖线位置向右延伸
    painter.drawLine(
        mid + end_vline_offset, mid + end_hline_offset,  # 起点：竖线与横线交点
        end_hline_length, mid + end_hline_offset  # 终点：横线长度参数控制的位置
    )
    painter.end()
    end.save(os.path.join(output_dir, "branch-end.png"))


    print(f"Successfully generated: vline, branch-more, branch-end -> {output_dir}")

if __name__ == "__main__":
    generate_tree_icons("#008B8B") # 黑色，与左边图片一致
