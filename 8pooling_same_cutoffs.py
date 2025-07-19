import os
import shutil
import glob
import sys
import argparse
from pathlib import Path
from collections import defaultdict

def find_subfolders_with_same_name():
    """Find all subfolders with the same name across the selection directory tree"""
    subfolder_paths = defaultdict(list)
    selection_dir = "./selection"
    
    if not os.path.exists(selection_dir):
        print(f"Selection directory not found: {selection_dir}")
        return subfolder_paths

    for root, dirs, files in os.walk(selection_dir):
        for dir_name in dirs:
            full_path = os.path.join(root, dir_name)
            subfolder_paths[dir_name].append(full_path)

    return subfolder_paths

def pool_pdb_files():
    """Pool all PDB files from subfolders with same names in selection directory"""
    selection_dir = "./selection"
    subfolder_paths = find_subfolders_with_same_name()

    if not subfolder_paths:
        print("No subfolders found in selection directory")
        return

    total_folders_created = 0
    total_files_copied = 0

    for folder_name, paths in subfolder_paths.items():
        if len(paths) > 1:
            print(f"\nProcessing folder name: '{folder_name}' (found in {len(paths)} locations)")

            pdb_files = []
            for folder_path in paths:
                folder_pdb_files = glob.glob(os.path.join(folder_path, "*.pdb"))
                if folder_pdb_files:
                    print(f"  Found {len(folder_pdb_files)} PDB files in: {folder_path}")
                    pdb_files.extend(folder_pdb_files)

            if pdb_files:
                pooled_folder = os.path.join(selection_dir, folder_name)
                os.makedirs(pooled_folder, exist_ok=True)

                files_copied = 0
                for pdb_file in pdb_files:
                    filename = os.path.basename(pdb_file)
                    dest_path = os.path.join(pooled_folder, filename)

                    if os.path.exists(dest_path):
                        rel_source = os.path.relpath(os.path.dirname(pdb_file), selection_dir)
                        safe_path = rel_source.replace(os.sep, "_").replace(".", "")
                        name, ext = os.path.splitext(filename)
                        new_filename = f"{name}_{safe_path}{ext}"
                        dest_path = os.path.join(pooled_folder, new_filename)

                    shutil.copy2(pdb_file, dest_path)
                    files_copied += 1

                print(f"  Created pooled folder: {pooled_folder}")
                print(f"  Copied {files_copied} PDB files")
                total_folders_created += 1
                total_files_copied += files_copied

    print(f"\n=== SUMMARY ===")
    print(f"Pooled folders created: {total_folders_created}")
    print(f"Total PDB files copied: {total_files_copied}")

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Pool PDB files by same cutoff names')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("PDB File Pooling Script (Selection Directory Only)")
    print("=" * 60)

    subfolder_paths = find_subfolders_with_same_name()
    multiple_folders = {name: paths for name, paths in subfolder_paths.items() if len(paths) > 1}

    print(f"Unique folder names found: {len(subfolder_paths)}")
    print(f"Folder names appearing multiple times: {len(multiple_folders)}")

    if not args.auto_confirm:
        response = input("Proceed with pooling PDB files? (y/n): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return

    pool_pdb_files()

if __name__ == "__main__":
    main()
