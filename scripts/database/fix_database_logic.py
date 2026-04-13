import sqlite3
import sys
import os
from pathlib import Path

# Thêm dự án gốc vào sys.path
root = Path(__file__).parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from core.config import DB_PATH

def fix():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tìm và reset các câu bị bắt lỗi nhầm bởi logic "anh" cũ
    # Lưu ý: feedback cũ là "Phát hiện xưng hô không phù hợp: ['anh']"
    query = "UPDATE records SET rate = 0.0, review_feedback = NULL, status = 1 WHERE review_feedback LIKE ?"
    pattern = "%Phát hiện xưng hô không phù hợp: ['anh']%"
    
    cursor.execute(query, (pattern,))
    count = cursor.rowcount
    
    conn.commit()
    conn.close()
    print(f"[+] Đã reset {count:,} bản ghi bị chấm điểm nhầm.")

if __name__ == "__main__":
    fix()
