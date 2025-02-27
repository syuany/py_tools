import os
import sys
import xxhash
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Manager, Lock

def get_fast_hash(filename):
    """快速哈希（头尾抽样）"""
    hasher = xxhash.xxh64()
    try:
        with open(filename, 'rb') as f:
            # 读取头16KB
            head = f.read(16384)
            hasher.update(head)
            
            # 读文件大小并决定是否读取尾部
            file_size = os.path.getsize(filename)
            if file_size > 32768:  # 超过32KB才读尾部
                f.seek(-16384, os.SEEK_END)
                tail = f.read(16384)
                hasher.update(tail)
                
            return (file_size, hasher.hexdigest())
    except Exception as e:
        print(f"快速哈希失败[{filename}]: {str(e)}")
        return (None, None)

def get_full_hash(filename, expected_size):
    """全文件哈希校验"""
    try:
        # 先验证当前文件大小是否匹配
        actual_size = os.path.getsize(filename)
        if actual_size != expected_size:
            print(f"文件大小变化[{filename}]：{expected_size}=>{actual_size}")
            return None
    except OSError as e:
        print(f"无法获取文件大小[{filename}]: {str(e)}")
        return None
    
    hasher = xxhash.xxh64()
    try:
        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(8192)  # 分块读取避免大文件内存问题
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"全哈希计算失败[{filename}]: {str(e)}")
        return None

def scan_files(current_dir, recursive_mode):
    """智能文件扫描"""
    current_script = os.path.abspath(sys.argv[0])
    file_list = []
    
    # 构建排除列表（防止删除脚本自身）
    exclude_files = {current_script, os.path.abspath(__file__)}
    
    if recursive_mode:
        for root, dirs, files in os.walk(current_dir):
            for f in files:
                path = os.path.join(root, f)
                if path not in exclude_files:
                    file_list.append(path)
    else:
        file_list = [
            os.path.join(current_dir, f)
            for f in os.listdir(current_dir)
            if os.path.isfile(os.path.join(current_dir, f))
            and os.path.abspath(os.path.join(current_dir, f)) not in exclude_files
        ]
    
    return file_list

def process_group(group, global_auto_confirm, total_deleted, total_deleted_lock):
    """安全处理重复文件组"""
    size, _, full_hash, files = group
    current_dir = os.getcwd()
    sorted_files = sorted(files)
    to_keep = sorted_files[0]
    to_delete = sorted_files[1:]
    
    print(f"\n▌重复文件组（{size}字节 | 全哈希:{full_hash[:8]}...）")
    print(f"保留: {os.path.relpath(to_keep, current_dir)}")
    print("待删除:")
    for f in to_delete:
        print(f"  ├ {os.path.relpath(f, current_dir)}")
    print("  └───确认删除？───")
    
    # 用户确认逻辑
    confirm = 'y' if global_auto_confirm.value else input("[Y]确认/N取消/YA全部确认: ").strip().lower() or 'y'
    if confirm == 'ya':
        global_auto_confirm.value = True
        confirm = 'y'
    
    deleted_count = 0
    if confirm == 'y':
        for f in to_delete:
            try:
                os.remove(f)
                print(f"✓ 已删除: {os.path.relpath(f, current_dir)}")
                with total_deleted_lock:
                    total_deleted.value += 1
                    deleted_count += 1
            except Exception as e:
                print(f"✕ 删除失败[{f}]: {str(e)}")
    
    return global_auto_confirm.value

def main():
    # 参数解析
    recursive_mode = '-r' in sys.argv
    auto_confirm = '-y' in sys.argv
    
    # 多进程共享资源
    manager = Manager()
    total_deleted = manager.Value('i', 0)
    total_deleted_lock = manager.Lock()
    auto_confirm_flag = manager.Value('b', auto_confirm)
    
    # 阶段1：快速扫描
    print("🔍 扫描文件中...")
    all_files = scan_files(os.getcwd(), recursive_mode)
    
    # 阶段2：快速哈希分组
    print("⚡ 快速哈希预处理...")
    fast_hash_map = defaultdict(list)
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_fast_hash, f): f for f in all_files}
        for future in futures:
            path = futures[future]
            try:
                file_size, fast_hash = future.result()
                if file_size and fast_hash:
                    fast_hash_map[(file_size, fast_hash)].append(path)
            except Exception as e:
                print(f"处理失败[{path}]: {str(e)}")
    
    # 阶段3：全哈希校验
    print("🔒 全文件哈希校验...")
    final_groups = []
    for (file_size, _), candidates in fast_hash_map.items():
        if len(candidates) < 2:
            continue
        
        # 并行计算全哈希
        full_hash_map = defaultdict(list)
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_full_hash, f, file_size): f for f in candidates}
            for future in futures:
                path = futures[future]
                full_hash = future.result()
                if full_hash:
                    full_hash_map[full_hash].append(path)
        
        # 生成最终分组
        for h, files in full_hash_map.items():
            if len(files) > 1:
                final_groups.append((file_size, None, h, files))
    
    # 阶段4：处理重复文件
    print("\n🚀 发现", len(final_groups), "个重复文件组")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for group in final_groups:
            futures.append(
                executor.submit(
                    process_group,
                    group,
                    auto_confirm_flag,
                    total_deleted,
                    total_deleted_lock
                )
            )
        for future in futures:
            future.result()
    
    print(f"\n✅ 完成！共释放 {total_deleted.value} 个重复文件")

if __name__ == "__main__":
    # 运行示例：python dedup.py -r -y
    main()
