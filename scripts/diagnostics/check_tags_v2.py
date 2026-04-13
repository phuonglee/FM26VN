import sqlite3
from core.config import DB_PATH

import re
import sys

# Đảm bảo in được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def check_tags():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tags = ['[%person#4-I]', '[%person#2-you]', '[%male#3-him]', '[%male#1-he]']
    
    print("--- KIỂM TRA SỰ TỒN TẠI CỦA THẺ (TOÀN BỘ DB) ---")
    for tag in tags:
        # Kiểm tra trong bản dịch
        c.execute("SELECT id FROM records WHERE translated_text LIKE ?", (f'%{tag}%',))
        t_rows = c.fetchall()
        
        # Kiểm tra trong bản gốc
        c.execute("SELECT id FROM records WHERE english_text LIKE ?", (f'%{tag}%',))
        e_rows = c.fetchall()
        
        print(f"Thẻ {tag:20} | Dịch: {len(t_rows)} dòng | Gốc: {len(e_rows)} dòng")
        
        # Nếu có trong gốc nhưng không có trong dịch (nghĩa là chưa dịch hoặc đã dịch nhưng mất thẻ)
        if len(e_rows) > 0 and len(t_rows) == 0:
            c.execute("SELECT id, translated_text FROM records WHERE english_text LIKE ? AND status = 1 LIMIT 3", (f'%{tag}%',))
            samples = c.fetchall()
            if samples:
                print("  Mẫu các dòng đã dịch nhưng có thể đã MẤT thẻ:")
                for rid, trans in samples:
                    print(f"    ID {rid}: {trans[:100]}...")
    
    conn.close()

if __name__ == "__main__":
    check_tags()
