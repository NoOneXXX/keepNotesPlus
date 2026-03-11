import os
import re
import base64
import time

from PySide6.QtWidgets import QTextEdit, QMenu, QMessageBox, QFileDialog, QApplication
from PySide6.QtGui import QImage, QClipboard, QContextMenuEvent, QAction, QTextCharFormat, QFont, QCursor, QIcon, \
    QKeySequence
from PySide6.QtCore import QMimeData, QBuffer, QByteArray, QUrl
from PySide6.QtPrintSupport import QPrinter
from gui.func.utils import logger
''''
富文本类设置
'''
class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.html_file_path = None  # 必须外部设置
        self._cleaning_base64 = False

    def insertFromMimeData(self, source: QMimeData):
        # 情况 1：如果剪贴板中包含图片数据（例如截图）
        if source.hasImage():
            image = source.imageData()
            if isinstance(image, QImage):
                if not self.html_file_path:
                    logger.info("请先设置 html_file_path")
                    return

                # 获取 HTML 文件所在目录，用于保存粘贴的图片
                html_dir = os.path.dirname(self.html_file_path)
                logger.info(f'这个保存的html_dir地址是啥：{html_dir}')
                # 生成一个唯一的图片文件名
                img_name = f"pasted_img_{int(time.time() * 1000)}.png"
                img_path = os.path.join(html_dir, img_name)

                # 保存图片到文件
                image.save(img_path)

                # 使用相对路径将图片插入到富文本框中
                self.textCursor().insertHtml(f'<img src="{img_name}">')

        # 情况 2：如果是拖拽或复制的文件（URL），例如拖拽一个本地图片进来
        elif source.hasUrls():
            for url in source.urls():
                local_path = url.toLocalFile()

                # 仅处理常见图片格式
                if local_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                    if not self.html_file_path:
                        print("请先设置 html_file_path")
                        continue

                    html_dir = os.path.dirname(self.html_file_path)

                    # 生成新的文件名，并拷贝图片到 HTML 文件目录中
                    img_name = f"dragged_img_{len(os.listdir(html_dir))}.png"
                    img_path = os.path.join(html_dir, img_name)

                    from shutil import copyfile
                    copyfile(local_path, img_path)

                    # 插入到 HTML 中使用相对路径
                    self.textCursor().insertHtml(f'<img src="{img_name}">')
                else:
                    # 如果不是图片，默认插入路径字符串
                    self.textCursor().insertText(local_path)

        # 情况 3：默认处理，比如复制粘贴文本
        else:
            super().insertFromMimeData(source)

    def clean_base64_images(self):
        if self._cleaning_base64:
            return
        self._cleaning_base64 = True

        try:
            if not self.html_file_path:
                return
            html = self.toHtml()
            html_dir = os.path.dirname(self.html_file_path)
            pattern = re.compile(
                r'<img[^>]+src="data:image/(?P<ext>png|jpg|jpeg);base64,(?P<data>[A-Za-z0-9+/=]{100,})"'
            )
            counter = 0

            def repl(match):
                nonlocal counter
                ext = match.group("ext")
                data = match.group("data")

                filename = f"pasted_img_{counter}.{ext}"
                file_path = os.path.join(html_dir, filename)

                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(data))

                counter += 1
                return f'<img src="{filename}"'

            new_html = pattern.sub(repl, html)

            #  关键：避免 setHtml 再次触发 clean_base64_images
            if new_html != html:
                self.blockSignals(True)
                self.setHtml(new_html)
                self.blockSignals(False)

        finally:
            self._cleaning_base64 = False

    '''右键点击事件'''
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu()

        #  设置更美观的样式
        menu.setStyleSheet("""
                    QMenu {
                        background-color: #ffffff;
                        border: 1px solid #dcdcdc;
                        border-radius: 8px;
                        padding: 4px;
                        font-size: 14px;
                        font-family: 'Microsoft YaHei', 'Arial', sans-serif;
                    }
                    QMenu::item {
                        padding: 6px 24px 6px 8px;
                        border-radius: 4px;
                        color: #333333;
                    }
                    QMenu::item:selected {
                        background-color: #e6f7ff;
                        color: #1890ff;
                    }
                    QMenu::icon {
                        padding-left: 0px;
                        margin-left: 0px;
                    }
                    QMenu::separator {
                        height: 1px;
                        background: #f0f0f0;
                        margin: 4px 0px;
                    }
                """)

        # 复制功能
        copy_action = QAction(QIcon(":images/document-copy.png"), "复制", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy)
        # 只有在有选中内容时才启用复制
        copy_action.setEnabled(self.textCursor().hasSelection())

        # 粘贴功能
        paste_action = QAction(QIcon(":images/clipboard-paste-document-text.png"), "粘贴", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.paste)
        # 检查剪贴板是否有内容
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(clipboard.mimeData().hasText() or clipboard.mimeData().hasImage() or clipboard.mimeData().hasHtml())

        # 导出PDF功能
        export_pdf_action = QAction(QIcon(":images/question.png"), "导出PDF", self)
        export_pdf_action.triggered.connect(self.export_to_pdf)

        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(export_pdf_action)

        menu.exec(QCursor.pos())

    def export_to_pdf(self):
        """导出当前内容为PDF文件"""
        # 获取默认文件名
        default_filename = "导出文档.pdf"
        if self.html_file_path:
            default_filename = os.path.splitext(os.path.basename(self.html_file_path))[0] + ".pdf"

        # 弹出保存文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出PDF",
            default_filename,
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        try:
            # 创建打印机对象，设置为PDF格式
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)

            # 设置页面大小为A4
            printer.setPageSize(QPrinter.A4)

            # 打印文档到PDF
            self.document().print_(printer)

            logger.info(f"PDF导出成功: {file_path}")
            QMessageBox.information(self, "导出成功", f"PDF文件已保存到:\n{file_path}")
        except Exception as e:
            logger.error(f"PDF导出失败: {str(e)}")
            QMessageBox.critical(self, "导出失败", f"导出PDF时出错:\n{str(e)}")

    '''给字体加粗'''
    def toggle_bold(self):
        """Toggle bold formatting for selected text."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()
        weight = QFont.Bold if not cursor.charFormat().font().bold() else QFont.Normal
        fmt.setFontWeight(weight)
        cursor.mergeCharFormat(fmt)
        self.setTextCursor(cursor)