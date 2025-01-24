import os
import shutil
import re

current_dir = os.getcwd()
files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]

for filename in files:
    # 检查文件名中是否包含@
    match = re.search(r'@([a-zA-Z]+)', filename)
    if match:
        folder_name = match.group(1)
    else:
        # 取前10个字符，并去除可能的空格
        folder_name = filename[:10].strip()
    
    # 创建目标文件夹路径
    dest_dir = os.path.join(current_dir, folder_name)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # 移动文件
    src_path = os.path.join(current_dir, filename)
    dest_path = os.path.join(dest_dir, filename)
    try:
        shutil.move(src_path, dest_path)
        print(f"Moved '{filename}' to '{folder_name}'")
    except Exception as e:
        print(f"Error moving '{filename}': {e}")