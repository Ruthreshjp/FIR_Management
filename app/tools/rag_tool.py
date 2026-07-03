import os
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoFIR_RAG")

# ----------------- Fallback Keyword Overlap Engine -----------------
def keyword_search_fallback(query: str, dataset: list, top_k: int = 10) -> list:
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
        offense = item.get("offense") or item.get("section_name") or ""
        offense_words = re.findall(r'\w+', offense.lower())
        for w in offense_words:
            if w in query_tokens:
                score += 5.0  # High weight for main offense title words
                
        # Match Description words
        description = item.get("description", "")
        desc_words = re.findall(r'\w+', description.lower())
        for dw in desc_words:
            if dw in query_tokens:
                score += 0.5  # Lower weight for description words
                
        if score > 0:
            results.append((score, item))
            
    # Sort descending by score
    results.sort(key=lambda x: x[0], reverse=True)
    ranked_items = [item for _, item in results[:top_k]]
    
    if not ranked_items:
        ranked_items = dataset[:2]
        
    return ranked_items

# ----------------- ChromaDB Setup -----------------
CHROMA_AVAILABLE = False

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    pass

class SemanticRAG:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dataset_path = os.path.join(base_dir, "data", "ipc_bns_dataset.json")
        self.chroma_path = os.path.join(base_dir, "data", "chroma_db")
        self.dataset = self.load_dataset()
        self.use_chroma = False
        
        if CHROMA_AVAILABLE:
            try:
                logger.info("Connecting to Persistent ChromaDB at data/chroma_db...")
                # We do NOT create embeddings on the fly anymore. We assume rebuild_chromadb.py was run.
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
                self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
                self.collection = self.chroma_client.get_collection("legal_sections")
                self.use_chroma = True
                logger.info(f"Connected to ChromaDB successfully. Collection has {self.collection.count()} items.")
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB or embeddings: {str(e)}. Defaulting to fallback mode.")
                self.use_chroma = False

    def load_dataset(self):
        if os.path.exists(self.dataset_path):
            try:
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def search(self, query: str, top_k: int = 10) -> list:
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
                    # Map the raw metadata back into the format expected by the LLM
                    retrieved_items.append({
                        "act": meta.get("act"),
                        "section_number": meta.get("section_number"),
                        "offense": meta.get("offense"),
                        "cognizable": meta.get("cognizable"),
                        "bailable": meta.get("bailable"),
                        "punishment": meta.get("punishment"),
                        "corresponding_bns": meta.get("corresponding_bns"),
                        "corresponding_ipc": meta.get("corresponding_ipc")
                    })
                if retrieved_items:
                    return retrieved_items
            except Exception as e:
                logger.error(f"Semantic search failed: {str(e)}. Using keyword search fallback.")
                
        return keyword_search_fallback(query, self.dataset, top_k)

# Global Instance of RAG
rag_instance = SemanticRAG()

def search_legal_sections(query: str, top_k: int = 10) -> list:
    """
    Exposed function to search legal sections.
    """
    return rag_instance.search(query, top_k)
