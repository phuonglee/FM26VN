import sqlite3
from core.config import DB_PATH

import re
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def check_status_3_tags():
    db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check all records with any translated text
    c.execute("SELECT status, translated_text FROM records WHERE translated_text IS NOT NULL AND translated_text != ''")
    rows = c.fetchall()
    
    stats = {}
    pronoun_potential = {'he', 'she', 'it', 'him', 'her', 'they', 'them', 'we', 'us', 'me', 'my', 'his', 'hers', 'their', 'our', 'your', 'yours', 'himself', 'herself', 'itself', 'themselves', 'ourselves', 'myself', 'yourself', 'mine', 'theirs', 'ours'}

    for status, text in rows:
        matches = re.findall(r'\[%[^\]]+-([a-zA-Z0-9_]+)\]', text)
        for m in matches:
            suffix = m.lower()
            if suffix in pronoun_potential:
                if status not in stats: stats[status] = {}
                stats[status][suffix] = stats[status].get(suffix, 0) + 1

    print("--- THỐNG KÊ THẺ ĐẠI TRỪ TRONG CÁC TRẠNG THÁI ---")
    for status in sorted(stats.keys()):
        print(f"\nSTATUS {status}:")
        for p, count in sorted(stats[status].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {p:10}: {count} dòng")
            
    conn.close()

if __name__ == "__main__":
    check_status_3_tags()
