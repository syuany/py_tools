import os
import sys
import xxhash
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# SSD优化参数
SSD_PARALLEL_WORKERS = 10      # 并行工作线程数（根据CPU核心数调整）
BLOCK_SIZE = 4096             # 匹配SSD页面大小（通常4KB）
SAMPLE_RATIO = 0.1            # 大文件抽样比例（10%）

def ssd_fast_hash(path):
    """SSD优化哈希算法：智能抽样+并行读取"""
    hasher = xxhash.xxh64()
    try:
        size = os.path.getsize(path)
        # 小文件全量哈希
        if size <= 1024 * 1024:  # <1MB
            with open(path, 'rb', buffering=BLOCK_SIZE) as f:
                hasher.update(f.read())
        else:
            # 大文件随机抽样（间隔跳跃读取）
            sample_size = max(int(size * SAMPLE_RATIO), BLOCK_SIZE)
            step = size // (sample_size // BLOCK_SIZE)
            with open(path, 'rb', buffering=BLOCK_SIZE) as f:
                for _ in range(sample_size // BLOCK_SIZE):
                    f.seek(_ * step % size)
                    hasher.update(f.read(BLOCK_SIZE))
        return hasher.hexdigest()
    except Exception as e:
        print(f"哈希错误[{path}]: {str(e)}")
        return None

def ssd_walk(root_dir, recursive):
    """SSD优化版文件扫描（激进并发）"""
    with ThreadPoolExecutor(max_workers=SSD_PARALLEL_WORKERS) as executor:
        futures = []
        results = []
        
        def scan_dir(current_dir):
            try:
                with os.scandir(current_dir) as it:
                    entries = list(it)
                    dirs = []
                    for entry in entries:
                        if entry.is_file():
                            results.append(entry.path)
                        elif entry.is_dir():
                            dirs.append(entry.path)
                    if recursive:
                        for d in dirs:
                            futures.append(executor.submit(scan_dir, d))
            except Exception as e:
                print(f"扫描错误[{current_dir}]: {str(e)}")

        futures.append(executor.submit(scan_dir, root_dir))
        while futures:
            future = futures.pop()
            future.result()
        
        return [p for p in results if p != os.path.abspath(sys.argv[0])]

def main():
    # 参数解析
    recursive = '-r' in sys.argv
    auto_confirm = '-y' in sys.argv
    total_deleted = 0

    print("[SSD模式] 扫描文件中...")
    all_files = ssd_walk(os.getcwd(), recursive)
    
    # 并行哈希计算
    print(f"计算{len(all_files)}个文件哈希...")
    hash_map = defaultdict(list)
    with ThreadPoolExecutor(max_workers=SSD_PARALLEL_WORKERS) as executor:
        future_to_path = {executor.submit(ssd_fast_hash, p): p for p in all_files}
        for future in future_to_path:
            path = future_to_path[future]
            if h := future.result():
                size = os.path.getsize(path)
                hash_map[(size, h)].append(path)

    # 处理重复组
    for (size, hash_val), paths in hash_map.items():
        if len(paths) > 1:
            # SSD友好删除顺序：并发删除
            keep, to_delete = paths[0], paths[1:]
            print(f"\n🔍 重复组 {len(paths)} 文件 ({size/1024:.1f}KB)")
            print(f"保留: {os.path.basename(keep)}")

            # 自动确认或提示
            if auto_confirm or input(f"删除 {len(to_delete)} 个重复文件？([y]/n): ").lower().strip() in ('', 'y'):
                with ThreadPoolExecutor(max_workers=SSD_PARALLEL_WORKERS) as executor:
                    del_futures = [executor.submit(os.remove, p) for p in to_delete]
                    for i, future in enumerate(del_futures):
                        try:
                            future.result()
                            total_deleted += 1
                            print(f"已删除 {i+1}/{len(to_delete)}", end='\r')
                        except Exception as e:
                            print(f"\n删除失败: {str(e)}")
                print()

    print(f"\n✅ 操作完成，共删除 {total_deleted} 个重复文件")

if __name__ == "__main__":
    # 使用示例:
    # python ssd_dedup.py       # 当前目录
    # python ssd_dedup.py -r -y # 递归+自动确认
    main()