import sys
import os
import re
from pathlib import Path

# Thêm dự án gốc vào sys.path
root = Path(__file__).parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from core.sot_db import SOTDatabase

def build_index():
    print("[*] Loading SOT Database...")
    db = SOTDatabase()
    
    # 1. Index rules.md
    rules_path = root / "data" / "rules.md"
    if rules_path.exists():
        print(f"[*] Indexing {rules_path.name}...")
        with open(rules_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Chia thành các section dựa trên header ##
        sections = re.split(r'\n## ', content)
        
        documents = []
        metadatas = []
        ids = []
        
        for i, section in enumerate(sections):
            if i == 0:
                header = "Introduction"
            else:
                header = section.split('\n')[0]
                section = "## " + section
            
            documents.append(section)
            metadatas.append({"source": "rules.md", "section": header})
            ids.append(f"rule_{i}")
            
        db.add_rules(documents, metadatas, ids)
        print(f"[*] Added {len(documents)} rule sections.")

    # 2. Index Golden Records (Xếp hạng cao)
    import sqlite3
    from core.config import DB_PATH
    
    print("[*] Indexing Highly Rated Records (rate >= 0.9) from SQLite...")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Nạp 50,000 câu tinh túy nhất để làm context (Tránh nạp quá nhiều gây chậm retrieval)
        c.execute("SELECT id, english_text, translated_text, rate FROM records WHERE rate >= 0.9 ORDER BY rate DESC LIMIT 50000")
        rows = c.fetchall()
        
        docs = []
        metas = []
        record_ids = []
        
        for row_id, eng, trans, rate in rows:
            # Lưu cặp Anh-Việt làm tri thức
            docs.append(f"English: {eng}\nVietnamese: {trans}")
            metas.append({"source": "database.sqlite", "db_id": row_id, "rate": rate})
            record_ids.append(f"record_{row_id}")
            
        if docs:
            db.add_rules(docs, metas, record_ids)
            print(f"[*] Added {len(docs)} golden records to SOT.")
            
        conn.close()
    except Exception as e:
        print(f"[!] Error reading database: {e}")

    print("[+] SOT Index build complete.")

if __name__ == "__main__":
    build_index()
