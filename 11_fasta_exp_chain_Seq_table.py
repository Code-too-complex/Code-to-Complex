from Bio import PDB
from Bio.PDB.Polypeptide import protein_letters_3to1 as three_to_one
import os
import pandas as pd
import sys
import argparse

def extract_sequences(pdb_dir, target_chain, output_file):
    """Extract sequences from PDB files"""
    
    # Validate folder path
    if not os.path.exists(pdb_dir):
        print(f"Error: Folder path '{pdb_dir}' does not exist.")
        return False

    if not os.path.isdir(pdb_dir):
        print(f"Error: '{pdb_dir}' is not a directory.")
        return False

    # Create a PDB parser
    pdb_parser = PDB.PDBParser(QUIET=True)

    # List to store sequence data
    sequence_data = []

    # Process PDB files
    pdb_files_found = False
    for pdb_file in os.listdir(pdb_dir):
        if pdb_file.endswith(".pdb"):
            pdb_files_found = True
            pdb_path = os.path.join(pdb_dir, pdb_file)
            try:
                structure = pdb_parser.get_structure(pdb_file[:-4], pdb_path)
                chain_found = False
                
                for chain in structure.get_chains():
                    if chain.id == target_chain:
                        chain_found = True
                        seq = ""
                        for residue in chain:
                            if PDB.is_aa(residue):
                                seq += three_to_one.get(residue.get_resname(), 'X')

                        sequence_data.append({
                            "PDB_ID": pdb_file[:-4],
                            "Chain": target_chain,
                            "Sequence": seq
                        })
                        break

                if not chain_found:
                    print(f"Warning: Chain {target_chain} not found in {pdb_file}")

            except Exception as e:
                print(f"Error processing {pdb_file}: {str(e)}")

    # Check if any PDB files were found
    if not pdb_files_found:
        print(f"Error: No PDB files found in directory '{pdb_dir}'")
        return False

    # Check if any sequences were extracted
    if not sequence_data:
        print(f"Error: No sequences found for chain {target_chain} in any PDB files")
        return False

    # Create a DataFrame from the sequence data
    df = pd.DataFrame(sequence_data)

    # Write to Excel file
    try:
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"Successfully extracted {len(sequence_data)} sequences for chain {target_chain}")
        print(f"Sequences have been written to {output_file}")
        return True
    except Exception as e:
        print(f"Error writing to Excel file: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract protein sequences from PDB files')
    parser.add_argument('--folder', required=True, help='Folder path containing PDB files')
    parser.add_argument('--chain', required=True, help='Target chain (e.g., A, B, C)')
    parser.add_argument('--output', help='Output Excel file name')
    
    args = parser.parse_args()
    
    # Set default output filename if not provided
    if not args.output:
        args.output = f"chain_{args.chain.upper()}_sequences_aa.xlsx"
    
    success = extract_sequences(args.folder.strip(), args.chain.strip().upper(), args.output)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
