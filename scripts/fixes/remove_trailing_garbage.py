import sqlite3
from core.config import DB_PATH

import re
import sys
import time

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def cleanup():
    db_path = DB_PATH
    conn = None
    try:
        # Tăng timeout để tránh database is locked
        conn = sqlite3.connect(db_path, timeout=30)
        c = conn.cursor()
        
        c.execute("SELECT id, translated_text FROM records WHERE translated_text LIKE '%.%'")
        rows = c.fetchall()
        
        garbage_words = [
            'của anh ấy', 'anh ấy', 'của cô ấy', 'cô ấy', 'của tôi', 'tôi',
            'của nó', 'nó', 'chúng tôi', 'chúng ta', 'bạn', 'họ'
        ]
        
        words_pipe = '|'.join(garbage_words)
        pattern = rf'\.(\s*)(?:{words_pipe})+\s*(?=\[COMMENT|$)'
        regex = re.compile(pattern, re.IGNORECASE)
        
        updated_records = []
        fixed_count = 0
        
        for row_id, trans in rows:
            new_trans = regex.sub('.', trans)
            if new_trans != trans:
                new_trans = new_trans.replace('..', '.')
                updated_records.append((new_trans, row_id))
                fixed_count += 1
        
        if updated_records:
            print(f"Đang cập nhật {len(updated_records)} dòng...")
            # Chia nhỏ batch để tránh lock lâu
            batch_size = 5000
            for i in range(0, len(updated_records), batch_size):
                batch = updated_records[i : i + batch_size]
                c.executemany("UPDATE records SET translated_text = ? WHERE id = ?", batch)
                conn.commit()
                print(f"Đã xong {min(i + batch_size, len(updated_records))}...")
            print("Hoàn tất cleanup.")
        else:
            print("Không tìm thấy dòng nào cần cleanup.")
            
    except sqlite3.Error as e:
        print(f"Lỗi SQLite: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    cleanup()
