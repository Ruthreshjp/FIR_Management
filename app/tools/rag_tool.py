import os
import json
import logging
import re
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoFIR_RAG")

# ----------------- Fallback Keyword Overlap Engine -----------------
def keyword_search_fallback(query: str, dataset: list, top_k: int = 3) -> list:
    """
    Pure Python keyword matching score engine.
    Ranks dataset items by keyword overlaps and term frequency.
    """
    logger.info("Using keyword-overlap search engine (RAG Fallback).")
    query_tokens = set(re.findall(r'\w+', query.lower()))
    
    results = []
    for item in dataset:
        score = 0
        
        # Match Offense name
        offense_words = re.findall(r'\w+', item["offense"].lower())
        for w in offense_words:
            if w in query_tokens:
                score += 5.0  # High weight for main offense title words
                
        # Match Keywords list
        for kw in item.get("keywords", []):
            kw_clean = kw.lower()
            if kw_clean in query:  # Substring match in raw query
                score += 3.0
            if kw_clean in query_tokens:  # Token match
                score += 2.0
                
        # Match Description words
        desc_words = re.findall(r'\w+', item["description"].lower())
        for dw in desc_words:
            if dw in query_tokens:
                score += 0.5  # Lower weight for description words
                
        if score > 0:
            results.append((score, item))
            
    # Sort descending by score
    results.sort(key=lambda x: x[0], reverse=True)
    ranked_items = [item for _, item in results[:top_k]]
    
    # If no matches, return top default sections (e.g. Theft and Cheating)
    if not ranked_items:
        ranked_items = dataset[:2]
        
    return ranked_items

# ----------------- Attempt ChromaDB + SentenceTransformers Setup -----------------
CHROMA_AVAILABLE = False
vector_db = None
embedding_model = None

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    pass

class SemanticRAG:
    def __init__(self):
        self.dataset_path = os.path.join(settings.DATA_DIR, "ipc_bns_dataset.json")
        self.dataset = self.load_dataset()
        self.use_chroma = False
        
        if CHROMA_AVAILABLE:
            try:
                logger.info("Initializing SentenceTransformer model 'all-MiniLM-L6-v2'...")
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                
                # In-memory ephemeral Chroma client
                self.chroma_client = chromadb.EphemeralClient()
                self.collection = self.chroma_client.create_collection("legal_sections")
                
                # Index dataset
                documents = []
                embeddings = []
                metadatas = []
                ids = []
                
                for idx, item in enumerate(self.dataset):
                    doc_text = f"{item['offense']}: {item['description']} Justification: {item['justification']}"
                    documents.append(doc_text)
                    metadatas.append({
                        "offense": item["offense"],
                        "ipc_section": item["ipc_section"],
                        "bns_section": item["bns_section"],
                        "justification": item["justification"]
                    })
                    ids.append(str(idx))
                    
                # Compute embeddings in batch
                logger.info("Generating semantic embeddings for legal database...")
                emb_list = self.model.encode(documents).tolist()
                
                self.collection.add(
                    ids=ids,
                    embeddings=emb_list,
                    metadatas=metadatas,
                    documents=documents
                )
                self.use_chroma = True
                logger.info("ChromaDB vector store initialized successfully!")
                
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB or embeddings: {str(e)}. Defaulting to fallback mode.")
                self.use_chroma = False

    def load_dataset(self):
        if os.path.exists(self.dataset_path):
            try:
                with open(self.dataset_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        # Hardcoded tiny backup dataset
        return [
            {
                "offense": "Theft",
                "ipc_section": "IPC Section 379",
                "bns_section": "BNS Section 303",
                "keywords": ["theft", "stolen", "snatched"],
                "description": "Theft. Mapped from IPC Section 379 to BNS Section 303.",
                "justification": "Dishonest removal of movable property without consent."
            }
        ]

    def search(self, query: str, top_k: int = 3) -> list:
        """
        Searches the legal database. Utilizes Chroma semantic search or keyword fallback.
        Returns a list of matching items.
        """
        if self.use_chroma:
            try:
                query_vector = self.model.encode([query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_vector,
                    n_results=top_k
                )
                
                retrieved_items = []
                metas = results.get("metadatas", [[]])[0]
                for meta in metas:
                    retrieved_items.append({
                        "offense": meta["offense"],
                        "ipc_section": meta["ipc_section"],
                        "bns_section": meta["bns_section"],
                        "justification": meta["justification"],
                        "description": ""
                    })
                if retrieved_items:
                    return retrieved_items
            except Exception as e:
                logger.error(f"Semantic search failed: {str(e)}. Using keyword search fallback.")
                
        return keyword_search_fallback(query, self.dataset, top_k)

# Global Instance of RAG
rag_instance = SemanticRAG()

def search_legal_sections(query: str, top_k: int = 3) -> list:
    """
    Exposed function to search legal sections.
    """
    return rag_instance.search(query, top_k)
