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
import sys
from datetime import datetime
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

#==================================================
# 自定义渲染时间
#=================================================
def time_tag_plugin(md):
    # 更新正则：匹配 [time:YYYY-MM-DD HH:mm:ss] 这种持久化后的格式
    # 如果你想同时兼容 [time] 和 [time:...]，可以使用这个正则：
    import re
    TIME_RE = re.compile(r'^\[time(?::(.*?))?\]')

    def tokenize_time(state, silent):
        content = state.src[state.pos:]
        match = TIME_RE.match(content)
        if not match:
            return False

        if not silent:
            # 这里的 match.group(1) 就是冒号后面的时间字符串
            # 如果是老格式 [time]，group(1) 会是 None
            time_str = match.group(1) if match.group(1) else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            token = state.push("time_tag", "", 0)
            token.content = time_str

        state.pos += len(match.group(0))
        return True

    md.inline.ruler.after("emphasis", "time_tag", tokenize_time)

    def render_time(self, tokens, idx, options, env):
        # 保持你之前调好的“醒目”样式
        return f'<span class="time-node">🕒 {tokens[idx].content}</span>'

    md.add_render_rule("time_tag", render_time)

    def render_time(self, tokens, idx, options, env):
        time_str = tokens[idx].content

        # 美观的古朴大方样式
        return f'''<span class="time-node">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align: middle; margin-right: 7px;">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>{time_str}
        </span>'''

    md.add_render_rule("time_tag", render_time)

# ============================================================
# CSS 样式模板
# ============================================================

def get_css_styles(dark_mode: bool = True) -> str:
    """从外部文件加载 CSS 样式（支持开发环境和打包后的环境）"""
    file_name = "style-dark.css" if dark_mode else "style-light.css"

    # 尝试多个可能的路径
    possible_paths = []
    
    # 获取当前 py 文件所在的目录路径（开发环境）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths.append(os.path.join(current_dir, 'css', file_name))
    
    # 打包后的环境（Nuitka 会将文件放在 exe 同级目录）
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件目录
        exe_dir = os.path.dirname(sys.executable)
        possible_paths.append(os.path.join(exe_dir, 'gui', 'func', 'right_bottom_corner', 'css', file_name))
    
    # 尝试每个路径
    for css_path in possible_paths:
        try:
            if os.path.exists(css_path):
                with open(css_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            print(f"Warning: Failed to load CSS from {css_path}: {e}")
            continue
    
    # 如果所有路径都失败，打印错误并返回基础 fallback 样式
    print(f"Error: Could not load CSS file {file_name} from any location")
    return "body { background-color: #222; color: #fff; }"

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

// ===== 图片点击放大功能 =====
function initImageZoom() {
    // 为所有图片添加点击事件
    const images = document.querySelectorAll('.markdown-body img');
    images.forEach(function(img) {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', function(e) {
            e.preventDefault();
            showImageModal(this.src);
        });
    });
}

function showImageModal(src) {
    // 创建弹框
    const modal = document.createElement('div');
    modal.id = 'image-modal';
    modal.innerHTML = `
        <div class="modal-overlay" onclick="closeImageModal()"></div>
        <div class="modal-content">
            <span class="modal-close" onclick="closeImageModal()">&times;</span>
            <img src="${src}" alt="大图">
        </div>
    `;
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
}

function closeImageModal() {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.remove();
        document.body.style.overflow = '';
    }
}

// ESC 键关闭弹框
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeImageModal();
    }
});

// ===== 页面加载完成后渲染 =====
document.addEventListener("DOMContentLoaded", function() {
    console.log('DOMContentLoaded - starting render');
    // 延迟执行，确保外部脚本已加载
    setTimeout(function() {
        renderMath();
        renderMermaid();
        initImageZoom();
    }, 500);
});

// ===== 多次尝试渲染（用于动态加载的内容）=====
function tryRender(attempts) {
    if (attempts <= 0) return;
    setTimeout(function() {
        renderMath();
        renderMermaid();
        initImageZoom();
        tryRender(attempts - 1);
    }, 1000);
}

// 立即开始尝试渲染
tryRender(3);
'''


def setup_callout_plugin(md):
    """
    不需要额外安装插件，直接拦截原生 blockquote 的渲染
    支持 Obsidian 风格的 callout: > [!NOTE], > [!TIP], > [!WARNING], > [!IMPORTANT], > [!CAUTION]
    """

    # Callout 类型到标题的映射
    CALLOUT_TITLES = {
        'note': 'Note',
        'tip': 'Tip',
        'warning': 'Warning',
        'important': 'Important',
        'caution': 'Caution',
    }

    def custom_blockquote_open(self, tokens, idx, options, env):
        # 获取引用块内部的第一行内容
        content = tokens[idx + 2].content if (idx + 2) < len(tokens) else ""

        # 匹配 Obsidian 语法: > [!NOTE]
        import re
        match = re.match(r'^\[!(.*?)\]', content)

        if match:
            callout_type = match.group(1).lower()
            # 标记这个 blockquote 是一个 callout，方便后面处理
            tokens[idx].info = "is_callout"
            tokens[idx].meta = {"callout_type": callout_type}
            
            # 获取标题，默认为类型名首字母大写
            title = CALLOUT_TITLES.get(callout_type, callout_type.capitalize())
            
            # 移除内容中的 [!type] 标记
            content = re.sub(r'^\[!(.*?)\]\s*', '', content)
            tokens[idx + 2].content = content
            
            return f'<div class="admonition callout {callout_type}" data-callout="{callout_type}"><div class="callout-title">{title}</div>'

        return '<blockquote>'

    def custom_blockquote_close(self, tokens, idx, options, env):
        if tokens[idx].info == "is_callout":
            return '</div>'
        return '</blockquote>'

    # 覆盖原生的 blockquote 渲染规则
    md.add_render_rule("blockquote_open", custom_blockquote_open)
    md.add_render_rule("blockquote_close", custom_blockquote_close)

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
    md_parser.use(time_tag_plugin)        # <--- 新增这一行：启用时间标签插件
    md_parser.use(setup_callout_plugin)   # 自定义 callout
    
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
