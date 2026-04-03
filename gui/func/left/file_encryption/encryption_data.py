import os
import py7zr


class FileEncryptor:
    """7z 加密工具类"""

    @staticmethod
    def encrypt_file(source_path, password, output_path=None):
        """
        加密单个文件或文件夹
        :param source_path: 源文件路径
        :param password: 加密密码
        :param output_path: 输出路径，默认为 原文件名.7z
        :return: (bool, message)
        """
        if not os.path.exists(source_path):
            return False, "源文件不存在"

        if not output_path:
            output_path = source_path + ".7z"

        try:
            # header_encryption=True 确保不输密码看不见文件名
            with py7zr.SevenZipFile(output_path, 'w', password=password, header_encryption=True) as archive:
                if os.path.isfile(source_path):
                    archive.write(source_path, arcname=os.path.basename(source_path))
                else:
                    # 如果是文件夹，递归写入
                    archive.writeall(source_path, arcname=os.path.basename(source_path))
            return True, output_path
        except Exception as e:
            return False, str(e)


class FileDecryptor:
    """7z 解密工具类"""

    @staticmethod
    def decrypt_file(source_7z, password, target_dir=None):
        """
        解密 7z 文件
        :param source_7z: .7z 文件路径
        :param password: 解密密码
        :param target_dir: 解压目标目录，默认为当前目录
        :return: (bool, message)
        """
        if not os.path.exists(source_7z):
            return False, "压缩包不存在"

        if not target_dir:
            target_dir = os.path.dirname(os.path.abspath(source_7z))

        try:
            with py7zr.SevenZipFile(source_7z, mode='r', password=password) as archive:
                archive.extractall(path=target_dir)
            return True, target_dir
        except py7zr.exceptions.PasswordRequiredError:
            return False, "此文件需要密码"
        except (py7zr.exceptions.Bad7zFileError, py7zr.exceptions.CrcError):
            return False, "密码错误或文件损坏"
        except Exception as e:
            return False, f"解密失败: {str(e)}"