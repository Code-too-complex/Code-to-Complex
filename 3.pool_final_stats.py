#!/usr/bin/env python3

import os
import shutil
from pathlib import Path

# Dynamic directory detection - works from current working directory
current_dir = os.getcwd()
src_dir = current_dir
dest_dir = os.path.join(current_dir, "stats")

print(f"Working from: {src_dir}")
print(f"Stats destination: {dest_dir}")

# Create the main stats directory
os.makedirs(dest_dir, exist_ok=True)

# Find all final_design_stats.csv files
src_path = Path(src_dir)
csv_files = list(src_path.rglob("final_design_stats.csv"))

print(f"Found {len(csv_files)} final_design_stats.csv files")

for file_path in csv_files:
    # Get relative path from source directory
    relative_path = file_path.relative_to(src_path)
    
    # Extract the first folder name (top-level directory)
    first_folder = relative_path.parts[0]
    
    # Create subdirectory within stats for this first folder
    first_folder_dest = Path(dest_dir) / first_folder
    first_folder_dest.mkdir(exist_ok=True)
    
    # Get the remaining path after the first folder for filename suffix
    remaining_parts = relative_path.parts[1:-1]  # Exclude first folder and filename
    
    # Create filename
    if remaining_parts:
        remaining_path = "_".join(remaining_parts)
        filename = f"final_design_stats_{remaining_path}.csv"
    else:
        filename = "final_design_stats.csv"
    
    # Copy the file to the appropriate subdirectory
    dest_file = first_folder_dest / filename
    shutil.copy2(file_path, dest_file)
    
    print(f"Copied: {file_path} -> {first_folder}/{filename}")

print(f"All final_design_stats.csv files have been organized by first-level folders in {dest_dir}")
