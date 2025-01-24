import os
import subprocess
import argparse

SUPPORTED_FORMATS = {
    '7z': {
        'extension': '7z',
        'volume_support': True,
        'password_support': True
    },
    'zip': {
        'extension': 'zip',
        'volume_support': False,
        'password_support': True
    }
}

def find_compress_targets(target_dir):
    """查找需要压缩的目录"""
    targets = []
    for root, dirs, files in os.walk(target_dir):
        # 检查是否已存在压缩文件
        has_archive = any(f.endswith(('.7z', '.zip')) for f in files)
        if not has_archive:
            targets.append(root)
    return targets

def compress_folder(folder_path, args):
    """执行单目录压缩"""
    folder_name = os.path.basename(folder_path)
    fmt = SUPPORTED_FORMATS[args.format]
    output_file = os.path.join(args.output, f"{folder_name}.{fmt['extension']}")

    # 构建7z命令
    cmd = [
        args.sevenz,
        'a',
        f'-t{args.format}',
        f'-mx{args.compression}',
        output_file,
        folder_path
    ]

    # 添加密码参数
    if args.password:
        cmd.insert(2, f'-p{args.password}')
    
    # 添加分卷参数（仅限7z格式）
    if args.volume and fmt['volume_support']:
        cmd.insert(3, f'-v{args.volume}')
    elif args.volume and not fmt['volume_support']:
        print(f"⚠️ {args.format.upper()}格式不支持分卷压缩，已忽略分卷参数")

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        print(f"✓ 成功压缩：{folder_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 压缩失败：{folder_name} (错误码 {e.returncode})")
        return False

def main():
    parser = argparse.ArgumentParser(description="批量压缩工具（支持7z/zip格式）")
    parser.add_argument("target", help="要压缩的根目录路径")
    parser.add_argument("-7", "--sevenz", default="7z.exe", 
                      help="7-Zip程序路径 (默认: 7z.exe)")
    parser.add_argument("-o", "--output", default="compressed",
                      help="输出目录 (默认: ./compressed)")
    parser.add_argument("-p", "--password", 
                      help="设置压缩密码（支持7z/zip格式）")
    parser.add_argument("-v", "--volume", 
                      help="分卷大小（示例：500m、2G，仅限7z格式）")
    parser.add_argument("-c", "--compression", type=int, default=5,
                      help="压缩级别 1-9 (默认: 5)", choices=range(1,10))
    parser.add_argument("-f", "--format", default="7z", 
                      choices=SUPPORTED_FORMATS.keys(),
                      help="压缩格式 (默认: 7z)")

    args = parser.parse_args()

    # 验证目标目录
    if not os.path.isdir(args.target):
        print("错误：目标目录不存在")
        exit(1)
    
    # 查找需要压缩的目录
    targets = find_compress_targets(args.target)
    if not targets:
        print("没有找到需要压缩的目录")
        return
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 执行压缩操作
    success = 0
    for folder in targets:
        success += compress_folder(folder, args)
    
    print(f"\n压缩完成：成功 {success} 个 / 总计 {len(targets)} 个")

if __name__ == "__main__":
    main()