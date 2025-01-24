import os

def rename_files_in_directory(directory):
    """
    递归地重命名指定目录下的所有文件，使其文件名以所在文件夹名作为前缀。
    :param directory: 要处理的根目录路径
    """
    script_path = os.path.abspath(__file__)

    for foldername, _, filenames in os.walk(directory):
        if foldername == directory:
            continue
        for filename in filenames:
            old_file_path = os.path.join(foldername, filename)
            if old_file_path == script_path:
                continue
            try:
                new_filename = f"{os.path.basename(foldername)}-{filename}"
                new_file_path = os.path.join(foldername, new_filename)
                os.rename(old_file_path, new_file_path)
            except Exception as e:
                print(f"Failed to rename {old_file_path}: {str(e)}")

if __name__ == "__main__":
    # 调用函数，从当前目录开始处理
    rename_files_in_directory(os.getcwd())