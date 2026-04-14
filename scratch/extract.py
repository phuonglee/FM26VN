import sqlite3
import re
from collections import defaultdict

db = sqlite3.connect('data/database.sqlite')
cursor = db.cursor()
cursor.execute("SELECT english_text FROM records WHERE english_text IS NOT NULL")
rows = cursor.fetchall()
db.close()

tags_square = defaultdict(int)
tags_curly = defaultdict(int)

for row in rows:
    text = row[0]
    if text:
        # Match square tags [%xyz]
        sq_matches = re.findall(r'\[%[^\]]+\]', text)
        for m in sq_matches:
            normalized = re.sub(r'#\d+', '#', m)
            tags_square[normalized] += 1
            
        cur_matches = re.findall(r'\{[^\}]+\}', text)
        for m in cur_matches:
            tags_curly[m] += 1

with open('scratch/tags_output_utf8.txt', 'w', encoding='utf-8') as f:
    f.write("SQUARE TAGS (Top 100):\n")
    for t, count in sorted(tags_square.items(), key=lambda x: x[1], reverse=True)[:100]:
        f.write(f"{t}: {count}\n")

    f.write("\nCURLY TAGS (Top 50):\n")
    for t, count in sorted(tags_curly.items(), key=lambda x: x[1], reverse=True)[:50]:
        f.write(f"{t}: {count}\n")
