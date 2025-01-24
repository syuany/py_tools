# [file name]: appendsuffix.py
import os
import argparse
import sys

def add_trailing_suffix(directory, suffix, recursive=False):
    """在完整文件名（含扩展名）后追加后缀"""
    for root, _, files in os.walk(directory):
        if not recursive and root != directory:
            continue
            
        for filename in files:
            # 直接在整个文件名后追加后缀
            new_name = f"{filename}{suffix}"
            src = os.path.join(root, filename)
            dst = os.path.join(root, new_name)

            # 跳过已存在目标文件的情况
            if os.path.exists(dst):
                print(f"Skipped: {filename} (target exists)")
                continue
                
            try:
                os.rename(src, dst)
                print(f"Renamed: {filename} -> {new_name}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="在完整文件名后添加后缀（保留原扩展名）",
        epilog="示例：\n  appendsuffix -s \"_backup\"\n  appendsuffix -s \"@v3\" -d \"D:\\Files\" -r",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-s", "--suffix", required=True,
                       help="要追加的后缀（例如：_backup）")
    parser.add_argument("-d", "--directory", default=os.getcwd(),
                       help="目标目录（默认：当前目录）")
    parser.add_argument("-r", "--recursive", action="store_true",
                       help="递归处理子目录")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"错误：目录不存在 - {args.directory}")
        sys.exit(1)

    add_trailing_suffix(
        directory=args.directory,
        suffix=args.suffix,
        recursive=args.recursive
    )