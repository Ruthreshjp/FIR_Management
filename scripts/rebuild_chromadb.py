import os
import sys
import json
import chromadb

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
        
        # The text that gets embedded — rich context for semantic search
        embed_text = (
            f"{act} Section {sec_num}: {offense}. {description[:500]}"
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
        }
        
        documents.append(embed_text)
        metadatas.append(meta)
        ids.append(f"{act}_{sec_num}_{i}")

    # Add in batches of 100 to avoid memory issues
    batch_size = 100
    print(f"Starting ingestion of {len(documents)} documents in batches of {batch_size}...")
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
        ("murder stabbing intentional killing", "Should return IPC 302 / BNS 103"),
        ("conspiracy pre-planned criminal agreement", "Should return IPC 120B"),
        ("common intention several persons joint act", "Should return IPC 34"),
        ("unlawful assembly five or more persons", "Should return IPC 149 / BNS 190"),
        ("causing disappearance of evidence absconding", "Should return IPC 201 / BNS 238"),
        ("grievous hurt dangerous weapon knife", "Should return IPC 326 / BNS 118"),
        ("theft stolen property dishonest removal", "Should return IPC 379 / BNS 303"),
        ("rape sexual assault woman", "Should return IPC 376 / BNS 64"),
    ]

    print("\n--- Running Verification Queries ---")
    for query, expected in test_queries:
        results = collection.query(query_texts=[query], n_results=3)
        hits = [
            f"{m.get('act')} {m.get('section_number')} — {m.get('offense')}"
            for m in results['metadatas'][0]
        ]
        print(f"\nQuery: '{query}'")
        print(f"Expected: {expected}")
        print(f"Got: {hits}")

if __name__ == "__main__":
    main()
