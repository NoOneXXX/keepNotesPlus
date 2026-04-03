import os
import shutil
import py7zr

from gui.func.utils.json_utils import JsonEditor


class FolderEncryptor:
    """专门针对文件夹的 7z 加密工具类"""

    @staticmethod
    def encrypt_folder_content(source_path, password, delete_source=True):
        """
        加密文件夹内除 .metadata.json 以外的所有内容，并将加密包存放在该文件夹下
        :param source_path: 源文件夹路径
        :param password: 加密密码
        :param delete_source: 是否在加密后删除源文件（保留 .metadata.json 和 .7z）
        :return: (bool, message)
        """
        if not os.path.isdir(source_path):
            return False, "提供的路径不是有效的文件夹"

        source_path = os.path.abspath(source_path)
        # 定义加密包名称，放在源文件夹内
        archive_name = "encrypted_data.7z"
        output_path = os.path.join(source_path, archive_name)

        # 排除名单
        EXCLUDES = [".metadata.json", archive_name]

        try:
            # 1. 创建加密包
            with py7zr.SevenZipFile(output_path, 'w', password=password, header_encryption=True) as archive:
                # 遍历文件夹下的直接子项
                for item in os.listdir(source_path):
                    if item in EXCLUDES:
                        continue

                    full_item_path = os.path.join(source_path, item)

                    if os.path.isdir(full_item_path):
                        # 如果是子文件夹，递归写入
                        # arcname 为文件夹名，保证解压后结构正确
                        archive.writeall(full_item_path, arcname=item)
                    else:
                        # 如果是文件，直接写入
                        archive.write(full_item_path, arcname=item)

            # 2. 检查生成是否成功
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                return False, "加密包创建失败"


            # 修改文件属性
            editor = JsonEditor()
            # 读取detail_info的信息
            detail_info = editor.read_node_infos(source_path)
            content_type = detail_info['node']['detail_info']['content_type']
            detail_info['node']['detail_info']['content_type'] = 'lock' + content_type
            editor.writeByData(os.path.join(source_path, ".metadata.json"), detail_info)
            return True, f"已加密并清理，保留了 .metadata.json 和 {archive_name}"

        except Exception as e:
            # 出错时尝试移除未完成的压缩包
            if os.path.exists(output_path):
                os.remove(output_path)
            return False, f"加密失败: {str(e)}"


class FolderDecryptor:
    """配套解密工具类"""

    @staticmethod
    def decrypt_in_place(source_path, password):
        """
        在当前文件夹下寻找 encrypted_data.7z 并解压
        :param source_path: 包含加密包的文件夹
        :param password: 密码
        """
        archive_name = "encrypted_data.7z"
        target_7z = os.path.join(source_path, archive_name)

        if not os.path.exists(target_7z):
            return False, f"未在目录下找到 {archive_name}"

        try:
            with py7zr.SevenZipFile(target_7z, mode='r', password=password) as archive:
                # 解压到当前文件夹
                archive.extractall(path=source_path)

            # 可选：解压成功后删除加密包
            # os.remove(target_7z)

            return True, "解密提取完成"
        except (py7zr.exceptions.Bad7zFileError, py7zr.exceptions.CrcError):
            return False, "密码错误"
        except Exception as e:
            return False, str(e)