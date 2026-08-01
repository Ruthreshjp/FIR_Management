import os
import json
import chromadb
from chromadb.config import Settings

# Simple in-memory ChromaDB instance for demonstration purposes
chroma_client = chromadb.Client(Settings(is_persistent=False))
collection_name = "ipc_bns_laws"
collection = chroma_client.get_or_create_collection(name=collection_name)

_INITIALIZED = False

def initialize_chroma_store():
    global _INITIALIZED
    if _INITIALIZED:
        return
    
    # Load dataset from data directory
    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ipc_bns_dataset.json")
    if not os.path.exists(data_path):
        return
        
    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    documents = []
    metadatas = []
    ids = []
    
    for i, item in enumerate(dataset):
        # Create a search document
        offense = item.get('offense', '')
        desc = item.get('description', '')
        keywords = item.get('keywords', [])
        kw_str = ', '.join(keywords) if keywords else ''
        doc = f"{offense} - {desc} - Keywords: {kw_str}"
        documents.append(doc)
        clean_item = {}
        for k, v in item.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                clean_item[k] = v
            else:
                clean_item[k] = str(v)
                
        metadatas.append(clean_item)
        ids.append(f"law_{i}")
        
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    _INITIALIZED = True

def search_legal_sections(query: str, top_k: int = 4) -> list:
    """Queries the ChromaDB collection for matching legal sections."""
    initialize_chroma_store()
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        if not results['metadatas']:
            return []
        return results['metadatas'][0]
    except Exception as e:
        print(f"Chroma search error: {e}")
        return []
