import sqlite3
from core.config import DB_PATH

import os
import sys

# Ensure UTF-8 for console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def extract():
    src_db = DB_PATH
    dst_db = 'pronoun_fixes.sqlite'
    
    if os.path.exists(dst_db):
        os.remove(dst_db)
        
    conn_src = sqlite3.connect(src_db)
    conn_dst = sqlite3.connect(dst_db)
    
    c_src = conn_src.cursor()
    c_dst = conn_dst.cursor()
    
    # Get schema
    c_src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='records'")
    create_sql = c_src.fetchone()[0]
    c_dst.execute(create_sql)
    
    # Define suffixes
    suffixes = ['-he', '-him', '-his', '-she', '-her', '-I', '-me', '-My', '-my', '-mine']
    
    # Build query
    like_clauses = [f"translated_text LIKE '%{s}]%'" for s in suffixes]
    query = f"SELECT * FROM records WHERE status = 1 AND ({' OR '.join(like_clauses)})"
    
    print(f"Đang tìm kiếm các câu chứa đại từ trong Status 1...")
    c_src.execute(query)
    rows = c_src.fetchall()
    
    if rows:
        print(f"Tìm thấy {len(rows)} câu. Đang sao chép sang {dst_db}...")
        placeholders = ', '.join(['?'] * len(rows[0]))
        c_dst.executemany(f"INSERT INTO records VALUES ({placeholders})", rows)
        conn_dst.commit()
    else:
        print("Không tìm thấy câu nào phù hợp.")
        
    conn_src.close()
    conn_dst.close()
    print("Hoàn tất trích xuất.")

if __name__ == "__main__":
    extract()
