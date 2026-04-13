import sqlite3
from core.config import DB_PATH

import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def extract():
    src_db = DB_PATH
    dst_db = 'you_your_fixes.sqlite'
    
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
    
    # Define tags to extract
    # We use a broad search for any tag ending in common English pronouns
    pronoun_suffixes = ['-you', '-your', '-i', '-my', '-me', '-he', '-his', '-she', '-her']
    
    like_clauses = [f"translated_text LIKE '%{s}]%'" for s in pronoun_suffixes]
    query = f"SELECT * FROM records WHERE status = 1 AND ({' OR '.join(like_clauses)})"
    
    print(f"Đang tìm kiếm các câu chứa thẻ đại từ sót lại...")
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
