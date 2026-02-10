# DESCRIPTION:
# This script is the final "Lab-Ready" formatter. It cleans up complex, 
# technical PDB identifiers (e.g., removing MPNN model numbers and project 
# prefixes) into short, readable names for synthesis orders. It also 
# integrates tag placement recommendations and calculates final AA lengths.
#
# SETUP & DIRECTORY STRUCTURE:
# 1. Script Location: Run from the Project Root.
# 2. Input: Requires 'chain_B_sequences_aa.xlsx' (from the extraction script).
# 3. Optional: If a 'Tag' column is added to the input Excel, it will be 
#    merged into the final 'Name'.
# 4. Output: Produces 'cleaned_sequences.csv', the final order form.
#
# HOW TO EXECUTE:
# Run from terminal: 'python script_name.py'
# Ensure 'pandas', 'openpyxl', and 're' are installed in your environment.

import pandas as pd
import re

def clean_pdb_id(name):
    """
    Clean PDB ID by:
    1. Removing everything before RXFP1
    2. Replacing GDNNGWSL_outside_small_ with cons_small_
    3. Replacing other GDNNGWSL variants with cons_
    4. Removing MPNN model suffixes
    """
    # Remove everything before RXFP1 (including the underscore after the numbers)
    if 'RXFP1' in name:
        # Find RXFP1 and keep everything from RXFP1 onwards
        rxfp1_index = name.find('RXFP1')
        name = name[rxfp1_index:]
    
    # Replace GDNNGWSL variants with cons_ (keeping _small when present)
    name = name.replace('ag_GDNNGWSL_outside_small_', 'cons_small_')
    name = name.replace('ag_GDNNGWSL_small_', 'cons_small_')
    name = name.replace('ag_GDNNGWSL_', 'cons_')
    
    # Remove MPNN model suffixes
    pattern = r'_mpnn\d+_model\d+.*$'
    cleaned_name = re.sub(pattern, '', name)
    
    return cleaned_name

def process_sequence_file(input_file='chain_B_sequences_aa.xlsx', output_file='cleaned_sequences.csv'):
    """
    Process the sequence file to clean names and combine with tag information
    """
    try:
        # Load the Excel file
        df = pd.read_excel(input_file)
        
        # Validate required columns
        required_columns = ['PDB_ID', 'Sequence']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean the PDB_ID names
        df['Cleaned_PDB_ID'] = df['PDB_ID'].apply(clean_pdb_id)
        
        # Handle Tag column - check if it exists, if not create empty
        if 'Tag' not in df.columns:
            print("Warning: 'Tag' column not found. Creating empty tag column.")
            df['Tag'] = ''
        
        # Fill any NaN values in Tag column
        df['Tag'] = df['Tag'].fillna('')
        
        # Combine cleaned PDB_ID with Tag (only add underscore if Tag is not empty)
        df['Name'] = df.apply(lambda row: 
            row['Cleaned_PDB_ID'] + ('_' + str(row['Tag']) if str(row['Tag']).strip() else ''), 
            axis=1)
        
        # Calculate sequence lengths
        df['Length'] = df['Sequence'].str.len()
        
        # Create final output dataframe
        output_df = pd.DataFrame({
            'Name': df['Name'],
            'Tag Terminus': df['Tag'],
            'Length': df['Length'],
            'Insert sequence': df['Sequence']
        })
        
        # Save to CSV
        output_df.to_csv(output_file, index=False)
        
        print(f"Processing complete! Results saved to {output_file}")
        print(f"Processed {len(output_df)} sequences")
        
        # Display sample results
        print("\nSample cleaned names:")
        for i, (original, cleaned) in enumerate(zip(df['PDB_ID'].head(10), df['Name'].head(10))):
            print(f"{i+1}. {original}")
            print(f"   → {cleaned}\n")
        
        return output_df
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

# Run the processing
if __name__ == "__main__":
    result = process_sequence_file()


