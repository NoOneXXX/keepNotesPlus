"""
Markdown 渲染模块
================

使用 markdown-it-py 实现功能完整的 Markdown 渲染器，支持：
- CommonMark + GFM（表格、任务列表、删除线、自动链接）
- Pygments 代码高亮（Dracula 风格）
- KaTeX 数学公式
- Mermaid 图表
- 现代暗黑/亮色双主题

作者: AI Assistant
"""

import os
import re
from typing import Optional

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from PySide6.QtCore import QUrl


# ============================================================
# Dracula 风格代码高亮格式化器
# ============================================================
class DraculaFormatter(HtmlFormatter):
    """Dracula 风格的代码高亮格式化器"""
    
    def __init__(self, **options):
        # 使用内置的 dracula 风格
        options['style'] = 'dracula'
        super().__init__(**options)


# ============================================================
# 代码高亮函数
# ============================================================
def highlight_code(code: str, lang: str, show_line_numbers: bool = False) -> str:
    """
    使用 Pygments 高亮代码块（Dracula 风格）
    
    Args:
        code: 代码内容
        lang: 语言标识（python, bash, sql 等）
        show_line_numbers: 是否显示行号
    
    Returns:
        高亮后的 HTML 字符串
    """
    # 语言映射表（别名 -> 标准名称）
    LANG_ALIASES = {
        'js': 'javascript',
        'ts': 'typescript',
        'sh': 'bash',
        'shell': 'bash',
        'zsh': 'bash',
        'yml': 'yaml',
        'dockerfile': 'docker',
        'docker': 'docker',
        'make': 'makefile',
        'cmake': 'cmake',
        'conf': 'ini',
        'config': 'ini',
        'env': 'ini',
        'text': 'text',
        'plaintext': 'text',
    }
    
    # 标准化语言名称
    lang_lower = (lang or '').lower().strip()
    lang_standard = LANG_ALIASES.get(lang_lower, lang_lower)
    
    try:
        # 尝试获取 lexer
        try:
            lexer = get_lexer_by_name(lang_standard, stripall=True)
        except ClassNotFound:
            # 尝试原始名称
            try:
                lexer = get_lexer_by_name(lang_lower, stripall=True)
            except ClassNotFound:
                # 尝试猜测
                lexer = guess_lexer(code)
        
        # 创建格式化器
        formatter = DraculaFormatter(
            cssclass=f'code-block language-{lang_standard}',
            nowrap=False,
            linenos='table' if show_line_numbers else False,
            noclasses=False,
        )
        
        # 高亮代码
        highlighted = highlight(code, lexer, formatter)
        
        # 包装成带有语言标签的结构
        lang_display = lang_standard.upper() if lang_standard else 'CODE'
        
        return f'''<div class="code-container" data-lang="{lang_standard}">
    <div class="code-header">
        <span class="code-lang">{lang_display}</span>
        <button class="code-copy-btn" onclick="copyCode(this)" title="复制代码">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        </button>
    </div>
    <div class="code-content">{highlighted}</div>
</div>'''
        
    except Exception as e:
        # 降级处理：返回纯文本
        escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'''<div class="code-container" data-lang="text">
    <div class="code-header">
        <span class="code-lang">TEXT</span>
    </div>
    <div class="code-content"><pre class="code-block"><code>{escaped_code}</code></pre></div>
</div>'''


# ============================================================
# 自定义 Fence 渲染规则
# ============================================================
def render_fence(self, tokens, idx, options, env):
    """自定义 fence 渲染规则，支持代码高亮和 Mermaid"""
    token = tokens[idx]
    lang = token.info.strip() if token.info else ''
    code = token.content
    
    # 检查是否是 Mermaid 图表
    if lang.lower() == 'mermaid':
        return f'''<div class="mermaid-container">
    <div class="mermaid">{code}</div>
</div>'''
    
    # 普通代码块，使用 Pygments 高亮
    return highlight_code(code, lang)


