import sys
import os
import tempfile
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from markdown_it import MarkdownIt


class MarkdownEditor(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("在此输入 Markdown...")
        layout.addWidget(self.editor)

        self.preview = QWebEngineView()
        layout.addWidget(self.preview)

        render_btn = QPushButton("渲染 Markdown")
        render_btn.clicked.connect(self.render_markdown)
        layout.addWidget(render_btn)

        save_btn = QPushButton("保存为 .md")
        save_btn.clicked.connect(self.save_markdown)
        layout.addWidget(save_btn)
        
        # 初始化 markdown-it-py 解析器
        self.md_parser = MarkdownIt('commonmark', {
            'html': True,
            'linkify': True,
            'typographer': True,
        })
        self.md_parser.enable('table')
        self.md_parser.enable('strikethrough')

    def render_markdown(self):
        md_text = self.editor.toPlainText()
        html_body = self.md_parser.render(md_text)
        full_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; background-color: #f9f9f9; }}
                pre, code {{ background-color: #eee; padding: 6px; border-radius: 4px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ccc; padding: 8px; }}
            </style>
        </head>
        <body>{html_body}</body>
        </html>
        """
        tmp_file = os.path.join(tempfile.gettempdir(), "md_preview.html")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write(full_html)
        self.preview.load(QUrl.fromLocalFile(tmp_file))

    def save_markdown(self):
        content = self.editor.toPlainText()
        path, _ = QFileDialog.getSaveFileName(self, "保存 Markdown", filter="Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown 编辑器 Demo (markdown-it-py)")
        self.setGeometry(200, 150, 900, 600)
        self.setCentralWidget(MarkdownEditor())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
