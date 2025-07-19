#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
import sys
from Bio.PDB import PDBParser, NeighborSearch, Selection
from Bio.PDB.PDBExceptions import PDBConstructionWarning
import warnings

warnings.filterwarnings('ignore', category=PDBConstructionWarning)

def calculate_distance(coord1, coord2):
    """Calculate Euclidean distance between two coordinate points"""
    return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(coord1, coord2)))

def check_polar_contacts(residue1, residue2, distance_threshold=3.5):
    """Check for polar contacts between two residues"""
    polar_atoms = {'N', 'O', 'S'}
    contacts = []
    
    for atom1 in residue1.get_atoms():
        for atom2 in residue2.get_atoms():
            if atom1.element in polar_atoms and atom2.element in polar_atoms:
                dist = calculate_distance(atom1.get_coord(), atom2.get_coord())
                if dist <= distance_threshold:
                    contacts.append((atom1, atom2, dist))
    
    return contacts

def check_intra_chain_polar_contacts(chain, n_term_res, c_term_res, distance_threshold=3.5):
    """Check for intra-chain polar contacts for N and C terminal residues"""
    n_contacts = 0
    c_contacts = 0

    for res in chain.get_residues():
        if res != n_term_res:
            contacts = check_polar_contacts(n_term_res, res, distance_threshold)
            n_contacts += len(contacts)

    for res in chain.get_residues():
        if res != c_term_res:
            contacts = check_polar_contacts(c_term_res, res, distance_threshold)
            c_contacts += len(contacts)

    return n_contacts, c_contacts

def get_available_directories():
    """Find all available directories with PDB files"""
    base_dirs = ["selection"]
    available_dirs = []
    
    for base_dir in base_dirs:
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                pdb_files = [f for f in files if f.endswith('.pdb')]
                if pdb_files:
                    available_dirs.append({
                        'path': root,
                        'pdb_count': len(pdb_files),
                        'description': os.path.basename(root)
                    })
    
    return available_dirs

def display_directory_options(available_dirs):
    """Display available directories for user selection"""
    print("\n=== Available PDB Directories ===")
    for i, dir_info in enumerate(available_dirs, 1):
        print(f"{i}. {dir_info['path']} ({dir_info['pdb_count']} PDB files)")
    print(f"{len(available_dirs) + 1}. Custom path (enter manually)")
    print(f"{len(available_dirs) + 2}. Process all directories")

def get_user_selection(available_dirs):
    """Get user's directory selection"""
    while True:
        try:
            display_directory_options(available_dirs)
            choice = input(f"\nSelect directory (1-{len(available_dirs) + 2}): ").strip()
            
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_dirs):
                    return [available_dirs[choice_num - 1]['path']]
                elif choice_num == len(available_dirs) + 1:
                    custom_path = input("Enter custom directory path: ").strip()
                    if os.path.exists(custom_path):
                        return [custom_path]
                    else:
                        print(f"Error: Directory '{custom_path}' does not exist.")
                        continue
                elif choice_num == len(available_dirs) + 2:
                    return [dir_info['path'] for dir_info in available_dirs]
                else:
                    print("Invalid selection. Please try again.")
            else:
                print("Please enter a number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")

def get_chain_selection():
    """Get target chain selection from user"""
    while True:
        chain = input("Target chain for analysis (A/B) [default: B]: ").strip().upper()
        if not chain:
            return 'B'
        elif chain in ['A', 'B']:
            return chain
        else:
            print("Please enter 'A' or 'B'")

