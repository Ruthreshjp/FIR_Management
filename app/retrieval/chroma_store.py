import os
import json
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi

# We will use lazy initialization to prevent blocking on import
chroma_client = None
collection = None
bm25_index = None
corpus_docs = []
corpus_metas = []
_INITIALIZED = False

def get_collection():
    global chroma_client, collection
    if collection is None:
        persist_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chroma_db")
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        collection = chroma_client.get_or_create_collection(name="ipc_bns_laws")
    return collection
    
def initialize_chroma_store():
    global _INITIALIZED, bm25_index, corpus_docs, corpus_metas
    if _INITIALIZED:
        return
        
    c = get_collection()
    
    # Initialize BM25 index from existing chroma data
    try:
        all_data = c.get(include=["documents", "metadatas"])
        if all_data and all_data.get("documents"):
            corpus_docs = all_data["documents"]
            corpus_metas = all_data["metadatas"]
            tokenized_corpus = [doc.lower().split(" ") for doc in corpus_docs]
            bm25_index = BM25Okapi(tokenized_corpus)
            _INITIALIZED = True
            return
    except Exception as e:
        print(f"BM25 initialization error from chroma: {e}")

    # Fallback: Load dataset from data directory
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
        c.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        corpus_docs = documents
        corpus_metas = metadatas
        tokenized_corpus = [doc.lower().split(" ") for doc in corpus_docs]
        bm25_index = BM25Okapi(tokenized_corpus)
        
    _INITIALIZED = True

def search_legal_sections(query: str, top_k: int = 10) -> list:
    """Queries the ChromaDB collection using hybrid search (Vector + BM25)."""
    initialize_chroma_store()
    try:
        c = get_collection()
        
        # 1. Vector Search
        vector_results = c.query(
            query_texts=[query],
            n_results=top_k * 2
        )
        
        vector_metas = vector_results.get('metadatas', [[]])[0]
        
        # 2. BM25 Keyword Search
        bm25_metas = []
        if bm25_index:
            tokenized_query = query.lower().split(" ")
            bm25_scores = bm25_index.get_scores(tokenized_query)
            # Get top_k * 2 indices
            top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k*2]
            for idx in top_indices:
                if bm25_scores[idx] > 0:
                    bm25_metas.append(corpus_metas[idx])
                    
        # 3. Combine and Deduplicate
        seen_keys = set()
        final_results = []
        
        # We alternate picking from bm25 and vector to mix exact matches and semantic matches
        max_len = max(len(bm25_metas), len(vector_metas))
        for i in range(max_len):
            if i < len(bm25_metas):
                meta = bm25_metas[i]
                key = f"{meta.get('act')}_{meta.get('section_number')}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    final_results.append(meta)
                    
            if len(final_results) >= top_k:
                break
                
            if i < len(vector_metas):
                meta = vector_metas[i]
                key = f"{meta.get('act')}_{meta.get('section_number')}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    final_results.append(meta)
                    
            if len(final_results) >= top_k:
                break
                
        return final_results
    except Exception as e:
        print(f"Hybrid search error: {e}")
        return []

