import os
import sys

AUTHOR = 'Echo'
VERSION = '1.0.0'
app_name = 'KeepnotePlus'

# 获取项目根目录
base_dir = os.path.dirname(os.path.abspath(__file__))

build_command = "nuitka --standalone --mingw64 --enable-plugin=pyside6 "
build_command += "--windows-disable-console "
build_command += "--windows-icon-from-ico=gui/images/icon/keepnotesPlus.ico --output-dir=out "
build_command += f"--windows-company-name={AUTHOR}  --windows-product-name={app_name} "
build_command += f"--windows-product-version={VERSION} "

# 包含 QSS 样式文件到打包目录中
qss_dir = os.path.join(base_dir, "gui", "ui", "qss")
if os.path.exists(qss_dir):
    for filename in os.listdir(qss_dir):
        if filename.endswith('.qss'):
            source_path = os.path.join(qss_dir, filename).replace('\\', '/')
            # 打包到输出目录的 gui/ui/qss/ 下
            build_command += f'--include-data-files="{source_path}=gui/ui/qss/{filename}" '

build_command += "--follow-import-to=gui "
build_command += "main.py  --lto=no "

print(build_command)
os.system(build_command)  # 打包
