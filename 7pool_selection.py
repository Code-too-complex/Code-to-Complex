# DESCRIPTION:
# This script scans for PDBs in 'podium' folders (the final winners of the filtering 
# and ranking process) and copies them into a central './selection' directory.

# SETUP & DIRECTORY STRUCTURE:
# 1. Script Location: Place this in the project root.
# 2. Input: Looks for the pattern: XXXX/pooled/aligned/filtered_pdbs_jc_XXXA/podium/
# 3. Output: Creates a new directory './selection' in the project root.
#
# HOW TO EXECUTE:
# Run from terminal: 'python script_name.py'

import os
import shutil
import glob
import re
import sys
import argparse
from pathlib import Path

def find_podium_files():
    """Find all files in XXXX/pooled/aligned/filtered_pdbs_jc_XXXA/podium structure"""
    podium_files = []
    pattern = r'^(.+)/pooled/aligned/(filtered_pdbs_jc_.+A)/podium$'

    for root, dirs, files in os.walk("."):
        if root.endswith("/podium"):
            match = re.match(pattern, root)
            if match:
                varying_part = match.group(1)
                filter_folder = match.group(2)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    podium_files.append({
                        'file_path': file_path,
                        'filename': file,
                        'varying_part': varying_part,
                        'filter_folder': filter_folder,
                        'source_dir': root
                    })

    return podium_files

def preview_copy_operations():
    """Preview what files would be copied and where"""
    print("Scanning for podium files...")
    podium_files = find_podium_files()

    if not podium_files:
        print("No files found in podium directories matching the pattern")
        return []

    print(f"Found {len(podium_files)} files in podium directories")

    copy_operations = []
    destination_summary = {}

    for file_info in podium_files:
        dest_dir = os.path.join("./selection", file_info['varying_part'], file_info['filter_folder'])
        dest_path = os.path.join(dest_dir, file_info['filename'])

        copy_operations.append({
            'source': file_info['file_path'],
            'destination': dest_path,
            'dest_dir': dest_dir,
            'filename': file_info['filename'],
            'varying_part': file_info['varying_part'],
            'filter_folder': file_info['filter_folder']
        })

        dest_key = f"{file_info['varying_part']}/{file_info['filter_folder']}"
        if dest_key not in destination_summary:
            destination_summary[dest_key] = 0
        destination_summary[dest_key] += 1

    return copy_operations, destination_summary

def execute_copy_operations(copy_operations):
    """Execute the actual copy operations"""
    copied_count = 0
    skipped_count = 0
    error_count = 0

    os.makedirs("./selection", exist_ok=True)

    for op in copy_operations:
        try:
            os.makedirs(op['dest_dir'], exist_ok=True)

            if os.path.exists(op['destination']):
                print(f"Warning: File already exists, skipping: {op['filename']}")
                skipped_count += 1
                continue

            shutil.copy2(op['source'], op['destination'])
            print(f"Copied: {op['filename']} -> ./selection/{op['varying_part']}/{op['filter_folder']}/")
            copied_count += 1

        except Exception as e:
            print(f"Error copying {op['filename']}: {str(e)}")
            error_count += 1

    print(f"\n=== SUMMARY ===")
    print(f"Files copied: {copied_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print(f"Total operations: {len(copy_operations)}")

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Pool selection files from podium directories')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("Podium Files Selection Copy Script")
    print("=" * 50)

    copy_operations, destination_summary = preview_copy_operations()

    if not copy_operations:
        print("No files to copy. Exiting.")
        return

    print(f"\n=== PREVIEW: {len(copy_operations)} files will be copied ===")
    print("\nDestination summary:")
    for dest_path, file_count in sorted(destination_summary.items()):
        print(f"  ./selection/{dest_path}: {file_count} files")

    if not args.auto_confirm:
        print("\n" + "=" * 50)
        response = input("Proceed with copying these files? (y/n): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return

    print("\nExecuting copy operations...")
    execute_copy_operations(copy_operations)

if __name__ == "__main__":
    main()
