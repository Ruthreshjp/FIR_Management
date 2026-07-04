import os
import sys
import re
import json
import chromadb

# Sections that are definitions only, not charges
DEFINITION_ONLY = {
    # BNS definition sections
    '101',   # BNS Murder definition -> use BNS 103 for charges
    # IPC definition sections
    '299',   # IPC Culpable homicide definition
    '300',   # IPC Murder definition -> use IPC 302
    '375',   # IPC Rape definition -> use IPC 376
    '141',   # IPC Unlawful assembly definition -> use IPC 143/149
    '120A',  # IPC Conspiracy definition -> use IPC 120B
    '378',   # IPC Theft definition -> use IPC 379
    '383',   # IPC Extortion definition -> use IPC 384
    '390',   # IPC Robbery definition -> use IPC 392
}

def clean_ipc_description(text: str, section_num: str) -> str:
    """Strip the standard preamble noise from scraped IPC descriptions."""
    if not text:
        return ""
    # Remove the standard preamble
    patterns = [
        rf"Description of IPC Section {re.escape(section_num)}\s*",
        rf"According to section {re.escape(section_num)} of [Ii]ndian penal code,?\s*",
        rf"IPC {re.escape(section_num)} in Simple Words\s*.*$",  # remove end summary
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.DOTALL)
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chroma_dir = os.path.join(base_dir, "data", "chroma_db")
    dataset_path = os.path.join(base_dir, "data", "ipc_bns_dataset.json")
    
    if not os.path.exists(dataset_path):
        print(f"Error: dataset not found at {dataset_path}")
        sys.exit(1)

    print(f"Initializing PersistentClient at {chroma_dir}...")
    client = chromadb.PersistentClient(path=chroma_dir)

    # Delete existing collection and rebuild fresh
    try:
        client.delete_collection("legal_sections")
        print("Deleted old collection 'legal_sections'.")
    except Exception:
        pass

    collection = client.create_collection(
        name="legal_sections",
        metadata={"hnsw:space": "cosine"}
    )

    with open(dataset_path, "r", encoding="utf-8") as f:
        sections = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for i, s in enumerate(sections):
        act = s.get("act", "")
        sec_num = str(s.get("section_number", ""))
        offense = s.get("offense") or s.get("section_name", "")
        description = s.get("description", "") or ""
        
        # FIX 2: Clean IPC descriptions — strip scraped preamble noise
        if act == "IPC":
            description = clean_ipc_description(description, sec_num)
        
        # FIX 1: Deprioritize definition-only sections in embedding text
        is_definition = sec_num in DEFINITION_ONLY
        # Also check if the dataset entry itself is flagged
        if s.get("is_definition_only"):
            is_definition = True
            
        if is_definition:
            embed_text = (
                f"DEFINITION ONLY — not a charge section. "
                f"{act} Section {sec_num}: {offense}. "
                f"{description[:300]}"
            )
        else:
            embed_text = (
                f"{act} Section {sec_num}: {offense}. "
                f"{description[:500]}"
            )
        
        # Clean metadata — ChromaDB only accepts str/int/float/bool
        meta = {
            "act": act,
            "section_number": sec_num,
            "offense": str(offense or ""),
            "cognizable": str(s.get("cognizable") or ""),
            "bailable": str(s.get("bailable") or ""),
            "punishment": str(s.get("punishment") or "")[:200],
            "corresponding_bns": str(
                (s.get("corresponding_section") or {}).get("BNS") or ""
            ),
            "corresponding_ipc": str(
                (s.get("corresponding_section") or {}).get("IPC") or ""
            ),
            "is_definition": "True" if is_definition else "False",
        }
        
        documents.append(embed_text)
        metadatas.append(meta)
        ids.append(f"{act}_{sec_num}_{i}")

    # Add in batches of 100 to avoid memory issues
    batch_size = 100
    def_count = sum(1 for m in metadatas if m["is_definition"] == "True")
    print(f"Starting ingestion of {len(documents)} documents ({def_count} definition-only) in batches of {batch_size}...")
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"Added batch {i//batch_size + 1}")

    print(f"\nChromaDB rebuilt. Total documents: {collection.count()}")

    # Verify with test queries
    test_queries = [
        ("murder stabbing intentional killing punishment", "Should return IPC 302 / BNS 103 (not BNS 101)"),
        ("conspiracy pre-planned criminal agreement", "Should return IPC 120B"),
        ("common intention several persons joint act", "Should return IPC 34 / BNS 3(5)"),
        ("unlawful assembly five or more persons", "Should return IPC 149 / BNS 190"),
        ("causing disappearance of evidence absconding", "Should return IPC 201 / BNS 238"),
        ("grievous hurt dangerous weapon knife", "Should return IPC 326 / BNS 118"),
        ("theft stolen property dishonest removal punishment", "Should return IPC 379 / BNS 303 (not IPC 378)"),
        ("rape sexual assault punishment woman", "Should return IPC 376 / BNS 64 (not IPC 375)"),
    ]

    print("\n--- Running Verification Queries ---")
    for query, expected in test_queries:
        results = collection.query(query_texts=[query], n_results=5)
        hits = [
            f"{m.get('act')} {m.get('section_number')} — {m.get('offense')} [def:{m.get('is_definition','?')}]"
            for m in results['metadatas'][0]
        ]
        print(f"\nQuery: '{query}'")
        print(f"Expected: {expected}")
        for h in hits:
            print(f"  {h}")

if __name__ == "__main__":
    main()
