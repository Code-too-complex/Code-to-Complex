# This script automates the spatial alignment of PDB models to a reference (RXFP1_Relaxin_LRR_Glyco).
# Purpose: To facilitate the removal of generated structures that physically clash with a 
# 'placeholder' molecule—manually positioned to represent the volume of missing glycans.
# This script recursively finds PDB files within 'pooled' directories (ignoring 'Ranked' folders),
# loads them into PyMOL, and aligns them to a reference structure (RXFP1_Relaxin_LRR_Glyco.pdb).
# It then applies basic styling (gray cartoon for models, red for reference) 
# and saves the newly aligned coordinates into local 'aligned' subdirectories.

from pymol import cmd
import glob
import os

# Step 1: Find all PDB files in "pooled" subfolders, excluding "Ranked" folders
pdb_files = []
for root, dirs, files in os.walk("."):
    # Skip directories named "Ranked" or any subdirectories within them
    if "Ranked" in root.split(os.sep):
        continue
    
    if "pooled" in root:
        for file in files:
            if file.endswith(".pdb"):
                pdb_files.append(os.path.join(root, file))

print(f"Found {len(pdb_files)} PDB files in pooled directories (excluding Ranked folders)")

# Step 2: Load reference structure from script directory
reference = "RXFP1_Relaxin_LRR_Glyco"
reference_file = f"{reference}.pdb"

if not os.path.exists(reference_file):
    raise ValueError(f"Reference structure '{reference_file}' not found in script directory.")

cmd.load(reference_file, reference)
print(f"Loaded reference structure: {reference}")

# Step 3: Load all PDB files from pooled directories
for pdb_file in pdb_files:
    obj_name = os.path.basename(pdb_file).replace(".pdb", "")
    cmd.load(pdb_file, obj_name)
    print(f"Loaded: {obj_name}")

# Step 4: Create aligned directory in pooled folder
pooled_dirs = set()
for pdb_file in pdb_files:
    pooled_dir = os.path.dirname(pdb_file)
    pooled_dirs.add(pooled_dir)

for pooled_dir in pooled_dirs:
    aligned_dir = os.path.join(pooled_dir, "aligned")
    os.makedirs(aligned_dir, exist_ok=True)
    print(f"Created aligned directory: {aligned_dir}")

# Step 5: Align all structures to the reference
all_objects = cmd.get_object_list()
for obj in all_objects:
    if obj != reference:
        cmd.align(obj, reference)
        print(f"Aligned {obj} to {reference}")

# Step 6: Adjust visualization
cmd.hide("everything")
cmd.show("cartoon")
cmd.color("gray", "all")
cmd.color("red", reference)
cmd.zoom()

# Step 7: Save aligned structures to aligned folders
for pdb_file in pdb_files:
    obj_name = os.path.basename(pdb_file).replace(".pdb", "")
    pooled_dir = os.path.dirname(pdb_file)
    aligned_dir = os.path.join(pooled_dir, "aligned")
    output_file = os.path.join(aligned_dir, f"{obj_name}_aligned.pdb")
    cmd.save(output_file, obj_name)
    print(f"Saved aligned structure: {output_file}")

print("Alignment and saving completed!")