def analyze_pdb_files(folder_path, target_chain='A', output_csv='tag_placement_results.csv'):
    """Analyze PDB files for optimal tag placement positions"""
    parser = PDBParser(QUIET=True)
    results = []

    if target_chain not in {'A', 'B'}:
        raise ValueError("Target chain must be 'A' or 'B'")

    other_chain = 'B' if target_chain == 'A' else 'A'

    # Validate directory exists
    if not os.path.exists(folder_path):
        print(f"Error: Directory {folder_path} does not exist")
        return []

    pdb_files = [f for f in os.listdir(folder_path) if f.endswith('.pdb')]
    if not pdb_files:
        print(f"No PDB files found in {folder_path}")
        return []

    print(f"Found {len(pdb_files)} PDB files to analyze")

    for pdb_file in pdb_files:
        pdb_path = os.path.join(folder_path, pdb_file)
        try:
            structure = parser.get_structure(pdb_file[:-4], pdb_path)
            model = structure[0]

            chain_target = None
            chain_other = None
            for chain in model:
                if chain.id == target_chain:
                    chain_target = chain
                elif chain.id == other_chain:
                    chain_other = chain

            if not chain_target or not chain_other:
                print(f"Warning: {pdb_file} missing chain {target_chain} or {other_chain}. Skipping...")
                continue

            residues_target = list(chain_target.get_residues())
            if not residues_target:
                print(f"Warning: No residues in chain {target_chain} of {pdb_file}. Skipping...")
                continue

            n_term_res = residues_target[0]
            c_term_res = residues_target[-1]

            def get_ca_coord(residue):
                for atom in residue.get_atoms():
                    if atom.name == 'CA':
                        return atom.get_coord()
                return next(residue.get_atoms()).get_coord()

            n_term_coord = get_ca_coord(n_term_res)
            c_term_coord = get_ca_coord(c_term_res)

            other_ca_coords = [get_ca_coord(res) for res in chain_other.get_residues() 
                             if any(atom.name == 'CA' for atom in res.get_atoms())]

            if not other_ca_coords:
                print(f"Warning: No CA atoms in chain {other_chain} of {pdb_file}. Skipping...")
                continue

            n_term_ca_dist = min([calculate_distance(n_term_coord, coord) for coord in other_ca_coords])
            c_term_ca_dist = min([calculate_distance(c_term_coord, coord) for coord in other_ca_coords])

            # Calculate shortest distance from any atom to any atom
            n_term_atoms = [atom.get_coord() for atom in n_term_res.get_atoms()]
            c_term_atoms = [atom.get_coord() for atom in c_term_res.get_atoms()]
            other_atoms = [atom.get_coord() for atom in chain_other.get_atoms()]

            n_term_any_dist = min(calculate_distance(n_term_atom, other_atom) 
                                for n_term_atom in n_term_atoms for other_atom in other_atoms) if n_term_atoms and other_atoms else None
            c_term_any_dist = min(calculate_distance(c_term_atom, other_atom) 
                                for c_term_atom in c_term_atoms for other_atom in other_atoms) if c_term_atoms and other_atoms else None

            # Check polar contacts
            n_term_contacts_other = []
            c_term_contacts_other = []
            for res_other in chain_other.get_residues():
                n_term_contacts_other.extend(check_polar_contacts(n_term_res, res_other))
                c_term_contacts_other.extend(check_polar_contacts(c_term_res, res_other))

            n_term_intra_contacts, c_term_intra_contacts = check_intra_chain_polar_contacts(
                chain_target, n_term_res, c_term_res)

            # Determine tag recommendation
            if n_term_ca_dist > c_term_ca_dist:
                tag_rec = 'N-terminal (greater distance to other chain)'
            elif c_term_ca_dist > n_term_ca_dist:
                tag_rec = 'C-terminal (greater distance to other chain)'
            else:
                tag_rec = 'No clear recommendation (equal distances to other chain)'

            results.append({
                'PDB_File': pdb_file,
                'Target_Chain': target_chain,
                'Other_Chain': other_chain,
                'N_Term_Distance_to_Other_Chain': n_term_ca_dist,
                'C_Term_Distance_to_Other_Chain': c_term_ca_dist,
                'N_Term_Shortest_Distance_to_Any_Atom': n_term_any_dist,
                'C_Term_Shortest_Distance_to_Any_Atom': c_term_any_dist,
                'N_Term_Polar_Contacts_with_Other_Chain': len(n_term_contacts_other),
                'C_Term_Polar_Contacts_with_Other_Chain': len(c_term_contacts_other),
                'N_Term_Polar_Contacts_Within_Chain': n_term_intra_contacts,
                'C_Term_Polar_Contacts_Within_Chain': c_term_intra_contacts,
                'Tag_Recommendation': tag_rec
            })

        except Exception as e:
            print(f"Error processing {pdb_file}: {str(e)}")
            continue

    print(f"Successfully analyzed {len(results)} structures")
    return results

def main():
    """Main interactive function"""
    print("=== Interactive Tag Placement Analysis ===")
    print("This script will analyze PDB files for optimal tag placement positions.")
    
    # Find available directories
    available_dirs = get_available_directories()
    
    if not available_dirs:
        print("No directories with PDB files found.")
        sys.exit(1)
    
    # Get user selections
    selected_dirs = get_user_selection(available_dirs)
    target_chain = get_chain_selection()
    
    # Get user's preferred filename but ensure Snakemake compatibility
    user_file = input("Additional output filename (optional, for your reference): ").strip()
    
    # Always use the Snakemake-expected filename as primary output
    snakemake_output = "interactive_tag_placement_results.csv"
    
    # Process each selected directory
    all_results = []
    for directory in selected_dirs:
        print(f"\nProcessing directory: {directory}")
        
        # Validate directory before processing
        if not os.path.exists(directory):
            print(f"Error: Directory {directory} does not exist")
            continue
            
        results = analyze_pdb_files(directory, target_chain, f"temp_{os.path.basename(directory)}_results.csv")
        
        # Handle None return or empty results
        if results is None:
            print(f"Warning: No results returned for directory {directory}")
            results = []
        
        # Add directory information to results
        for result in results:
            result['Source_Directory'] = directory
        
        all_results.extend(results)
    
    # Combine and save results
    if all_results:
        df_combined = pd.DataFrame(all_results)
        
        # Always save to Snakemake-expected filename
        df_combined.to_csv(snakemake_output, index=False)
        print(f"\nAnalysis complete!")
        print(f"Total structures analyzed: {len(all_results)}")
        print(f"Results saved to: {snakemake_output}")
        
        # Optionally save to user-specified filename as well
        if user_file and user_file != snakemake_output:
            df_combined.to_csv(user_file, index=False)
            print(f"Results also saved to: {user_file}")
        
        # Display summary statistics
        print(f"\nSummary by source directory:")
        summary = df_combined.groupby('Source_Directory').size()
        for directory, count in summary.items():
            print(f"  {directory}: {count} structures")
            
        # Display tag placement recommendations summary
        print(f"\nTag placement recommendations:")
        tag_summary = df_combined['Tag_Recommendation'].value_counts()
        for recommendation, count in tag_summary.items():
            print(f"  {recommendation}: {count} structures")
    else:
        print("No valid PDB files were processed.")
        # Create empty output file to satisfy Snakemake
        with open(snakemake_output, 'w') as f:
            f.write("No results generated\n")

if __name__ == "__main__":
    main()
