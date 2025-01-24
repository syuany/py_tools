import os
import sys
import xxhash
from collections import defaultdict, deque

# 配置参数
BLOCK_SIZE = 65536       # 匹配硬盘物理块大小
SAMPLE_SIZE = 16384      # 哈希抽样大小（头尾各16KB）
BFS_BATCH_SIZE = 100     # BFS每批处理目录数

def get_physical_order(items):
    """优化机械硬盘顺序：跨平台物理位置排序"""
    try:
        # Linux/Mac：按inode排序
        if sys.platform in ['linux', 'darwin']:
            return sorted(items, key=lambda x: os.stat(x).st_ino)
        
        # Windows：安装pywin32时使用簇号排序
        if sys.platform == 'win32':
            import win32file
            def cluster_key(path):
                drive = os.path.splitdrive(path)[0]
                sectors_p_clu = win32file.GetDiskFreeSpace(drive)[0]
                return os.stat(path).st_ino // sectors_p_clu
            return sorted(items, key=cluster_key)
    except:
        pass
    return sorted(items)  # 默认按文件名排序

def manual_bfs_scan(root_dir, recursive):
    """手动实现的BFS目录遍历"""
    dir_queue = deque([root_dir])
    candidates = []
    current_script = os.path.abspath(sys.argv[0])

    while dir_queue:
        # 批量处理目录减少队列操作
        batch_dirs = []
        for _ in range(min(BFS_BATCH_SIZE, len(dir_queue))):
            if dir_queue:
                batch_dirs.append(dir_queue.popleft())

        for current_dir in get_physical_order(batch_dirs):
            try:
                entries = []
                with os.scandir(current_dir) as it:
                    entries = list(it)  # 先获取全部条目再分类处理
                
                # 物理顺序处理文件和子目录
                files, subdirs = [], []
                for entry in get_physical_order(entries):
                    if entry.is_file():
                        filepath = entry.path
                        if filepath != current_script:
                            candidates.append(filepath)
                    elif entry.is_dir():
                        subdirs.append(entry.path)

                # 广度优先扩展：按物理顺序添加子目录
                if recursive:
                    for d in get_physical_order(subdirs):
                        dir_queue.append(d)

            except PermissionError:
                print(f"警告：无权限访问目录 {current_dir}")
            except Exception as e:
                print(f"扫描错误 {current_dir}: {str(e)}")

    return candidates

def fast_hash(path):
    """快速抽样哈希计算"""
    hasher = xxhash.xxh64()
    try:
        size = os.path.getsize(path)
        with open(path, 'rb', buffering=BLOCK_SIZE) as f:
            # 读取头尾各16KB（小文件全量读取）
            hasher.update(f.read(SAMPLE_SIZE))
            if size > SAMPLE_SIZE * 2:
                f.seek(-SAMPLE_SIZE, 2)
                hasher.update(f.read(SAMPLE_SIZE))
        return hasher.hexdigest()
    except Exception as e:
        print(f"错误[{path}]: {str(e)}")
        return None

def find_duplicates(root_dir, recursive):
    """查找重复文件：返回{(size, hash): [paths]}"""
    size_map = defaultdict(list)
    
    # 使用手动BFS扫描文件
    print("扫描文件中...")
    all_files = manual_bfs_scan(root_dir, recursive)
    
    # 物理顺序处理文件减少磁头移动
    for path in get_physical_order(all_files):
        try:
            size = os.path.getsize(path)
            if size > 0:  # 忽略空文件
                size_map[size].append(path)
        except:
            continue

    # 对可能重复的文件计算哈希
    hash_map = defaultdict(list)
    for size, paths in size_map.items():
        if len(paths) > 1:
            for path in paths:
                if h := fast_hash(path):
                    hash_map[(size, h)].append(path)
    
    return {k:v for k,v in hash_map.items() if len(v)>1}

def main():
    # 参数解析
    recursive = '-r' in sys.argv
    auto_confirm = '-y' in sys.argv
    total_deleted = 0

    duplicates = find_duplicates(os.getcwd(), recursive)
    
    # 处理每个重复组
    for (size, hash_val), paths in duplicates.items():
        # 按路径排序，保留第一个
        sorted_paths = get_physical_order(paths)
        keep, to_delete = sorted_paths[0], sorted_paths[1:]
        
        print(f"\n▶ 发现 {len(paths)} 个重复文件（{size//1024}KB | {hash_val}）")
        print(f"保留: {os.path.relpath(keep, os.getcwd())}")
        print("将删除:")
        for p in to_delete:
            print(f"  {os.path.relpath(p, os.getcwd())}")

        # 确认逻辑（默认回车确认）
        confirm = 'y' if auto_confirm else input("\n确认删除？([y]/n): ").strip().lower() or 'y'

        if confirm == 'y':
            for path in to_delete:
                try:
                    os.remove(path)
                    total_deleted += 1
                    print(f"已删除: {os.path.basename(path)}")
                except Exception as e:
                    print(f"删除失败: {str(e)}")

    print(f"\n操作完成，共删除 {total_deleted} 个重复文件")

if __name__ == "__main__":
    # 使用示例: 
    # python dedup_bfs.py       # 当前目录
    # python dedup_bfs.py -r -y # 递归+自动确认
    main()