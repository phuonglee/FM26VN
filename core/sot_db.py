import sys
import os
from pathlib import Path

# Thêm dự án gốc vào sys.path
root = Path(__file__).parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

import chromadb
from chromadb.utils import embedding_functions

class SOTDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            from core.config import PROJECT_ROOT
            db_path = str(PROJECT_ROOT / "data" / "vectordb")
            
        os.makedirs(db_path, exist_ok=True)
        
        # Liên kết tới ChromaDB local
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Sử dụng model embedding local (Miễn phí)
        # Model 'all-MiniLM-L6-v2' nhẹ và hiệu quả cho tìm kiếm ngữ cảnh
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Khởi tạo collection chính cho Rules và Glossary
        self.collection = self.client.get_or_create_collection(
            name="fm26_knowledge_base",
            embedding_function=self.emb_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def add_rules(self, documents, metadatas, ids):
        """Thêm các quy tắc hoặc thuật ngữ vào SOT."""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, text, n_results=5):
        """Tìm kiếm các tri thức liên quan nhất."""
        results = self.collection.query(
            query_texts=[text],
            n_results=n_results
        )
        return results

if __name__ == "__main__":
    # Test khởi tạo
    try:
        db = SOTDatabase()
        print("[*] SOT Database initialized successfully.")
    except Exception as e:
        print(f"[!] Error: {e}")