# ============================================================
# CSS 样式模板
# ============================================================
def get_css_styles(dark_mode: bool = True) -> str:
    """
    获取 CSS 样式
    
    Args:
        dark_mode: 是否使用暗黑主题
    
    Returns:
        CSS 样式字符串
    """
    if dark_mode:
        # 现代柔和暗黑主题（类似 GitHub Dark / VS Code Dark+）
        return '''
/* ===== 基础变量 ===== */
:root {
    --bg-primary: #1a1d23;
    --bg-secondary: #22262d;
    --bg-tertiary: #2d333b;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --accent-primary: #58a6ff;
    --accent-secondary: #79c0ff;
    --accent-success: #3fb950;
    --accent-warning: #d29922;
    --accent-error: #f85149;
    --border-color: #373e47;
    --code-bg: #22262d;
    --code-header-bg: #2d333b;
    --shadow-color: rgba(0, 0, 0, 0.3);
}

/* ===== 基础样式 ===== */
html {
    scroll-behavior: smooth;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
    font-size: 16px;
    line-height: 1.8;
    color: var(--text-primary);
    background: var(--bg-primary);
    margin: 0;
    padding: 0;
}

/* ===== 容器 ===== */
.markdown-body {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 32px;
}

@media (max-width: 768px) {
    .markdown-body {
        padding: 24px 16px;
        font-size: 15px;
    }
}

/* ===== 标题样式 ===== */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.4;
    color: var(--text-primary);
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    letter-spacing: -0.02em;
}

h1 {
    font-size: 2em;
    margin-top: 0;
    padding-bottom: 0.3em;
    border-bottom: 1px solid var(--border-color);
    font-weight: 700;
    color: #3a5a7c;
}

h2 {
    font-size: 1.5em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid var(--border-color);
    color: #4a6a8a;
}

h3 {
    font-size: 1.25em;
    color: #5a7a9a;
}

h4 {
    font-size: 1em;
    color: var(--text-secondary);
}

h5, h6 {
    font-size: 0.875em;
    color: var(--text-muted);
}

/* ===== 段落 ===== */
p {
    margin: 0.75em 0;
    text-align: justify;
    line-height: 1.8;
}

/* ===== 链接 ===== */
a {
    color: #5b8cb8;
    text-decoration: none;
    transition: all 0.2s ease;
    border-bottom: 1px solid transparent;
}

a:hover {
    color: #4a7aa8;
    border-bottom: 1px solid #4a7aa8;
    text-decoration: none;
}

/* ===== 行内代码 ===== */
code:not(pre code) {
    background: #f0ede8;
    color: #5a5a5a;
    padding: 0.2em 0.5em;
    border-radius: 5px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
    font-size: 0.85em;
    border: 1px solid #e5e1da;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
}

/* ===== 代码块容器 ===== */
.code-container {
    margin: 1.5em 0;
    border-radius: 8px;
    overflow: hidden;
    background: var(--code-bg);
    border: 1px solid var(--border-color);
}

.code-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
    background: var(--code-header-bg);
    border-bottom: 1px solid var(--border-color);
}

.code-lang {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-family: 'SF Mono', monospace;
}

.code-copy-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
}

.code-copy-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
}

.code-content {
    padding: 0;
    overflow-x: auto;
}

/* ===== Pygments 代码块 ===== */
.code-block {
    margin: 0 !important;
    padding: 16px !important;
    background: var(--code-bg) !important;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
    font-size: 14px;
    line-height: 1.6;
    border-radius: 0 !important;
}

.code-block pre {
    margin: 0;
    padding: 0;
    background: transparent;
}

.code-block code {
    background: transparent;
    color: #383a42;
}

/* ===== 引用块 ===== */
blockquote {
    margin: 1.5em 0;
    padding: 16px 20px;
    background: linear-gradient(135deg, #f5f3f0 0%, #faf9f7 100%);
    border-left: 4px solid #c4b7a6;
    border-radius: 0 8px 8px 0;
    color: #6a6a6a;
    font-style: italic;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

blockquote p {
    margin: 0.5em 0;
}

/* ===== 列表 ===== */
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

ul {
    list-style: none;
}

ul > li {
    position: relative;
    padding-left: 8px;
}

ul > li::before {
    content: '•';
    position: absolute;
    left: -1.2em;
    color: #a09080;
    font-weight: bold;
}

ol {
    counter-reset: item;
    list-style: none;
}

ol > li {
    counter-increment: item;
    position: relative;
    padding-left: 8px;
}

ol > li::before {
    content: counter(item);
    position: absolute;
    left: -1.8em;
    width: 1.5em;
    height: 1.5em;
    background: var(--accent-primary);
    color: var(--bg-primary);
    font-size: 12px;
    font-weight: 600;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    top: 2px;
}

li {
    margin: 0.5em 0;
}

/* ===== 任务列表 ===== */
.task-list-item {
    list-style: none;
    margin-left: -2em;
}

.task-list-item input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid var(--border-color);
    border-radius: 4px;
    margin-right: 10px;
    cursor: pointer;
    position: relative;
    transition: all 0.2s ease;
}

.task-list-item input[type="checkbox"]:checked {
    background: var(--accent-success);
    border-color: var(--accent-success);
}

.task-list-item input[type="checkbox"]:checked::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: var(--bg-primary);
    font-size: 12px;
    font-weight: bold;
}

/* ===== 表格 ===== */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    font-size: 0.95em;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px var(--shadow-color);
}

th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background: var(--bg-tertiary);
    font-weight: 600;
    color: var(--text-primary);
}

tr:nth-child(even) td {
    background: var(--bg-secondary);
}

tr:hover td {
    background: var(--bg-tertiary);
}

/* ===== 分隔线 ===== */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    margin: 2em 0;
}

/* ===== 图片 ===== */
img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 1em 0;
    box-shadow: 0 4px 12px var(--shadow-color);
}

/* ===== 删除线 ===== */
del {
    color: var(--text-muted);
    text-decoration: line-through;
}

/* ===== 强调 ===== */
strong {
    color: var(--accent-warning);
    font-weight: 600;
}

em {
    color: var(--accent-secondary);
    font-style: italic;
}

/* ===== 脚注 ===== */
.footnote-ref {
    font-size: 0.8em;
    vertical-align: super;
}

.footnote {
    font-size: 0.9em;
    color: var(--text-secondary);
    border-top: 1px solid var(--border-color);
    padding-top: 1em;
    margin-top: 2em;
}

/* ===== Mermaid 图表 ===== */
.mermaid-container {
    margin: 1.5em 0;
    padding: 20px;
    background: var(--bg-secondary);
    border-radius: 12px;
    overflow-x: auto;
}

.mermaid {
    display: flex;
    justify-content: center;
}

/* ===== KaTeX 数学公式 ===== */
.katex-display {
    margin: 1.5em 0;
    overflow-x: auto;
    padding: 1em 0;
}

.katex {
    font-size: 1.1em;
}

/* ===== 滚动条 ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* ===== 代码高亮 Dracula 风格 ===== */
.code-block .hll { background-color: #44475a }
.code-block .c { color: #6272a4; font-style: italic }
.code-block .err { color: #ff5555 }
.code-block .k { color: #ff79c6 }
.code-block .o { color: #ff79c6 }
.code-block .ch { color: #6272a4; font-style: italic }
.code-block .cm { color: #6272a4; font-style: italic }
.code-block .cp { color: #ff79c6 }
.code-block .cpf { color: #6272a4 }
.code-block .c1 { color: #6272a4; font-style: italic }
.code-block .cs { color: #6272a4; font-style: italic }
.code-block .gd { color: #ff5555 }
.code-block .ge { font-style: italic }
.code-block .gi { color: #50fa7b }
.code-block .gs { font-weight: bold }
.code-block .gu { color: #bd93f9 }
.code-block .kc { color: #ff79c6 }
.code-block .kd { color: #ff79c6 }
.code-block .kn { color: #ff79c6 }
.code-block .kp { color: #ff79c6 }
.code-block .kr { color: #ff79c6 }
.code-block .kt { color: #8be9fd }
.code-block .ld { color: #f1fa8c }
.code-block .m { color: #bd93f9 }
.code-block .s { color: #f1fa8c }
.code-block .na { color: #50fa7b }
.code-block .nb { color: #8be9fd }
.code-block .nc { color: #50fa7b }
.code-block .no { color: #8be9fd }
.code-block .nd { color: #ffb86c }
.code-block .ni { color: #f8f8f2 }
.code-block .ne { color: #50fa7b }
.code-block .nf { color: #50fa7b }
.code-block .nl { color: #8be9fd }
.code-block .nn { color: #f8f8f2 }
.code-block .nt { color: #ff79c6 }
.code-block .nv { color: #8be9fd }
.code-block .ow { color: #ff79c6 }
.code-block .w { color: #f8f8f2 }
.code-block .mb { color: #bd93f9 }
.code-block .mf { color: #bd93f9 }
.code-block .mh { color: #bd93f9 }
.code-block .mi { color: #bd93f9 }
.code-block .mo { color: #bd93f9 }
.code-block .sa { color: #f1fa8c }
.code-block .sb { color: #f1fa8c }
.code-block .sc { color: #f1fa8c }
.code-block .sd { color: #f1fa8c }
.code-block .se { color: #f1fa8c }
.code-block .sh { color: #f1fa8c }
.code-block .si { color: #f1fa8c }
.code-block .sx { color: #f1fa8c }
.code-block .sr { color: #ff5555 }
.code-block .s1 { color: #f1fa8c }
.code-block .ss { color: #f1fa8c }
.code-block .bp { color: #ff79c6 }
.code-block .fm { color: #50fa7b }
.code-block .vc { color: #8be9fd }
.code-block .vg { color: #8be9fd }
.code-block .vi { color: #8be9fd }
.code-block .vm { color: #8be9fd }
.code-block .il { color: #bd93f9 }
'''
    else:
        # 亮色主题
        return '''
/* ===== 基础变量 - 温暖自然风格 ===== */
:root {
    --bg-primary: #faf9f7;
    --bg-secondary: #f5f3f0;
    --bg-tertiary: #ebe8e3;
    --text-primary: #2d2d2d;
    --text-secondary: #5a5a5a;
    --text-muted: #8a8a8a;
    --accent-primary: #5b8cb8;
    --accent-secondary: #4a7aa8;
    --accent-success: #6aa87a;
    --accent-warning: #d4a03c;
    --accent-error: #d4736a;
    --border-color: #e0dcd5;
    --code-bg: #f7f5f2;
    --code-header-bg: #f0ede8;
    --shadow-color: rgba(0, 0, 0, 0.04);
}

/* ===== 基础样式 ===== */
html {
    scroll-behavior: smooth;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
    font-size: 16px;
    line-height: 1.8;
    color: var(--text-primary);
    background: var(--bg-primary);
    margin: 0;
    padding: 0;
}

/* ===== 容器 ===== */
.markdown-body {
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px;
}

@media (max-width: 768px) {
    .markdown-body {
        padding: 24px 16px;
        font-size: 15px;
    }
}

/* ===== 标题样式 ===== */
h1, h2, h3, h4, h5, h6 {
    font-weight: 600;
    line-height: 1.4;
    color: var(--text-primary);
    margin-top: 1.8em;
    margin-bottom: 0.6em;
}

h1 {
    font-size: 2.25em;
    margin-top: 0;
    padding-bottom: 0.4em;
    border-bottom: 2px solid var(--border-color);
    color: var(--accent-primary);
}

h2 {
    font-size: 1.75em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid var(--border-color);
    position: relative;
    padding-left: 16px;
}

h2::before {
    content: '';
    position: absolute;
    left: 0;
    top: 4px;
    bottom: calc(0.3em + 4px);
    width: 4px;
    background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));
    border-radius: 2px;
}

h3 {
    font-size: 1.4em;
    color: var(--accent-secondary);
}

h4 {
    font-size: 1.2em;
    color: var(--accent-success);
}

h5, h6 {
    font-size: 1em;
    color: var(--text-secondary);
}

/* ===== 段落 ===== */
p {
    margin: 1em 0;
    text-align: justify;
}

/* ===== 链接 ===== */
a {
    color: var(--accent-primary);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: all 0.2s ease;
}

a:hover {
    color: var(--accent-secondary);
    border-bottom-color: var(--accent-secondary);
}

/* ===== 行内代码 ===== */
code:not(pre code) {
    background: var(--bg-tertiary);
    color: var(--accent-error);
    padding: 0.2em 0.5em;
    border-radius: 6px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 0.875em;
}

/* ===== 代码块容器 ===== */
.code-container {
    margin: 1.5em 0;
    border-radius: 6px;
    overflow: hidden;
    background: var(--code-bg);
    border: 1px solid var(--border-color);
    box-shadow: 0 2px 4px var(--shadow-color);
}

.code-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
    background: var(--code-header-bg);
    border-bottom: 1px solid var(--border-color);
}

.code-lang {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-family: 'SF Mono', monospace;
}

.code-copy-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
}

.code-copy-btn:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
}

.code-content {
    padding: 0;
    overflow-x: auto;
}

/* ===== Pygments 代码块 - Typora 浅色风格 ===== */
.code-block {
    margin: 0 !important;
    padding: 16px !important;
    background: var(--code-bg) !important;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
    font-size: 14px;
    line-height: 1.6;
    border-radius: 0 !important;
}

.code-block pre {
    margin: 0;
    padding: 0;
    background: transparent;
}

.code-block code {
    background: transparent;
    color: var(--text-primary);
}

/* ===== 浅色代码高亮 - Typora/GitHub 风格 ===== */
.code-block .hll { background-color: #ffeb3b; color: #000; }
.code-block .c { color: #6a737d; font-style: italic }
.code-block .err { color: #cb2431 }
.code-block .k { color: #d73a49; font-weight: 600 }
.code-block .o { color: #24292e }
.code-block .ch { color: #6a737d; font-style: italic }
.code-block .cm { color: #6a737d; font-style: italic }
.code-block .cp { color: #d73a49; font-weight: 600 }
.code-block .cpf { color: #032f62 }
.code-block .c1 { color: #6a737d; font-style: italic }
.code-block .cs { color: #6a737d; font-style: italic }
.code-block .gd { color: #cb2431; background-color: #ffeef0 }
.code-block .ge { font-style: italic }
.code-block .gi { color: #22863a; background-color: #f0fff4 }
.code-block .gs { font-weight: 600 }
.code-block .gu { color: #6f42c1 }
.code-block .kc { color: #005cc5 }
.code-block .kd { color: #d73a49; font-weight: 600 }
.code-block .kn { color: #d73a49 }
.code-block .kp { color: #d73a49 }
.code-block .kr { color: #d73a49; font-weight: 600 }
.code-block .kt { color: #d73a49 }
.code-block .ld { color: #032f62 }
.code-block .m { color: #005cc5 }
.code-block .s { color: #032f62 }
.code-block .na { color: #6f42c1 }
.code-block .nb { color: #005cc5 }
.code-block .nc { color: #6f42c1; font-weight: 600 }
.code-block .no { color: #005cc5 }
.code-block .nd { color: #6f42c1 }
.code-block .ni { color: #005cc5 }
.code-block .ne { color: #cb2431 }
.code-block .nf { color: #6f42c1 }
.code-block .nl { color: #005cc5 }
.code-block .nn { color: #6f42c1 }
.code-block .nt { color: #22863a }
.code-block .nv { color: #e36209 }
.code-block .ow { color: #d73a49 }
.code-block .w { color: #bbbbbb }
.code-block .mb { color: #005cc5 }
.code-block .mf { color: #005cc5 }
.code-block .mh { color: #005cc5 }
.code-block .mi { color: #005cc5 }
.code-block .mo { color: #005cc5 }
.code-block .sa { color: #032f62 }
.code-block .sb { color: #032f62 }
.code-block .sc { color: #032f62 }
.code-block .sd { color: #032f62 }
.code-block .se { color: #032f62 }
.code-block .sh { color: #032f62 }
.code-block .si { color: #032f62 }
.code-block .sx { color: #032f62 }
.code-block .sr { color: #032f62 }
.code-block .s1 { color: #032f62 }
.code-block .ss { color: #005cc5 }
.code-block .bp { color: #d73a49 }
.code-block .fm { color: #6f42c1 }
.code-block .vc { color: #e36209 }
.code-block .vg { color: #e36209 }
.code-block .vi { color: #e36209 }
.code-block .vm { color: #e36209 }
.code-block .il { color: #005cc5 }

/* ===== 引用块 ===== */
blockquote {
    margin: 1.5em 0;
    padding: 16px 20px;
    background: var(--bg-secondary);
    border-left: 4px solid var(--accent-primary);
    border-radius: 0 8px 8px 0;
    color: var(--text-secondary);
    font-style: italic;
}

blockquote p {
    margin: 0.5em 0;
}

/* ===== 列表 ===== */
ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

ul {
    list-style: none;
}

ul > li {
    position: relative;
    padding-left: 8px;
}

ul > li::before {
    content: '•';
    position: absolute;
    left: -1.2em;
    color: var(--accent-primary);
    font-weight: bold;
}

ol {
    counter-reset: item;
    list-style: none;
}

ol > li {
    counter-increment: item;
    position: relative;
    padding-left: 8px;
}

ol > li::before {
    content: counter(item);
    position: absolute;
    left: -1.8em;
    width: 1.5em;
    height: 1.5em;
    background: var(--accent-primary);
    color: white;
    font-size: 12px;
    font-weight: 600;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    top: 2px;
}

li {
    margin: 0.5em 0;
}

/* ===== 任务列表 ===== */
.task-list-item {
    list-style: none;
    margin-left: -2em;
}

.task-list-item input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid var(--border-color);
    border-radius: 4px;
    margin-right: 10px;
    cursor: pointer;
    position: relative;
    transition: all 0.2s ease;
}

.task-list-item input[type="checkbox"]:checked {
    background: var(--accent-success);
    border-color: var(--accent-success);
}

.task-list-item input[type="checkbox"]:checked::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-size: 12px;
    font-weight: bold;
}

/* ===== 表格 ===== */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;
    font-size: 0.95em;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px var(--shadow-color);
}

th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

th {
    background: var(--bg-tertiary);
    font-weight: 600;
    color: var(--text-primary);
}

tr:nth-child(even) td {
    background: var(--bg-secondary);
}

tr:hover td {
    background: var(--bg-tertiary);
}

/* ===== 分隔线 ===== */
hr {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    margin: 2em 0;
}

/* ===== 图片 ===== */
img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 1em 0;
    box-shadow: 0 4px 12px var(--shadow-color);
}

/* ===== 删除线 ===== */
del {
    color: var(--text-muted);
    text-decoration: line-through;
}

/* ===== 强调 ===== */
strong {
    color: var(--accent-warning);
    font-weight: 600;
}

em {
    color: var(--accent-secondary);
    font-style: italic;
}

/* ===== 脚注 ===== */
.footnote-ref {
    font-size: 0.8em;
    vertical-align: super;
}

.footnote {
    font-size: 0.9em;
    color: var(--text-secondary);
    border-top: 1px solid var(--border-color);
    padding-top: 1em;
    margin-top: 2em;
}

/* ===== Mermaid 图表 ===== */
.mermaid-container {
    margin: 1.5em 0;
    padding: 20px;
    background: var(--bg-secondary);
    border-radius: 12px;
    overflow-x: auto;
}

.mermaid {
    display: flex;
    justify-content: center;
}

/* ===== KaTeX 数学公式 ===== */
.katex-display {
    margin: 1.5em 0;
    overflow-x: auto;
    padding: 1em 0;
}

.katex {
    font-size: 1.1em;
}

/* ===== 滚动条 ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* ===== 代码高亮 Atom One Light 优雅风格 ===== */
/* 基础色调：温暖、自然、低饱和度 */
.code-block .hll { background-color: #e5e5e6 }

/* 注释：柔和的橄榄灰 */
.code-block .c { color: #9a9a9a; font-style: italic }
.code-block .ch { color: #9a9a9a; font-style: italic }
.code-block .cm { color: #9a9a9a; font-style: italic }
.code-block .cp { color: #9a9a9a; font-style: italic }
.code-block .cpf { color: #9a9a9a; font-style: italic }
.code-block .c1 { color: #9a9a9a; font-style: italic }
.code-block .cs { color: #9a9a9a; font-style: italic }

/* 错误：柔和的红 */
.code-block .err { color: #e45649 }

/* 关键字：优雅的紫红 */
.code-block .k { color: #a626a4 }
.code-block .kc { color: #a626a4 }
.code-block .kd { color: #a626a4 }
.code-block .kn { color: #a626a4 }
.code-block .kp { color: #a626a4 }
.code-block .kr { color: #a626a4 }
.code-block .kt { color: #a626a4 }

/* 操作符：深灰 */
.code-block .o { color: #383a42 }
.code-block .ow { color: #a626a4 }

/* 删除/插入：柔和的红/绿 */
.code-block .gd { color: #e45649; background-color: #ffeaea }
.code-block .ge { font-style: italic }
.code-block .gi { color: #50a14f; background-color: #e8f5e9 }
.code-block .gs { font-weight: bold }
.code-block .gu { color: #9a9a9a }

/* 字面量/字符串：温暖的橙棕 */
.code-block .ld { color: #c18401 }
.code-block .s { color: #c18401 }
.code-block .sa { color: #c18401 }
.code-block .sb { color: #c18401 }
.code-block .sc { color: #c18401 }
.code-block .sd { color: #c18401 }
.code-block .se { color: #c18401 }
.code-block .sh { color: #c18401 }
.code-block .si { color: #c18401 }
.code-block .sx { color: #c18401 }
.code-block .sr { color: #c18401 }
.code-block .s1 { color: #c18401 }
.code-block .ss { color: #c18401 }

/* 数字：清新的蓝 */
.code-block .m { color: #4078f2 }
.code-block .mb { color: #4078f2 }
.code-block .mf { color: #4078f2 }
.code-block .mh { color: #4078f2 }
.code-block .mi { color: #4078f2 }
.code-block .mo { color: #4078f2 }
.code-block .il { color: #4078f2 }

/* 名称/属性：深蓝 */
.code-block .na { color: #4078f2 }
.code-block .nb { color: #4078f2 }
.code-block .nc { color: #c18401 }
.code-block .no { color: #4078f2 }
.code-block .nd { color: #4078f2 }
.code-block .ni { color: #383a42 }
.code-block .ne { color: #c18401 }
.code-block .nf { color: #4078f2 }
.code-block .nl { color: #383a42 }
.code-block .nn { color: #c18401 }
.code-block .nt { color: #e45649 }
.code-block .nv { color: #e45649 }
.code-block .vc { color: #e45649 }
.code-block .vg { color: #e45649 }
.code-block .vi { color: #e45649 }
.code-block .vm { color: #e45649 }

/* 内置：深蓝 */
.code-block .bp { color: #4078f2 }
.code-block .fm { color: #4078f2 }

/* 空白：深灰 */
.code-block .w { color: #383a42 }
'''


