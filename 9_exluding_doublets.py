import os
import pandas as pd
import shutil
import glob
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

def extract_s_number(filename):
    """Extract the number following 's' from filename"""
    match = re.search(r'_s(\d+)_', filename)
    return match.group(1) if match else None

def extract_core_identifier_with_ag1_fallback(filename, master_rankings):
    """Extract core identifier and if not found, try replacing '_ag1_' with '_7_' in the identifier"""
    base_name = os.path.splitext(filename)[0]
    base_name = re.sub(r'^\d+_\d+_', '', base_name)
    base_name = re.sub(r'_model\d+.*$', '', base_name)
    base_name = re.sub(r'_aligned.*$', '', base_name)

    if base_name in master_rankings:
        return base_name

    if '_ag1_' in base_name:
        alt_name = base_name.replace('_ag1_', '_7_')
        if alt_name in master_rankings:
            print(f"  Found match using _7_ substitution: {base_name} -> {alt_name}")
            return alt_name

    return base_name

def get_master_rankings():
    """Get rankings from master CSV file"""
    stats_dir = "./stats"
    master_file = os.path.join(stats_dir, "merged_all_final_design_stats.csv")

    if not os.path.exists(master_file):
        print(f"Master file not found: {master_file}")
        return {}

    master_df = pd.read_csv(master_file)
    master_df['csv_rank'] = range(1, len(master_df) + 1)

    desc_column = 'Design'
    if desc_column not in master_df.columns:
        print(f"Column '{desc_column}' not found in master file")
        return {}

    rankings = {}
    for _, row in master_df.iterrows():
        if pd.notna(row[desc_column]):
            design_name = str(row[desc_column]).strip()
            design_name = os.path.splitext(design_name)[0]
            rankings[design_name] = row['csv_rank']

    return rankings

def find_best_and_worst_ranked_files(files, master_rankings):
    """Find the best (lowest rank number) and worst (highest rank number) files"""
    file_rankings = []

    for file_path in files:
        filename = os.path.basename(file_path)
        core_identifier = extract_core_identifier_with_ag1_fallback(filename, master_rankings)
        rank = master_rankings.get(core_identifier)

        if rank is None:
            for csv_name, csv_rank in master_rankings.items():
                if csv_name in core_identifier or core_identifier in csv_name:
                    rank = csv_rank
                    print(f"  Fuzzy match: {core_identifier} -> {csv_name} (rank {csv_rank})")
                    break

        if rank is not None:
            file_rankings.append((file_path, rank, core_identifier))
        else:
            print(f"  No ranking found for: {core_identifier} (original file: {filename})")

    if not file_rankings:
        return None, None, []

    file_rankings.sort(key=lambda x: x[1])
    best_file = file_rankings[0]
    worst_files = file_rankings[1:]

    return best_file, worst_files, file_rankings

def process_duplicates(auto_confirm=False):
    """Process duplicate files and organize them"""
    selection_dir = "./selection"
    pooled_dirs = ["filtered_pdbs_jc_5.0A", "filtered_pdbs_jc_5.5A", "filtered_pdbs_jc_6.0A"]

    master_rankings = get_master_rankings()
    if not master_rankings:
        print("No rankings loaded from CSV file")
        return

    print(f"Loaded {len(master_rankings)} rankings from CSV")

    for pooled_dir in pooled_dirs:
        pooled_path = os.path.join(selection_dir, pooled_dir)
        if not os.path.exists(pooled_path):
            print(f"Pooled directory not found: {pooled_path}")
            continue

        print(f"\n=== Processing: {pooled_dir} ===")

        # Create output directories
        unique_dir = os.path.join(pooled_path, "unique")
        not_unique_dir = os.path.join(pooled_path, "not_unique_basefold")
        os.makedirs(unique_dir, exist_ok=True)
        os.makedirs(not_unique_dir, exist_ok=True)

        # Group files by s_number
        s_number_groups = defaultdict(list)
        pdb_files = glob.glob(os.path.join(pooled_path, "*.pdb"))

        for pdb_file in pdb_files:
            filename = os.path.basename(pdb_file)
            s_number = extract_s_number(filename)
            if s_number:
                s_number_groups[s_number].append(pdb_file)

        copied_unique = 0
        copied_not_unique = 0

        for s_number, files in s_number_groups.items():
            if len(files) == 1:
                # Single file - copy to unique
                file_path = files[0]
                filename = os.path.basename(file_path)
                dest_path = os.path.join(unique_dir, filename)
                
                if not os.path.exists(dest_path):
                    shutil.copy2(file_path, dest_path)
                    copied_unique += 1
            else:
                # Multiple files - find best and worst
                best_file, worst_files, all_rankings = find_best_and_worst_ranked_files(files, master_rankings)
                
                if best_file:
                    # Copy best to unique
                    filename = os.path.basename(best_file[0])
                    dest_path = os.path.join(unique_dir, filename)
                    if not os.path.exists(dest_path):
                        shutil.copy2(best_file[0], dest_path)
                        copied_unique += 1
                    
                    # Copy worst to not_unique
                    for worst_file in worst_files:
                        filename = os.path.basename(worst_file[0])
                        dest_path = os.path.join(not_unique_dir, filename)
                        if not os.path.exists(dest_path):
                            shutil.copy2(worst_file[0], dest_path)
                            copied_not_unique += 1

        print(f"Files copied to unique/: {copied_unique}")
        print(f"Files copied to not_unique_basefold/: {copied_not_unique}")

def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(description='Remove duplicate PDB files based on rankings')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("PDB File Ranking and Duplicate Resolution Script")
    print("=" * 80)

    if not args.auto_confirm:
        response = input("Proceed with duplicate removal? (y/n): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return

    process_duplicates(args.auto_confirm)
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
