import sqlite3
from core.config import DB_PATH

import re
import sys
from collections import Counter

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def find_tags_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT id, translated_text FROM records WHERE status = 1")
    rows = c.fetchall()
    
    tag_pattern = re.compile(r'\[%([^\]]+)\]')
    suffix_counter = Counter()

    for rid, trans in rows:
        if not trans: continue
        matches = tag_pattern.findall(trans)
        for m in matches:
            if '-' in m:
                suffix = m.split('-')[-1].lower()
                suffix_counter[suffix] += 1

    print("\n--- THỐNG KÊ HẬU TỐ THẺ CÒN SÓT LẠI (SUFFIXES) ---")
    # Lọc ra các hậu tố tiếng Anh phổ biến (đại từ)
    pronoun_keys = ['himself', 'herself', 'themselves', 'yourself', 'myself', 'ours', 'theirs', 'yours', 'it', 'its', 'ourselves', 'itself']
    
    for suffix, count in suffix_counter.most_common():
        # Chỉ in các thẻ có vẻ là đại từ hoặc các thẻ lạ
        if suffix in pronoun_keys or count < 100:
            print(f"  - {suffix}: {count} lần")
            
    conn.close()

if __name__ == "__main__":
    find_tags_stats()
