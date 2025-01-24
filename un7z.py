import os
import json
import subprocess
import argparse

def load_passwords(config_path):
    try:
        with open(config_path) as f:
            passwords = json.load(f)
            return passwords if isinstance(passwords, list) else []
    except Exception:
        return []

def find_archives(target_dir):
    archives = []
    for root, _, files in os.walk(target_dir):
        for f in files:
            lower = f.lower()
            if lower.endswith(('.7z', '.001', '.7z.001')):
                archives.append(os.path.join(root, f))
    return archives

def parse_passwords(args):
    passwords = []
    config_pwds = load_passwords(args.config) if os.path.exists(args.config) else []
    
    # Process command line passwords and indexes
    for item in args.passwords:
        if item.startswith('@'):
            try:
                index = int(item[1:]) - 1
                passwords.append(config_pwds[index])
            except (ValueError, IndexError):
                print(f"Invalid index: {item}")
                exit(1)
        else:
            passwords.append(item)
    
    # Merge all config passwords (if -a enabled)
    if args.all_config:
        passwords.extend(pwd for pwd in config_pwds if pwd not in passwords)
    
    return list(dict.fromkeys(passwords))  # Remove duplicates while preserving order

def extract(file_path, passwords, sevenz, output_dir):
    base_name = os.path.basename(file_path).split('.')[0]
    output_path = os.path.join(output_dir, base_name)
    
    for idx, pwd in enumerate(passwords, 1):
        try:
            subprocess.run([
                sevenz, 'x', f'-p{pwd}', '-y',
                f'-o{output_path}', file_path
            ], check=True, stdout=subprocess.DEVNULL)
            print(f"✓ {os.path.basename(file_path)} extracted successfully (Password #{idx})")
            return True
        except subprocess.CalledProcessError:
            continue
    
    print(f"✗ {os.path.basename(file_path)} all passwords failed")
    return False

def main():
    parser = argparse.ArgumentParser("7z Batch Extractor")
    parser.add_argument("target", help="Target directory containing archives")
    parser.add_argument("-c", "--config", default="passwords.json", 
                       help="Password configuration file (JSON array)")
    parser.add_argument("-p", "--passwords", nargs="+", default=[], 
                       help="Passwords to try (supports @index for config entries)")
    parser.add_argument("-a", "--all-config", action="store_true",
                       help="Include all passwords from config file")
    parser.add_argument("-7", "--7z", default="7z.exe", dest="sevenz", 
                       help="Path to 7z executable")
    parser.add_argument("-o", "--output", default="output", 
                       help="Output directory for extracted files")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.target):
        print("Error: Target directory does not exist")
        exit(1)

    passwords = parse_passwords(args)
    if not passwords:
        print("Error: No valid passwords found")
        exit(1)

    archives = find_archives(args.target)
    if not archives:
        print("No archive files found")
        return

    os.makedirs(args.output, exist_ok=True)
    
    success = 0
    for arch in archives:
        success += extract(arch, passwords, args.sevenz, args.output)
    
    print(f"\nExtraction complete: {success} successful / {len(archives)} total")

if __name__ == "__main__":
    main()