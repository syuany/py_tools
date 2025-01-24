import os

def remove_string_from_filenames(directory, target_str, replace_str):
    """
    遍历指定目录及其子目录，将所有包含指定字符串的文件名中的该字符串替换为另一个字符串，并重命名文件。

    参数:
    directory (str): 要遍历的根目录路径。
    target_str (str): 要从文件名中删除的目标字符串。
    replace_str (str): 用于替换目标字符串的新字符串。
    """
    for root, _, files in os.walk(directory):
        for filename in files:
            if target_str in filename:
                new_name = filename.replace(target_str, replace_str)
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_name)
                
                try:
                    os.rename(old_path, new_path)
                except Exception as e:
                    print(f"重命名失败: {old_path} -> {new_path} 错误: {e}")

if __name__ == "__main__":
    current_dir = '.'
    target_str = input("请输入目标字符串: ")
    replace_str = input("请输入要替换的字符串: ")
    remove_string_from_filenames(current_dir, target_str, replace_str)