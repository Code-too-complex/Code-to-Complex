import os
import glob
import shutil
from Bio import PDB
import sys

def get_water_coordinates(reference_pdb):
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("reference", reference_pdb)
    
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.get_resname() == "HOH":  # Water residue
                    for atom in residue:
                        return atom.coord  # Return the first water atom's coordinates
    return None

def min_distance_to_chainA(pdb_file, water_coord, backbone_only=False):
    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("query", pdb_file)
    
    min_dist = float("inf")
    backbone_atoms = {"N", "CA", "C", "O"} if backbone_only else None
    
    for model in structure:
        for chain in model:
            if chain.id.strip().upper() == "B":  # Ensure robust chain ID comparison
                for residue in chain:
                    for atom in residue:
                        if backbone_only and atom.get_name() not in backbone_atoms:
                            continue  # Skip sidechain atoms if backbone_only is set
                        
                        distance = atom.coord - water_coord
                        dist_value = (distance**2).sum()**0.5  # Euclidean distance
                        min_dist = min(min_dist, dist_value)
    return min_dist

def filter_pdb_files_in_aligned_folders(aligned_folders, reference_pdb, threshold, backbone_only=False):
    water_coord = get_water_coordinates(reference_pdb)
    print("Water coordinates:", water_coord)
    if water_coord is None:
        print("No water molecule found in the reference PDB.")
        return []

    all_filtered_files = []

    for aligned_folder in aligned_folders:
        print(f"\nProcessing aligned folder: {aligned_folder}")
        pdb_files = glob.glob(os.path.join(aligned_folder, "*.pdb"))
        print(f"Found {len(pdb_files)} PDB files in {aligned_folder} and its subfolders.")
        
        if len(pdb_files) == 0:
            print(f"No PDB files found in {aligned_folder}, skipping...")
            continue
        
        output_folder = os.path.join(aligned_folder, f"filtered_pdbs_jc_{threshold}A")
        failed_folder = os.path.join(aligned_folder, f"failed_pdbs_jc_{threshold}A")
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        if not os.path.exists(failed_folder):
            os.makedirs(failed_folder)
        
        for pdb_file in pdb_files:
            min_dist = min_distance_to_chainA(pdb_file, water_coord, backbone_only)
            print(f"{pdb_file} -> min distance: {min_dist:.2f}")
            dest_folder = output_folder if min_dist >= threshold else failed_folder
            
            base_name = os.path.basename(pdb_file)
            name, ext = os.path.splitext(base_name)
            new_name = f"{name}_{threshold:.1f}{ext}"
            
            dest_file = os.path.join(dest_folder, new_name)
            
            if os.path.abspath(pdb_file) != os.path.abspath(dest_file):
                shutil.copy(pdb_file, dest_file)
                print(f"Copied to {os.path.basename(dest_folder)}")
            
            if min_dist >= threshold:
                all_filtered_files.append(dest_file)
    
    return all_filtered_files

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python filter_script.py <threshold> [backbone_only]")
        sys.exit(1)

    threshold = float(sys.argv[1])
    backbone_only = bool(int(sys.argv[2])) if len(sys.argv) > 2 else False

    # Find all aligned folders starting from current directory (script location)
    start_dir = os.getcwd()
    aligned_folders = []
    
    print(f"Searching for 'aligned' folders within 'pooled' subfolders starting from: {start_dir}")
    for root, dirs, files in os.walk(start_dir):
        # Only consider 'aligned' folders that are inside a 'pooled' folder
        if 'aligned' in dirs and 'pooled' in root.split(os.sep):
            aligned_path = os.path.join(root, 'aligned')
            aligned_folders.append(aligned_path)
            print(f"Found aligned folder: {aligned_path}")

    if not aligned_folders:
        print("No 'aligned' folders found inside 'pooled' subfolders in the directory tree.")
        sys.exit(1)

    # Reference PDB is in the same folder as the script
    reference_pdb = os.path.join(start_dir, "RXFP1_Glyco_marker.pdb")
    if not os.path.exists(reference_pdb):
        print(f"Reference PDB file not found: {reference_pdb}")
        sys.exit(1)

    print(f"\nUsing reference PDB: {reference_pdb}")
    print(f"Threshold: {threshold}A")
    print(f"Backbone only: {backbone_only}")
    print(f"Found {len(aligned_folders)} aligned folders to process\n")

    filtered_files = filter_pdb_files_in_aligned_folders(aligned_folders, reference_pdb, threshold, backbone_only)
    
    total_processed = sum(len(glob.glob(os.path.join(folder, "*.pdb"))) for folder in aligned_folders)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total aligned folders processed: {len(aligned_folders)}")
    print(f"Total PDB files processed: {total_processed}")
    print(f"Files passing threshold ({threshold}A): {len(filtered_files)}")
    print(f"Files failing threshold: {total_processed - len(filtered_files)}")

