# DESCRIPTION:
# This script renames and centralizes filtered PDB models into 'podium' directories.
# It matches PDB filenames to rankings stored in the 'stats' CSV files.
# Resulting files are prefixed with their local and master ranks (e.g., '1_15_model.pdb'),
# making it easy to identify the top-performing designs in any file browser or PyMOL.
#
# SETUP & DIRECTORY STRUCTURE:
# 1. Script Location: Place this in your project root (same level as the 'stats' folder).
# 2. The Reference File: Requires 'stats/merged_all_final_design_stats.csv' to exist.
# 3. The Target Files: Looks for PDBs in '.../pooled/aligned/filtered_pdbs_jc_*' folders.
# 4. Output: Creates a 'podium' folder inside each 'aligned' directory.
#
# HOW TO EXECUTE:
# Run from terminal: 'python script_name.py'

import os
import pandas as pd
import shutil
import glob
import re
from pathlib import Path

def extract_identifier(filename):
    """Extract identifier including mpnn variant"""
    match = re.search(r'(s\d+_mpnn\d+)', filename)
    return match.group(1) if match else None


def get_file_rankings():
    """Get rankings for files from both individual and master CSV files"""
    stats_dir = "./stats"
    
    # Load master file with fixed name
    master_file = os.path.join(stats_dir, "merged_all_final_design_stats.csv")
    if not os.path.exists(master_file):
        print(f"Master file not found: {master_file}")
        return {}, {}
    
    master_df = pd.read_csv(master_file)
    master_df['master_rank'] = range(1, len(master_df) + 1)
    
    # Use 'Design' column in column B as identifier
    desc_column = 'Design'
    if desc_column not in master_df.columns:
        print(f"Column '{desc_column}' not found in master file")
        return {}, {}
    
    master_rankings = {}
    for _, row in master_df.iterrows():
        if pd.notna(row[desc_column]):
            identifier = extract_identifier(str(row[desc_column]))
            if identifier is not None:
                master_rankings[identifier] = row['master_rank']
    
    # Load individual subfolder files
    individual_rankings = {}
    all_csv_files = glob.glob(os.path.join(stats_dir, "merged_*_stats.csv"))
    
    for csv_file in all_csv_files:
        if csv_file == master_file:
            continue
        
        # Extract subfolder name from filename
        filename = os.path.basename(csv_file)
        subfolder_name = filename.replace("merged_", "").replace("_stats.csv", "")
        
        df = pd.read_csv(csv_file)
        
        if desc_column not in df.columns:
            print(f"Column '{desc_column}' not found in {filename}")
            continue
        
        df['individual_rank'] = range(1, len(df) + 1)
        
        if subfolder_name not in individual_rankings:
            individual_rankings[subfolder_name] = {}
        
        for _, row in df.iterrows():
            if pd.notna(row[desc_column]):
                identifier = extract_identifier(str(row[desc_column]))
                if identifier is not None:
                    individual_rankings[subfolder_name][identifier] = row['individual_rank']
    
    return individual_rankings, master_rankings

def find_corresponding_pdb_files():
    """Find all PDB files in */pooled/aligned/filtered* subfolders"""
    pdb_files = []
    
    # Search for pooled/aligned directories
    for root, dirs, files in os.walk("."):
        if root.endswith("pooled/aligned") or "/pooled/aligned" in root:
            # Look in subdirectories that contain "filtered" in their name
            for subdir in dirs:
                if "filtered" in subdir:
                    filtered_path = os.path.join(root, subdir)
                    for file in os.listdir(filtered_path):
                        if file.endswith(".pdb"):
                            pdb_path = os.path.join(filtered_path, file)
                            pdb_files.append(pdb_path)
    
    return pdb_files

def extract_mother_folder_name(pdb_path):
    """Extract the mother folder name from PDB path"""
    path_parts = Path(pdb_path).parts
    
    # Find the part before 'pooled'
    for i, part in enumerate(path_parts):
        if part == "pooled" and i > 0:
            return path_parts[i-1]
    
    return None

