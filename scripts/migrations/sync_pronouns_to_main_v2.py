import sqlite3
from core.config import DB_PATH

import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def sync():
    main_db = DB_PATH
    fix_db = 'pronoun_fixes.sqlite'
    
    conn_main = sqlite3.connect(main_db)
    conn_fix = sqlite3.connect(fix_db)
    
    c_main = conn_main.cursor()
    c_fix = conn_fix.cursor()
    
    print(f"Đang đọc dữ liệu từ {fix_db}...")
    # Lấy text trước, id sau để khớp với SQL: SET translated_text = ?, WHERE id = ?
    c_fix.execute("SELECT translated_text, id FROM records")
    data = c_fix.fetchall()
    
    if data:
        print(f"Bắt đầu đồng bộ lại {len(data)} câu vào {main_db}...")
        c_main.executemany("UPDATE records SET translated_text = ?, status = 1 WHERE id = ?", data)
        conn_main.commit()
        print("Đồng bộ hoàn tất (V2).")
    else:
        print("Không có dữ liệu để đồng bộ.")
        
    conn_main.close()
    conn_fix.close()

if __name__ == "__main__":
    sync()
