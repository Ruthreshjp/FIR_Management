import os
import pandas as pd
import re

def fix_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    # Fix common mangled UTF-8 chars and newlines
    text = text.replace("â€”", "—").replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')
    text = text.replace('\r\n', '\n').replace('\\r\\n', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_section_ipc(url):
    if pd.isna(url):
        return ""
    match = re.search(r'section-(\w+)', str(url))
    if match:
        return match.group(1).upper()
    return ""

def clean_ipc(input_path, output_path):
    print(f"Loading {input_path}...")
    try:
        df = pd.read_csv(input_path, encoding='utf-8')
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        return

    # Create Unified Schema
    clean_df = pd.DataFrame()
    clean_df['Act'] = 'IPC'  # Defaulting to IPC
    clean_df['Section'] = df['URL'].apply(extract_section_ipc)
    clean_df['Offense_Title'] = df['Offense'].apply(fix_text)
    clean_df['Description'] = df['Description'].apply(fix_text)
    clean_df['Punishment'] = df['Punishment'].apply(fix_text)
    clean_df['Cognizable'] = df['Cognizable'].apply(fix_text)
    clean_df['Bailable'] = df['Bailable'].apply(fix_text)

    # Prune garbage data
    initial_count = len(clean_df)
    
    # Condition: Must have a Section number and at least 15 chars in Description or Offense
    clean_df = clean_df[clean_df['Section'] != ""]
    clean_df = clean_df[
        (clean_df['Description'].str.len() > 15) | 
        (clean_df['Offense_Title'].str.len() > 15)
    ]
    
    # Deduplicate by Act + Section
    clean_df = clean_df.drop_duplicates(subset=['Act', 'Section'], keep='first')
    
    final_count = len(clean_df)
    print(f"IPC Cleanup: Dropped {initial_count - final_count} garbage/duplicate rows. Total remaining: {final_count}")
    
    clean_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Saved to {output_path}")

def clean_bns(input_path, output_path):
    print(f"\nLoading {input_path}...")
    try:
        df = pd.read_csv(input_path, encoding='utf-8')
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        return

    # Find the offense title column (Section _name or Section_name)
    section_name_col = next((c for c in df.columns if 'Section_name' in c or 'Section _name' in c), None)

    # Create Unified Schema
    clean_df = pd.DataFrame()
    clean_df['Act'] = 'BNS'
    clean_df['Section'] = df['Section'].apply(lambda x: str(x).strip() if not pd.isna(x) else "")
    clean_df['Offense_Title'] = df[section_name_col].apply(fix_text) if section_name_col else ""
    clean_df['Description'] = df['Description'].apply(fix_text)
    clean_df['Punishment'] = ""
    clean_df['Cognizable'] = ""
    clean_df['Bailable'] = ""

    # Prune garbage data
    initial_count = len(clean_df)
    
    clean_df = clean_df[clean_df['Section'] != ""]
    clean_df = clean_df[
        (clean_df['Description'].str.len() > 15) | 
        (clean_df['Offense_Title'].str.len() > 15)
    ]
    
    # Deduplicate by Act + Section
    clean_df = clean_df.drop_duplicates(subset=['Act', 'Section'], keep='first')
    
    final_count = len(clean_df)
    print(f"BNS Cleanup: Dropped {initial_count - final_count} garbage/duplicate rows. Total remaining: {final_count}")
    
    clean_df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Saved to {output_path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    
    ipc_input = os.path.join(raw_dir, "FIR_DATASET.csv")
    bns_input = os.path.join(raw_dir, "bns_sections.csv")
    
    ipc_output = os.path.join(raw_dir, "ipc_special_acts_clean.csv")
    bns_output = os.path.join(raw_dir, "bns_sections_clean.csv")
    
    print("=== STARTING DATASET RESTRUCTURING ===\n")
    clean_ipc(ipc_input, ipc_output)
    clean_bns(bns_input, bns_output)
    print("\n=== RESTRUCTURING COMPLETE ===")

if __name__ == "__main__":
    main()
