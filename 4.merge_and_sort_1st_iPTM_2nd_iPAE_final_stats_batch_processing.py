# This script processes the 'stats' folder to merge all individual BindCraft stat CSVs.
# It creates per-run summaries and one 'Master' file containing every design, 
# automatically ranking them by Average_i_pTM (High to Low) and Average_i_pAE (Low to High).
# It adds 'source_file' and 'source_subfolder' columns to track the origin of every hit.

import pandas as pd
import glob
import os
from pathlib import Path

# Dynamic base directory detection
def get_base_directory():
    """
    Dynamically determine the base directory for processing.
    Works from current working directory or detects common patterns.
    """
    current_dir = os.getcwd()
    
    # Check if we're already in a directory with stats subdirectories
    if os.path.exists(os.path.join(current_dir, "stats")):
        return current_dir
    
    # Check if we're in a subdirectory and need to go up
    parent_dir = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(parent_dir, "stats")):
        return parent_dir
    
    # Default to current directory and create stats if needed
    return current_dir

# Get dynamic base directory
base_dir = get_base_directory()
stats_dir = os.path.join(base_dir, "stats")

print(f"Working from base directory: {base_dir}")
print(f"Stats directory: {stats_dir}")

# Check if stats directory exists, create if needed
if not os.path.exists(stats_dir):
    print(f"Stats directory {stats_dir} does not exist. Creating it...")
    os.makedirs(stats_dir, exist_ok=True)

# List to hold all dataframes for master file
all_dfs = []

# Get all subdirectories in stats
subdirs = [d for d in os.listdir(stats_dir) if os.path.isdir(os.path.join(stats_dir, d))]

if not subdirs:
    print(f"No subdirectories found in {stats_dir}")
    print("Looking for CSV files directly in stats directory...")
    
    # If no subdirectories, look for CSV files directly in stats
    csv_files = glob.glob(os.path.join(stats_dir, "*.csv"))
    if csv_files:
        print(f"Found {len(csv_files)} CSV files directly in stats directory")
        # Process them as a single group
        subdirs = ["direct_files"]
        
        # Create a temporary subdirectory structure for processing
        temp_subdir = os.path.join(stats_dir, "direct_files")
        if not os.path.exists(temp_subdir):
            os.makedirs(temp_subdir)
            # Move CSV files to temp subdirectory for processing
            for csv_file in csv_files:
                if not csv_file.startswith(os.path.join(stats_dir, "merged_")):
                    dest_file = os.path.join(temp_subdir, os.path.basename(csv_file))
                    if not os.path.exists(dest_file):
                        os.link(csv_file, dest_file)  # Create hard link
    else:
        print("No CSV files found to process")
        exit()

# Process each subfolder
for subdir in subdirs:
    subdir_path = os.path.join(stats_dir, subdir)
    csv_files = glob.glob(os.path.join(subdir_path, "*.csv"))
    
    # Filter out already merged files to avoid double processing
    csv_files = [f for f in csv_files if not os.path.basename(f).startswith("merged_")]
    
    if csv_files:
        print(f"Processing {len(csv_files)} CSV files in {subdir}")
        
        # List to hold dataframes for this subfolder
        subdir_dfs = []
        
        for csv_file in sorted(csv_files):
            try:
                df = pd.read_csv(csv_file)
                # Add source information
                df["source_subfolder"] = subdir
                df["source_file"] = os.path.basename(csv_file)
                
                subdir_dfs.append(df)
                all_dfs.append(df)  # Also add to master list
                
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
        
        # Create merged file for this subfolder
        if subdir_dfs:
            merged_subdir_df = pd.concat(subdir_dfs, ignore_index=True)
            
            # Sort by Average_i_pTM (descending) and Average_i_pAE (ascending)
            sort_columns = []
            sort_ascending = []
            
            if "Average_i_pTM" in merged_subdir_df.columns:
                sort_columns.append("Average_i_pTM")
                sort_ascending.append(False)  # Descending for i_pTM
            
            if "Average_i_pAE" in merged_subdir_df.columns:
                sort_columns.append("Average_i_pAE")
                sort_ascending.append(True)   # Ascending for i_pAE (lower is better)
            
            if sort_columns:
                merged_subdir_df = merged_subdir_df.sort_values(sort_columns, ascending=sort_ascending)
                print(f"Sorted {subdir} data by {', '.join(sort_columns)}")
            else:
                print(f"Warning: Neither 'Average_i_pTM' nor 'Average_i_pAE' columns found in {subdir} data")
            
            subdir_output_file = os.path.join(stats_dir, f"merged_{subdir}_stats.csv")
            merged_subdir_df.to_csv(subdir_output_file, index=False)
            print(f"Created: {subdir_output_file}")

# Create master file with all data - SORT AFTER FINAL CONCATENATION
if all_dfs:
    # First concatenate ALL data
    master_df = pd.concat(all_dfs, ignore_index=True)
    
    # THEN sort the complete master dataframe
    sort_columns = []
    sort_ascending = []
    
    if "Average_i_pTM" in master_df.columns:
        sort_columns.append("Average_i_pTM")
        sort_ascending.append(False)  # Descending for i_pTM
    
    if "Average_i_pAE" in master_df.columns:
        sort_columns.append("Average_i_pAE")
        sort_ascending.append(True)   # Ascending for i_pAE (lower is better)
    
    if sort_columns:
        master_df = master_df.sort_values(sort_columns, ascending=sort_ascending).reset_index(drop=True)
        print(f"Sorted master data by {', '.join(sort_columns)}")
        
        # Show top 5 entries with both metrics for verification
        if len(sort_columns) == 2:
            print("Top 5 entries (i_pTM, i_pAE):")
            for i in range(min(5, len(master_df))):
                print(f"  {i+1}. i_pTM: {master_df.iloc[i]['Average_i_pTM']:.3f}, i_pAE: {master_df.iloc[i]['Average_i_pAE']:.3f}")
        else:
            print(f"Top 5 {sort_columns[0]} values: {master_df[sort_columns[0]].head().tolist()}")
    else:
        print("Warning: Neither 'Average_i_pTM' nor 'Average_i_pAE' columns found in master data")
    
    # Create master file in current working directory's stats folder
    master_output_file = os.path.join(stats_dir, "merged_all_final_design_stats.csv")
    master_df.to_csv(master_output_file, index=False)
    print(f"Created master file: {master_output_file}")
    print(f"Master file contains {len(master_df)} total rows from {len(subdirs)} subfolders")
    
    # Verify file was created successfully
    if os.path.exists(master_output_file):
        file_size = os.path.getsize(master_output_file)
        print(f"Master file verified: {file_size} bytes")
    else:
        print(f"WARNING: Master file was not created at expected location: {master_output_file}")
        
else:
    print("No CSV files found to merge")

print("Pooling completed!")
print(f"All output files created in: {stats_dir}")


