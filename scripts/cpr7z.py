# -*- coding: utf-8 -*-
import os
import json
import subprocess
import argparse
import shlex

SUPPORTED_FORMATS = {
    '7z': {
        'ext': '7z',
        'vol': True,
        'pwd': True,
        'enc_list': True
    },
    'zip': {
        'ext': 'zip',
        'vol': False,
        'pwd': True,
        'enc_list': False
    }
}

def load_passwords(config):
    try:
        with open(config, 'r', encoding='utf-8') as f:
            return json.load(f) if isinstance(pwds := json.load(f), list) else []
    except Exception as e:
        print(f"Config Error: {str(e)}")
        return []

def get_password(args):
    if not args.password:
        return None
    
    if args.password.startswith('@'):
        try:
            pwds = load_passwords(args.config)
            idx = int(args.password[1:]) - 1
            return pwds[idx] if 0 <= idx < len(pwds) else exit(f"Invalid index: {args.password}")
        except:
            exit(f"Index Error: {args.password}")
    return args.password

def find_targets(root_dir):
    """Improved directory scanning with error handling"""
    try:
        entries = os.scandir(root_dir)
    except FileNotFoundError:
        exit(f"Error: Target directory not found - {root_dir}")
    except PermissionError:
        exit(f"Error: No permission to access directory - {root_dir}")

    targets = []
    for entry in entries:
        if entry.is_dir():
            try:
                # Validate path exists before listing
                if not os.path.exists(entry.path):
                    print(f"Warning: Skipping inaccessible directory - {entry.path}")
                    continue
                    
                # Check for existing archives
                has_archive = any(f.endswith(('.7z', '.zip')) for f in os.listdir(entry.path))
                if not has_archive:
                    targets.append(entry.path)
            except (PermissionError, FileNotFoundError) as e:
                print(f"Warning: Skipping directory {entry.name} - {str(e)}")
    return targets

def compress(folder, pwd, args):
    fmt = SUPPORTED_FORMATS[args.format]
    out_file = shlex.quote(os.path.join(args.output, f"{os.path.basename(folder)}.{fmt['ext']}"))
    
    cmd = [
        shlex.quote(args.sevenz), 'a',
        f'-t{args.format}', f'-mx{args.compression}',
        out_file, shlex.quote(folder)
    ]
    
    if pwd:
        if not fmt['pwd']: return False
        cmd.insert(2, f'-p{shlex.quote(pwd)}')
        if args.encrypt_list: 
            if fmt['enc_list']:
                cmd.insert(3, '-mhe=on')
            else:
                print("Encrypt list not supported for this format")
                return False
    
    if args.volume and fmt['vol']:
        cmd.insert(4, f'-v{args.volume}')
    
    try:
        subprocess.run(' '.join(cmd), shell=True, check=True, stdout=subprocess.DEVNULL)
        status = "[Encrypted]" if pwd else "[Open]"
        status += "+SecureList" if args.encrypt_list else ""
        print(f"✓ {os.path.basename(folder):40} {status}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {os.path.basename(folder):40} [Error {e.returncode}]")
        return False

def main():
    parser = argparse.ArgumentParser("Batch Compressor")
    parser.add_argument("target", help="Root directory to compress")
    parser.add_argument("-c", "--config", default="D:\Desktop\script\config\passwords.json", help="Password config file")
    parser.add_argument("-p", "--password", help="Password or @index (e.g. @1)")
    parser.add_argument("-7", "--sevenz", default="7z.exe", help="7z executable path")
    parser.add_argument("-o", "--output", default="output", help="Output directory")
    parser.add_argument("-v", "--volume", help="Volume size (7z only, e.g. 500m)")
    parser.add_argument("-f", "--format", default="7z", choices=SUPPORTED_FORMATS.keys(), help="Archive format")
    parser.add_argument("-l", "--level", type=int, default=5, choices=range(1,10), help="Compression level")
    parser.add_argument("-e", "--encrypt-list", action="store_true", help="Encrypt file list (7z only)")
    
    args = parser.parse_args()
    
    # Normalize target path
    args.target = os.path.normpath(args.target)
    
    # Validations
    if not os.path.isdir(args.target):
        exit(f"Error: Invalid target directory - {args.target}")
    if args.encrypt_list and (not args.password or args.format != '7z'):
        exit("Error: Encrypt list requires 7z format and password")
    
    # Process
    targets = find_targets(args.target)
    if not targets:
        exit("No directories need compression")
    
    os.makedirs(args.output, exist_ok=True)
    
    pwd = get_password(args)
    success = sum(compress(f, pwd, args) for f in targets)
    print(f"\nCompleted: {success} success / {len(targets)} total")

if __name__ == "__main__":
    main()