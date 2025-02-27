import os
import json
import subprocess
import argparse
from typing import List


def load_passwords(config_path):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            passwords = json.load(f)
            return passwords if isinstance(passwords, list) else []
    except Exception:
        return []


def find_archives(target_dir):
    archives = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            lower = f.lower()
            if lower.endswith((".7z", ".zip", ".7z.001")):
                archives.append(os.path.join(root, f))
    return archives


def parse_passwords(args):
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 如果用户未指定--config，则使用脚本目录下的默认路径
    default_config = os.path.join(script_dir, "config", "passwords.json")
    config_path = (
        args.config if args.config != "config/passwords.json" else default_config
    )
    # 加载配置（支持绝对路径或相对路径）
    if os.path.exists(config_path):
        config_pwds = load_passwords(config_path)
    else:
        print(f"Warning: Config file not found at {config_path}")
        config_pwds = []

    password_list = []
    cli_pwds = args.passwords.copy()
    seen = set()
    for pwd in config_pwds + cli_pwds:
        if pwd not in seen:
            seen.add(pwd)
            password_list.append(pwd)
    print(f"Using passwords: {password_list}")

    return password_list


def get_volume_files(file_path: str) -> List[str]:
    """获取分卷文件组"""
    if not file_path.lower().endswith((".001", ".7z.001")):
        return [file_path]

    directory, filename = os.path.split(file_path)
    name_parts = filename.split(".")
    prefix = (
        ".".join(name_parts[:-1]) + "." if len(name_parts) > 1 else name_parts[0] + "."
    )

    return sorted(
        [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.startswith(prefix)
            and f[len(prefix) :].isdigit()
            and len(f[len(prefix) :]) == 3
        ],
        key=lambda x: int(x.split(".")[-1]),
    )


def remove_archive_files(archive_path: str) -> bool:
    """删除压缩文件及其分卷"""
    try:
        volumes = get_volume_files(archive_path)
        for vol in volumes:
            os.remove(vol)
        return True
    except Exception as error:
        print(f"! Cleanup failed [{os.path.basename(archive_path)}]: {error}")
        return False


def extract(file_path, passwords, sevenz, output_dir):
    base_name = os.path.basename(file_path)
    output_path = os.path.join(output_dir, base_name.split(".")[0])

    # 尝试空密码
    try:
        subprocess.run(
            [sevenz, "x", "-y", f"-o{output_path}", file_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        print(f"✓ {base_name:50} [No Password]")
        os.remove(file_path)  # 新增：解压成功后删除源文件
        return True
    except subprocess.CalledProcessError:
        pass
    except Exception as e:  # 捕获删除异常
        print(f"! {base_name:50} [Delete Failed: {str(e)}]")

    # 尝试其他密码
    for idx, pwd in enumerate(passwords, 1):
        try:
            subprocess.run(
                [sevenz, "x", f"-p{pwd}", "-y", f"-o{output_path}", file_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
            print(f"✓ {base_name:50} [P{idx}]")
            # os.remove(file_path)
            remove_archive_files(file_path)
            return True
        except subprocess.CalledProcessError:
            continue
        except Exception as e:  # 捕获删除异常
            print(f"! {base_name:50} [Delete Failed: {str(e)}]")
            return False  # 删除失败视为整体失败

    print(f"✗ {base_name:50} [Failed]")
    return False


def main():
    parser = argparse.ArgumentParser("7z Batch Extractor")
    parser.add_argument("target", help="Target directory containing archives")
    parser.add_argument(
        "-c", "--config", default="config/passwords.json", help="Password config file"
    )
    parser.add_argument(
        "-p",
        "--passwords",
        nargs="+",
        default=[],
        help="Passwords to try (@index for config entries)",
    )
    parser.add_argument(
        "-7", "--7z", default="7z.exe", dest="sevenz", help="7z executable path"
    )
    parser.add_argument("-o", "--output", default=".", help="Output directory")

    args = parser.parse_args()

    if not os.path.isdir(args.target):
        print("Error: Target directory not found")
        exit(1)

    passwords = parse_passwords(args)
    archives = find_archives(args.target)

    if not archives:
        print("No archives found")
        return

    os.makedirs(args.output, exist_ok=True)

    success = 0
    for arch in archives:
        success += extract(arch, passwords, args.sevenz, args.output)

    print(f"\nResults: {success} success / {len(archives)} total")


if __name__ == "__main__":
    # python un7z.py .
    main()
