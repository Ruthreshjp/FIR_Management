import os
import csv
import json
import re
import chromadb
from chromadb.config import Settings

def fix_text(text):
    if not text:
        return text
    # Fix common mangled UTF-8 chars
    text = text.replace("â€”", "—").replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')
    return text.strip()

SYNONYM_MAP = {
    "theft": ["stealing", "stolen", "snatching", "robbed", "took", "missing", "looted", "bike theft", "car theft"],
    "murder": ["killed", "dead", "homicide", "slaughtered", "assassinated"],
    "hurt": ["hit", "punch", "slap", "beat", "assault", "injured", "bruise", "bleeding", "cut", "stabbed"],
    "weapon": ["knife", "gun", "sword", "rod", "pistol", "sharp object"],
    "animal": ["cow", "dog", "cat", "cattle", "pet", "puppy", "street dog", "bull"],
    "cyber": ["online fraud", "otp", "phishing", "upi", "bank fraud", "internet banking", "anydesk", "password", "pin"],
    "fraud": ["fake", "forged", "cheating", "scam", "impersonation", "counterfeit"],
    "women": ["rape", "molest", "domestic violence", "harassment", "dowry", "wife", "modesty"],
    "accident": ["rash driving", "hit and run", "vehicle", "car", "bike", "truck", "speeding", "negligent", "drunk driving", "fracture", "hospital", "endangering life", "hit by vehicle"],
    "kidnap": ["abduction", "abducted", "kidnapped", "taken away", "held captive", "ransom"]
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

def normalize_status(val):
    if not val:
        return None, None
    val_clean = val.strip().lower()
    if val_clean == "cognizable" or val_clean == "bailable":
        return val.strip().title(), None
    elif val_clean == "non-cognizable" or val_clean == "non-bailable":
        return val.strip().title(), None
    else:
        return "Conditional", val.strip()

def clean_ipc(csv_path, out_json):
    sections = []
    failed = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                act = row.get('Act', 'IPC')
                section_number = row.get('Section', '')
                offense = fix_text(row.get('Offense_Title'))
                description = fix_text(row.get('Description'))
                punishment = fix_text(row.get('Punishment'))
                
                cog_val, cog_notes = normalize_status(row.get('Cognizable'))
                bail_val, bail_notes = normalize_status(row.get('Bailable'))
                
                notes_list = []
                if cog_notes: notes_list.append(f"Cognizable: {cog_notes}")
                if bail_notes: notes_list.append(f"Bailable: {bail_notes}")
                notes = " | ".join(notes_list) if notes_list else None
                
                gen_keywords = get_keywords(f"{description} {offense}")
                
                sections.append({
                    "act": act,
                    "section_number": section_number,
                    "offense": offense,
                    "description": description,
                    "punishment": punishment,
                    "cognizable": cog_val,
                    "bailable": bail_val,
                    "court": None,
                    "source_url": None,
                    "notes": notes,
                    "corresponding_section": None,
                    "keywords": gen_keywords
                })
            except Exception as e:
                print(f"Error parsing IPC row {row.get('Section')}: {e}")
                failed += 1
                
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2)
    return sections, failed

def clean_bns(csv_path, out_json):
    sections = []
    failed = 0
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                act = row.get('Act', 'BNS')
                section_number = row.get('Section', '')
                section_name = fix_text(row.get('Offense_Title'))
                desc = fix_text(row.get('Description', ''))
                
                gen_keywords = get_keywords(f"{desc} {section_name}")
                
                sections.append({
                    "act": act,
                    "section_number": section_number,
                    "chapter": None,
                    "chapter_name": None,
                    "section_name": section_name,
                    "description": desc,
                    "cognizable": None,
                    "bailable": None,
                    "court": None,
                    "source_url": None,
                    "notes": None,
                    "corresponding_section": None,
                    "keywords": gen_keywords
                })
            except Exception as e:
                print(f"Error parsing BNS row {row.get('Section')}: {e}")
                failed += 1
                
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2)
    return sections, failed

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    proc_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    
    ipc_csv = os.path.join(raw_dir, "ipc_special_acts_clean.csv")
    bns_csv = os.path.join(raw_dir, "bns_sections_clean.csv")
    
    # Wait, check if they exist first so we don't break
    if not os.path.exists(ipc_csv):
        print("Clean CSVs not found. Run restructure_datasets.py first!")
        return
        
    print("1. Cleaning IPC data...")
    ipc_data, ipc_failed = clean_ipc(ipc_csv, os.path.join(proc_dir, "ipc_sections.json"))
    
    print("2. Cleaning BNS data...")
    bns_data, bns_failed = clean_bns(bns_csv, os.path.join(proc_dir, "bns_sections.json"))
    
    # MAPPING: Skipped due to lack of reliable structured source
    # No official NCRB or PRS mapping table in CSV format is publicly accessible without a paywall or scraping an SPA.
    mapped_count = 0
    
    print("3. Loading into ChromaDB...")
    # Creating a persistent chroma store in data/chroma_db so it can be queried later
    chroma_db_dir = os.path.join(base_dir, "data", "chroma_db")
    client = chromadb.PersistentClient(path=chroma_db_dir)
    collection = client.get_or_create_collection("legal_sections")
    
    docs = []
    metas = []
    ids = []
    
    for i, item in enumerate(ipc_data + bns_data):
        act = item["act"]
        sec = item["section_number"]
        name = item.get("offense") or item.get("section_name") or "Unknown Offense"
        desc = item["description"] or ""
        keywords = item.get("keywords", "")
        
        doc_text = f"{act} Section {sec}: {name}. {desc} Keywords: {keywords}"
        
        meta = {
            "act": act,
            "section_number": sec,
            "cognizable": item["cognizable"] or "Unknown",
            "bailable": item["bailable"] or "Unknown",
            "keywords": keywords
        }
        
        docs.append(doc_text)
        metas.append(meta)
        ids.append(f"{act}_{sec}_{i}")
        
    # Batch add to chroma to avoid payload size issues
    batch_size = 200
    for i in range(0, len(docs), batch_size):
        collection.add(
            documents=docs[i:i+batch_size],
            metadatas=metas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        
    print("\n=== INGESTION SUMMARY ===")
    print(f"IPC Sections Loaded: {len(ipc_data)} (Failed: {ipc_failed})")
    print(f"BNS Sections Loaded: {len(bns_data)} (Failed: {bns_failed})")
    print(f"Mappings Applied: {mapped_count} (SKIPPED: No reliable structured source available)")
    print(f"Total documents added to ChromaDB: {len(docs)}")

if __name__ == "__main__":
    main()