# ============================================================
# JavaScript 脚本
# ============================================================
def get_javascript() -> str:
    """获取必要的 JavaScript 脚本"""
    return '''
// ===== 复制代码功能 =====
// 使用 QWebChannel 与 Python 通信进行复制
var copyHandler = null;
var channelReady = false;

// 初始化 QWebChannel
document.addEventListener("DOMContentLoaded", function() {
    if (typeof qt !== 'undefined' && qt.webChannelTransport) {
        try {
            new QWebChannel(qt.webChannelTransport, function(channel) {
                copyHandler = channel.objects.copyHandler;
                channelReady = true;
                console.log('QWebChannel initialized successfully');
            });
        } catch (e) {
            console.error('QWebChannel initialization failed:', e);
        }
    } else {
        console.log('Qt WebChannel not available');
    }
});

function copyCode(button) {
    const container = button.closest('.code-container');
    if (!container) {
        console.error('Code container not found');
        return;
    }
    // 尝试多种方式获取代码内容
    // 1. 先尝试找 code 标签
    let codeElement = container.querySelector('code');
    // 2. 如果没有 code 标签，尝试找 .code-content 内的内容
    if (!codeElement) {
        const codeContent = container.querySelector('.code-content');
        if (codeContent) {
            codeElement = codeContent;
        }
    }
    // 3. 如果都没有，尝试找 pre 标签
    if (!codeElement) {
        codeElement = container.querySelector('pre');
    }
    if (!codeElement) {
        console.error('Code element not found in container:', container.innerHTML.substring(0, 200));
        return;
    }
    const text = codeElement.textContent;
    
    // 优先使用 QWebChannel 与 Python 通信
    if (channelReady && copyHandler) {
        try {
            // QWebChannel 的 Slot 调用方式
            var result = copyHandler.copyText(text);
            if (result === true || result === undefined) {
                showCopySuccess(button);
            } else {
                console.error('复制失败，尝试备用方案');
                fallbackCopy(text, button);
            }
        } catch (e) {
            console.error('QWebChannel copy failed:', e);
            fallbackCopy(text, button);
        }
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
        // 尝试使用现代 clipboard API
        navigator.clipboard.writeText(text).then(() => {
            showCopySuccess(button);
        }).catch(err => {
            console.error('Clipboard API failed:', err);
            // 降级使用 execCommand
            fallbackCopy(text, button);
        });
    } else {
        // 使用降级方案
        fallbackCopy(text, button);
    }
}

function fallbackCopy(text, button) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    
    try {
        const success = document.execCommand('copy');
        if (success) {
            showCopySuccess(button);
        } else {
            console.error('复制失败');
        }
    } catch (err) {
        console.error('复制失败:', err);
    }
    
    document.body.removeChild(textarea);
}

function showCopySuccess(button) {
    const originalHTML = button.innerHTML;
    button.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    button.style.color = 'var(--accent-success, #3fb950)';
    
    setTimeout(() => {
        button.innerHTML = originalHTML;
        button.style.color = '';
    }, 2000);
}

// ===== KaTeX 自动渲染 =====
function renderMath() {
    if (typeof renderMathInElement !== 'undefined') {
        console.log('Rendering KaTeX...');
        renderMathInElement(document.body, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false},
                {left: '\\[', right: '\\]', display: true},
                {left: '\\(', right: '\\)', display: false}
            ],
            throwOnError: false
        });
        console.log('KaTeX rendering done');
    } else {
        console.log('KaTeX not loaded yet');
    }
}

// ===== Mermaid 渲染 =====
function renderMermaid() {
    if (typeof mermaid !== 'undefined') {
        console.log('Rendering Mermaid...');
        mermaid.initialize({
            startOnLoad: false,
            theme: document.body.classList.contains('dark') ? 'dark' : 'default',
            securityLevel: 'loose'
        });
        // 手动渲染所有 mermaid 图表
        const mermaidElements = document.querySelectorAll('.mermaid');
        console.log('Found', mermaidElements.length, 'mermaid elements');
        if (mermaidElements.length > 0) {
            try {
                mermaid.run({
                    querySelector: '.mermaid'
                });
                console.log('Mermaid rendering done');
            } catch (e) {
                console.error('Mermaid run failed:', e);
                // 降级到 init
                try {
                    mermaid.init(undefined, mermaidElements);
                    console.log('Mermaid init done');
                } catch (e2) {
                    console.error('Mermaid init failed:', e2);
                }
            }
        }
    } else {
        console.log('Mermaid not loaded yet');
    }
}

// ===== 页面加载完成后渲染 =====
document.addEventListener("DOMContentLoaded", function() {
    console.log('DOMContentLoaded - starting render');
    // 延迟执行，确保外部脚本已加载
    setTimeout(function() {
        renderMath();
        renderMermaid();
    }, 500);
});

// ===== 多次尝试渲染（用于动态加载的内容）=====
function tryRender(attempts) {
    if (attempts <= 0) return;
    setTimeout(function() {
        renderMath();
        renderMermaid();
        tryRender(attempts - 1);
    }, 1000);
}

// 立即开始尝试渲染
tryRender(3);
'''


