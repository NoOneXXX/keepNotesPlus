import os
import sys
import subprocess

AUTHOR = 'Echo'
VERSION = '1.0.0'
app_name = 'KeepnotePlus'

# 获取项目根目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 确保 pdfjs/pdfs 目录存在
pdfs_dir = os.path.join(base_dir, "pdfjs", "pdfs")
os.makedirs(pdfs_dir, exist_ok=True)
# 创建 .gitkeep 文件确保目录不为空
gitkeep_path = os.path.join(pdfs_dir, ".gitkeep")
if not os.path.exists(gitkeep_path):
    with open(gitkeep_path, "w") as f:
        f.write("")

# 构建命令参数列表
# 使用 python -m nuitka 方式调用，确保使用正确的环境
cmd_args = [
    sys.executable,
    "-m",
    "nuitka",
    "--standalone",
    "--mingw64",
    "--enable-plugin=pyside6",
    "--windows-disable-console",
    "--windows-icon-from-ico=gui/images/icon/keepnotesPlus.ico",
    "--output-dir=out",
    f"--windows-company-name={AUTHOR}",
    f"--windows-product-name={app_name}",
    f"--windows-product-version={VERSION}",
]

# 包含 QSS 样式文件
qss_dir = os.path.join(base_dir, "gui", "ui", "qss")
if os.path.exists(qss_dir):
    for filename in os.listdir(qss_dir):
        if filename.endswith('.qss'):
            source_path = os.path.join(qss_dir, filename).replace('\\', '/')
            cmd_args.append(f"--include-data-files={source_path}=gui/ui/qss/{filename}")

# 包含 JS 资源文件（KaTeX 和 Mermaid）
js_dir = os.path.join(base_dir, "gui", "ui", "js")
if os.path.exists(js_dir):
    for root, dirs, files in os.walk(js_dir):
        for filename in files:
            if filename.endswith(('.js', '.css')):
                source_path = os.path.join(root, filename).replace('\\', '/')
                # 计算相对路径
                rel_path = os.path.relpath(source_path, base_dir).replace('\\', '/')
                cmd_args.append(f"--include-data-files={source_path}={rel_path}")

# 包含 pdfjs 目录（PDF预览功能需要）
pdfjs_dir = os.path.join(base_dir, "pdfjs")
if os.path.exists(pdfjs_dir):
    # 包含整个 pdfjs 目录
    cmd_args.append(f"--include-data-dir={pdfjs_dir.replace(chr(92), '/')}=pdfjs")

# 包含 pygments 库（语法高亮需要）
cmd_args.append("--include-package=pygments")

cmd_args.append("--follow-import-to=gui")
cmd_args.append("keepNotesPlus.py")
cmd_args.append("--lto=no")

# 打印命令
print("执行命令:")
print(" ".join(cmd_args))
print()

# 执行打包
result = subprocess.run(cmd_args, cwd=base_dir)
sys.exit(result.returncode)
