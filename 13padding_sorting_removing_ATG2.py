import pandas as pd

# Read the CSV file
input_file = 'RXFP1_ago.csv'
output_file = 'processed_RXFP1_ago.csv'

try:
    # Load the CSV file
    df = pd.read_csv(input_file)
    
    # Display current columns to verify structure
    print("Current columns in the file:")
    print(df.columns.tolist())
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Extract Tag Terminus from the suffix in 'Name' column (after last underscore)
    df['Tag Terminus'] = df['Name'].apply(lambda x: x.split('_')[-1] if isinstance(x, str) else '')
    
    # Calculate Length from the number of characters in 'Insert sequence'
    df['Length'] = df['Insert sequence'].apply(lambda x: len(x) if isinstance(x, str) else 0)
    
    print(f"\nExtracted Tag Terminus and calculated Length:")
    print(df[['Name', 'Tag Terminus', 'Length', 'Insert sequence']].head())
    
    # Load padding sequence
    try:
        with open('DNA_Padding.txt', 'r') as f:
            padding_sequence = f.read().strip()
        print(f"\nLoaded padding sequence: {len(padding_sequence)} bp")
    except FileNotFoundError:
        print("Warning: DNA_Padding.txt not found. Using default padding sequence.")
        padding_sequence = "TTGTGTTGCGATAGCCCAGTATGATATTCTAAGGCGTTACGCTGATGAATATTCTACGGAATTGCCATAGGCGTTGAACGCTACACGGACGATACGAATT"[1]
    
    # Process the data for molecular cloning
    # Remove first ATG if present (NdeI processing)
    def process_sequence(seq):
        if isinstance(seq, str) and seq.startswith('ATG'):
            return seq[3:]  # Remove first ATG
        return seq
    
    df['Processed_Sequence'] = df['Insert sequence'].apply(process_sequence)
    
    # Modified tag addition logic - only add His-tag to C-terminal if padding is needed
    # No stop codons for sequences without His-tags (vectors provide them)
    def add_tags(row):
        seq = row['Processed_Sequence']
        terminus = str(row['Tag Terminus']).strip().upper()
        seq_length = len(seq) if isinstance(seq, str) else 0
        needs_padding = seq_length < 300
        
        if terminus == 'N':
            # N-terminal: add stop codon only
            return seq + 'TGA'
        elif terminus == 'C':
            if needs_padding:
                # C-terminal with padding needed: add 6xHIS tag with stop codon
                return seq + 'GGCTCCCACCACCACCACCACCACTGA'
            else:
                # C-terminal without padding needed: no addition (vector provides His-tag and stop codon)
                return seq
        else:
            return seq
    
    df['Tagged_Sequence'] = df.apply(add_tags, axis=1)
    
    # Function to pad sequences to 300 bp minimum
    def pad_sequence(seq):
        if isinstance(seq, str) and len(seq) < 300:
            target_length = 300
            current_length = len(seq)
            padding_needed = target_length - current_length
            
            # Repeat padding sequence as needed to reach target length
            padding_repeats = (padding_needed // len(padding_sequence)) + 1
            full_padding = (padding_sequence * padding_repeats)[:padding_needed]
            
            return seq + full_padding
        return seq
    
    # Apply padding to reach 300 bp minimum
    df['Final_Sequence'] = df['Tagged_Sequence'].apply(pad_sequence)
    
    # Calculate final lengths
    df['Final_Length'] = df['Final_Sequence'].str.len()
    
    # Check which sequences were padded and which got His-tags
    df['Was_Padded'] = df['Tagged_Sequence'].str.len() < 300
    df['Has_His_Tag'] = df.apply(lambda row: 
        str(row['Tag Terminus']).strip().upper() == 'C' and 
        len(row['Processed_Sequence']) < 300, axis=1)
    df['Has_Stop_Codon'] = df.apply(lambda row:
        str(row['Tag Terminus']).strip().upper() == 'N' or
        (str(row['Tag Terminus']).strip().upper() == 'C' and len(row['Processed_Sequence']) < 300), axis=1)
    
    # Create output dataframe
    output_df = pd.DataFrame({
        'Name': df['Name'],
        'Tag_Terminus': df['Tag Terminus'],
        'Original_Length': df['Length'],
        'Tagged_Length': df['Tagged_Sequence'].str.len(),
        'Final_Length': df['Final_Length'],
        'Was_Padded': df['Was_Padded'],
        'Has_His_Tag': df['Has_His_Tag'],
        'Has_Stop_Codon': df['Has_Stop_Codon'],
        'Final_Sequence': df['Final_Sequence'],
        'Complexity': df['Complexity'],
        'Errors': df['Errors'],
        'Warnings': df['Warnings']
    })
    
    # Sort by terminus (N-terminal first)
    output_df['Sort_Key'] = output_df['Tag_Terminus'].str.contains('N', case=False, na=False)
    output_df = output_df.sort_values('Sort_Key', ascending=False).drop('Sort_Key', axis=1)
    
    # Save processed data
    output_df.to_csv(output_file, index=False)
    print(f"\nProcessing complete! Results saved to {output_file}")
    print(f"Processed {len(output_df)} sequences")
    
    # Display summary
    print(f"\nSummary:")
    print(f"N-terminal sequences: {sum(output_df['Tag_Terminus'] == 'N')}")
    print(f"C-terminal sequences: {sum(output_df['Tag_Terminus'] == 'C')}")
    print(f"Sequences that were padded: {sum(output_df['Was_Padded'])}")
    print(f"C-terminal sequences with His-tag: {sum(output_df['Has_His_Tag'])}")
    print(f"C-terminal sequences without His-tag (vector provides): {sum((output_df['Tag_Terminus'] == 'C') & (~output_df['Has_His_Tag']))}")
    print(f"Sequences with stop codon added: {sum(output_df['Has_Stop_Codon'])}")
    print(f"Sequences with errors: {sum(output_df['Complexity'] == 'ERROR')}")
    print(f"Average final length: {output_df['Final_Length'].mean():.1f} bp")
        
except FileNotFoundError:
    print(f"Error: File '{input_file}' not found.")
    print("Please ensure RXFP1_ago.csv is in the current directory.")
except Exception as e:
    print(f"Error processing file: {str(e)}")

