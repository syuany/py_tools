#!/usr/bin/env python3
import os
import argparse

def rename_files(directory, texts, recursive=False, dry_run=False):
    for root, dirs, files in os.walk(directory) if recursive else [(directory, [], os.listdir(directory))]:
        for name in files + dirs:  # 处理文件和目录
            original_name = name
            new_name = name
            
            # 检查是否有任意text存在
            has_text = any(t in original_name for t in texts)
            if not has_text:
                continue
            
            # 按输入顺序依次删除所有text
            for text in texts:
                new_name = new_name.replace(text, "")
            
            src = os.path.join(root, original_name)
            dst = os.path.join(root, new_name)
            
            if dry_run:
                print(f"[Dry Run] {original_name} → {new_name}")
            else:
                try:
                    os.rename(src, dst)
                    print(f"Renamed: {original_name} → {new_name}")
                except FileExistsError:
                    print(f"Skip: {new_name} already exists")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch remove multiple texts from filenames")
    parser.add_argument("dir", help="Target directory")
    parser.add_argument("texts", nargs="+", help="Texts to remove (ordered)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process recursively")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Simulation mode")
    args = parser.parse_args()
    
    rename_files(args.dir, args.texts, args.recursive, args.dry_run)