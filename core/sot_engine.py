import sys
import os
import re
from pathlib import Path

# Thêm dự án gốc vào sys.path
root = Path(__file__).parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from core.sot_db import SOTDatabase

# Fix lỗi hiển thị tiếng Việt trên Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

class SOTEngine:
    def __init__(self):
        self.db = SOTDatabase()
        
    def query_instruction(self, query_text):
        """
        Tra cứu tri thức và trả về chỉ dẫn dịch thuật rút gọn.
        Đây là "Layer 2" trong chiến lược tiết kiệm chi phí.
        """
        results = self.db.query(query_text, n_results=3)
        
        if not results or not results['documents'][0]:
            return "Không tìm thấy quy tắc cụ thể. Hãy tuân thủ rules.md chung."
            
        instructions = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i]
            source = metadata.get('source', 'Unknown')
            
            # Nếu là từ rules.md, lấy làm chỉ dẫn ưu tiên
            if source == "rules.md":
                instructions.append(f"[RULE] {doc}")
            # Nếu là từ database (Golden Record), lấy làm ví dụ
            elif source == "database.sqlite":
                instructions.append(f"[EXAMPLE] {doc}")
                
        return "\n---\n".join(instructions)

def test_engine():
    engine = SOTEngine()
    
    # Thử nghiệm với từ khóa 'Manager'
    print(f"[*] Querying SOT for: 'Manager'...")
    prompt = engine.query_instruction("Manager")
    print("\n[RESULT FROM SOT]:")
    print(prompt)
    
    print("\n" + "="*50 + "\n")
    
    # Thử nghiệm với một câu cụ thể
    print(f"[*] Querying SOT for representative translation for stadium...")
    prompt = engine.query_instruction("stadium info tag")
    print("\n[RESULT FROM SOT]:")
    print(prompt)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SOT Knowledge Query Tool")
    parser.add_argument("--query", type=str, help="Từ khóa hoặc nội dung cần tra cứu tri thức")
    args = parser.parse_args()
    
    if args.query:
        engine = SOTEngine()
        print(f"[*] Querying SOT for: '{args.query}'...")
        prompt = engine.query_instruction(args.query)
        print("\n[RESULT FROM SOT]:")
        print(prompt)
    else:
        # Chế độ test mặc định nếu không có query
        test_engine()