def clear_podium_directories():
    """Clear all existing podium directories before copying new files"""
    podium_dirs = []
    
    for root, dirs, files in os.walk("."):
        if "podium" in dirs:
            podium_path = os.path.join(root, "podium")
            if root.endswith("pooled/aligned") or "/pooled/aligned" in root:
                podium_dirs.append(podium_path)
    
    for podium_dir in podium_dirs:
        if os.path.exists(podium_dir):
            # Remove all files in podium directory
            for file in os.listdir(podium_dir):
                file_path = os.path.join(podium_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(f"Cleared existing files in: {podium_dir}")

def copy_files_with_rankings():
    """Main function to copy files with ranking prefixes"""
    print("Clearing existing podium directories...")
    clear_podium_directories()
    
    print("Getting file rankings from CSV files...")
    individual_rankings, master_rankings = get_file_rankings()
    
    if not master_rankings and not individual_rankings:
        print("No rankings found. Please check your CSV files.")
        return
    
    print(f"Loaded {len(master_rankings)} entries from master rankings")
    print(f"Loaded individual rankings for {len(individual_rankings)} subfolders")
    
    # Debug: Print some sample identifiers
    if master_rankings:
        print("Sample master ranking identifiers:", list(master_rankings.keys())[:5])
    if individual_rankings:
        for subfolder, rankings in list(individual_rankings.items())[:2]:
            print(f"Sample {subfolder} ranking identifiers:", list(rankings.keys())[:3])
    
    print("Finding PDB files in pooled/aligned folders...")
    pdb_files = find_corresponding_pdb_files()
    
    if not pdb_files:
        print("No PDB files found in */pooled/aligned subfolders")
        return
    
    print(f"Found {len(pdb_files)} PDB files to process")
    
    # Process each PDB file
    copied_files = 0
    skipped_files = 0
    overwritten_files = 0
    
    for pdb_path in pdb_files:
        # Extract information from path
        mother_folder = extract_mother_folder_name(pdb_path)
        if not mother_folder:
            print(f"Could not determine mother folder for: {pdb_path}")
            skipped_files += 1
            continue
        
        # Extract identifier from PDB filename
        pdb_filename = os.path.basename(pdb_path)
        identifier = extract_identifier(pdb_filename)
        
        if identifier is None:
            print(f"Could not extract identifier from: {pdb_filename}")
            skipped_files += 1
            continue
        
        # Get rankings using identifier
        individual_rank = None
        if mother_folder in individual_rankings and identifier in individual_rankings[mother_folder]:
            individual_rank = individual_rankings[mother_folder][identifier]
        
        master_rank = master_rankings.get(identifier)
        
        if individual_rank is None or master_rank is None:
            print(f"Rankings not found for identifier '{identifier}' from {pdb_filename} (individual: {individual_rank}, master: {master_rank})")
            skipped_files += 1
            continue
        
        # Create podium directory in the same aligned folder
        aligned_dir = os.path.dirname(pdb_path)
        podium_dir = os.path.join(aligned_dir, "podium")
        os.makedirs(podium_dir, exist_ok=True)
        
        # Create new filename with ranking prefixes
        new_filename = f"{individual_rank}_{master_rank}_{pdb_filename}"
        dest_path = os.path.join(podium_dir, new_filename)
        
        # Check if file already exists
        file_existed = os.path.exists(dest_path)
        
        # Copy file (this will overwrite if it exists)
        shutil.copy2(pdb_path, dest_path)
        
        if file_existed:
            print(f"Overwritten: {pdb_filename} ({identifier}) -> {new_filename}")
            overwritten_files += 1
        else:
            print(f"Copied: {pdb_filename} ({identifier}) -> {new_filename}")
        
        copied_files += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Files copied: {copied_files}")
    print(f"Files overwritten: {overwritten_files}")
    print(f"Files skipped: {skipped_files}")
    print(f"Total files processed: {len(pdb_files)}")

if __name__ == "__main__":
    copy_files_with_rankings()

