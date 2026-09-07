import csv
import os

SYNONYM_MAP = {
    "theft": ["stealing", "stolen", "snatching", "robbed", "took", "missing", "looted", "bike theft", "car theft"],
    "murder": ["killed", "dead", "homicide", "slaughtered", "assassinated"],
    "hurt": ["hit", "punch", "slap", "beat", "assault", "injured", "bruise", "bleeding", "cut", "stabbed"],
    "weapon": ["knife", "gun", "sword", "rod", "pistol", "sharp object"],
    "animal": ["cow", "dog", "cat", "cattle", "pet", "puppy", "street dog", "bull"],
    "cyber": ["online fraud", "otp", "phishing", "upi", "bank fraud", "internet banking", "anydesk", "password", "pin"],
    "fraud": ["fake", "forged", "cheating", "scam", "impersonation", "counterfeit"],
    "women": ["rape", "molest", "domestic violence", "harassment", "dowry", "wife", "modesty"]
}

def get_keywords(text):
    if not text:
        return ""
    text_lower = text.lower()
    keywords = set()
    for category, synonyms in SYNONYM_MAP.items():
        if category in text_lower or any(syn in text_lower for syn in synonyms):
            keywords.update(synonyms)
    return ", ".join(keywords)

def process_csv(input_path, output_path, is_bns=False):
    print(f"Processing {input_path}...")
    with open(input_path, 'r', encoding='utf-8', errors='replace') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        if "Keywords" not in fieldnames:
            fieldnames.append("Keywords")
        
        rows = []
        for row in reader:
            desc = row.get("Description", "")
            
            offense = ""
            if is_bns:
                section_name_key = next((k for k in row.keys() if 'Section _name' in k or 'Section_name' in k), None)
                if section_name_key:
                    offense = row.get(section_name_key, "")
            else:
                offense = row.get("Offense", "")
                
            combined_text = f"{desc} {offense}"
            row["Keywords"] = get_keywords(combined_text)
            rows.append(row)
            
    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved to {output_path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    
    bns_csv = os.path.join(raw_dir, "bns_sections.csv")
    ipc_csv = os.path.join(raw_dir, "FIR_DATASET.csv")
    
    # We will process and overwrite the original files to add the Keywords column
    process_csv(bns_csv, bns_csv, is_bns=True)
    process_csv(ipc_csv, ipc_csv, is_bns=False)
    
if __name__ == "__main__":
    main()