# ============================================================
# 资源路径（本地文件）
# ============================================================
# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# KaTeX 本地路径
KATEX_CSS = os.path.join(PROJECT_ROOT, 'gui', 'ui', 'js', 'katex', 'katex.min.css')
KATEX_JS = os.path.join(PROJECT_ROOT, 'gui', 'ui', 'js', 'katex', 'katex.min.js')
KATEX_AUTO_RENDER = os.path.join(PROJECT_ROOT, 'gui', 'ui', 'js', 'katex', 'auto-render.min.js')
# Mermaid 本地路径
MERMAID_JS = os.path.join(PROJECT_ROOT, 'gui', 'ui', 'js', 'mermaid', 'mermaid.min.js')


# ============================================================
# 主渲染函数
# ============================================================
def render_markdown(md_text: str, dark_mode: bool = True) -> str:
    """
    将 Markdown 文本渲染为完整的 HTML 页面
    
    Args:
        md_text: Markdown 文本内容
        dark_mode: 是否使用暗黑主题（默认 True）
    
    Returns:
        完整的 HTML 字符串（包含 <!DOCTYPE html>）
    
    Features:
        - CommonMark + GFM（表格、任务列表、删除线）
        - Pygments 代码高亮（Dracula 风格）
        - KaTeX 数学公式
        - Mermaid 图表
        - 响应式设计
        - 暗黑/亮色双主题
    """
    # 创建 Markdown 解析器
    md_parser = MarkdownIt('commonmark', {
        'html': True,
        'linkify': True,
        'typographer': True,
    })
    
    # 启用 GFM 特性
    md_parser.enable('table')
    md_parser.enable('strikethrough')
    
    # 添加插件
    md_parser.use(front_matter_plugin)    # YAML 前言
    md_parser.use(footnote_plugin)        # 脚注
    md_parser.use(tasklists_plugin)       # 任务列表
    
    # 自定义 fence 渲染规则
    md_parser.add_render_rule('fence', render_fence)
    
    # 渲染 Markdown 内容
    html_body = md_parser.render(md_text)
    
    # 获取 CSS 样式
    css_styles = get_css_styles(dark_mode)
    
    # 获取 JavaScript
    js_script = get_javascript()
    
    # 主题类名
    theme_class = 'dark' if dark_mode else 'light'
    
    # 使用文件 URL 加载本地资源
    katex_css_url = QUrl.fromLocalFile(KATEX_CSS).toString()
    katex_js_url = QUrl.fromLocalFile(KATEX_JS).toString()
    katex_auto_render_url = QUrl.fromLocalFile(KATEX_AUTO_RENDER).toString()
    mermaid_js_url = QUrl.fromLocalFile(MERMAID_JS).toString()
    
    # 构建完整 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Preview</title>
    
    <!-- KaTeX CSS -->
    <link rel="stylesheet" href="{katex_css_url}">
    
    <style>
{css_styles}
    </style>
</head>
<body class="{theme_class}">
    <article class="markdown-body">
{html_body}
    </article>
    
    <!-- KaTeX JS -->
    <script src="{katex_js_url}"></script>
    <script src="{katex_auto_render_url}"></script>
    
    <!-- Mermaid JS -->
    <script src="{mermaid_js_url}"></script>
    
    <!-- QWebChannel JS -->
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    
    <script>
{js_script}
    </script>
</body>
</html>'''
    
    return html


# ============================================================
# 便捷函数
# ============================================================
def render_markdown_dark(md_text: str) -> str:
    """渲染暗黑主题 Markdown"""
    return render_markdown(md_text, dark_mode=True)


def render_markdown_light(md_text: str) -> str:
    """渲染亮色主题 Markdown"""
    return render_markdown(md_text, dark_mode=False)
