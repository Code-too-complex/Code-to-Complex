import os
import numpy as np
import pandas as pd
import sys
import argparse
from Bio.PDB import PDBParser, NeighborSearch, Selection
from Bio.PDB.PDBExceptions import PDBConstructionWarning
import warnings

warnings.filterwarnings('ignore', category=PDBConstructionWarning)

def calculate_distance(coord1, coord2):
    return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(coord1, coord2)))

def check_polar_contacts(residue1, residue2, distance_threshold=3.5):
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

def analyze_pdb_files(folder_path, target_chain='A', output_csv='tag_placement_results2.csv'):
    parser = PDBParser(QUIET=True)
    results = []

    if target_chain not in {'A', 'B'}:
        raise ValueError("Target chain must be 'A' or 'B'")

    other_chain = 'B' if target_chain == 'A' else 'A'

    pdb_files = [f for f in os.listdir(folder_path) if f.endswith('.pdb')]
    if not pdb_files:
        print(f"No PDB files found in {folder_path}")
        return results

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

    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_csv, index=False)
        print(f"Analysis complete. Results saved to {output_csv}")
    else:
        print("No valid PDB files processed. No output CSV generated.")

    return results

def main():
    parser = argparse.ArgumentParser(description='Analyze PDB files for tag placement')
    parser.add_argument('--folder', required=True, help='Folder path containing PDB files')
    parser.add_argument('--chain', default='A', help='Target chain (A or B)')
    parser.add_argument('--output', default='tag_placement_results2.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    try:
        results = analyze_pdb_files(args.folder, args.chain.upper(), args.output)
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
