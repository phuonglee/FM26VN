import sqlite3
from core.config import DB_PATH

import re
import os
import sys

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class DatabaseStandardizer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.changed_pronouns_ids = []
        
        # Mapping for tags
        self.en_to_vi_tags = {
            "you": "Ngài", "your": "Ngài", "i": "tôi", "me": "tôi",
            "my": "của tôi", "he": "anh ấy", "him": "anh ấy",
            "his": "của anh ấy", "himself": "bản thân anh ấy",
            "she": "cô ấy", "her": "cô ấy", "hers": "của cô ấy",
            "they": "họ", "them": "họ", "their": "của họ", "it": "nó", "its": "của nó"
        }
        
        self.vi_to_vi_tags = {
            "bạn": "Ngài", "anh": "Ngài", "cậu": "Ngài", "anh ấy": "anh ấy", 
            "anh ta": "anh ta", "cô ấy": "cô ấy", "cô ta": "cô ta", "nó": "nó", "họ": "họ"
        }

    def clean_text(self, eng, tra, rid):
        if not tra: return tra
        
        original_tra = tra
        
        # 1. Handle Curly Tags
        tra = tra.replace("{an}", "{một}").replace("{a}", "{một}")
        tra = tra.replace("{An}", "{Một}").replace("{A}", "{Một}")
        tra = tra.replace("{scoreline}", "{một tỷ số}")
        tra = tra.replace("{ordinal}", "{thứ}")
        tra = tra.replace("{the}", "{}")
        
        # 2. Handle Possessive {s}
        tra = re.sub(r'(\[%[^\]]+\])\{s\}', r'của \1', tra)
        
        # 3. Tag Suffix Normalization & Suffix Translation
        def tag_replacer(match):
            content = match.group(1).strip()
            suffix_match = re.search(r'-([^\]]+)$', content)
            if suffix_match:
                base = content[:suffix_match.start()]
                suffix = suffix_match.group(1).lower()
                target_suffix = self.en_to_vi_tags.get(suffix, self.vi_to_vi_tags.get(suffix, suffix))
                return f"[%{base}-{target_suffix}]"
            return f"[%{content}]"

        tra = re.sub(r'\[%([^\]]+)\]', tag_replacer, tra)
        
        # 4. Fix redundant pronouns after tags
        for word in ["ngài", "tôi", "anh ấy", "cô ấy", "họ", "nó"]:
            tra = re.sub(rf'\]\s+{word}\b', ']', tra, flags=re.IGNORECASE)
            
        # 5. Plain Text Pronouns (bạn/anh/cậu -> Ngài) if English has "you"
        if re.search(r'\byou\b', eng, re.I):
            # Replace common you-pronouns with Ngài
            new_tra = re.sub(r'\b(bạn|anh|cậu)\b', 'Ngài', tra, flags=re.IGNORECASE)
            if new_tra != tra:
                self.changed_pronouns_ids.append(rid)
                tra = new_tra

        # 6. Technical Cleanup
        tra = tra.replace("]]", "]")
        tra = tra.replace("tôiđã", "tôi đã")
        tra = tra.replace("quan trọngtôi", "quan trọng")
        
        # Repetitions
        for word in ["của", "nó", "tôi", "đã", "anh", "người", "ngài", "của nó", "anh ấy", "cô ấy", "họ", "mình"]:
            tra = re.sub(rf'\b({word})\s+\1\b', r'\1', tra, flags=re.IGNORECASE)
        
        # 7. Capitalization
        # Start of sentence
        if tra and tra[0].islower():
            if not tra.startswith('[%'): # If it's pure text
                tra = tra[0].upper() + tra[1:]
        
        # If tag at start of sentence has suffix
        if tra.startswith('[%'):
            tra = re.sub(r'^\[%([^\]-]+)-([a-z])', lambda m: f"[%{m.group(1)}-{m.group(2).upper()}", tra)

        # After punctuation
        tra = re.sub(r'([\.!\?])\s?([a-z])', lambda m: m.group(1) + " " + m.group(2).upper(), tra)

        # 8. Whitespace
        tra = re.sub(r'\s{2,}', ' ', tra)
        tra = re.sub(r'\s+([\.!\?,])', r'\1', tra)
        tra = tra.strip()
        
        return tra

    def run(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("Đang truy vấn các bản ghi đã dịch (Status 1)...")
        cursor.execute("SELECT id, english_text, translated_text FROM records WHERE status = 1")
        rows = cursor.fetchall()
        total = len(rows)
        print(f"Tổng cộng {total:,} bản ghi.")
        
        updated_count = 0
        
        for rid, eng, tra in rows:
            cleaned = self.clean_text(eng, tra, rid)
            if cleaned != tra:
                cursor.execute("UPDATE records SET translated_text = ? WHERE id = ?", (cleaned, rid))
                updated_count += 1
            
            if (updated_count + (len(rows) - total)) % 10000 == 0:
                print(f"Đã xử lý: {rid}/{rows[-1][0]}... (Đã cập nhật: {updated_count:,})")
                conn.commit()

        conn.commit()
        conn.close()
        
        print(f"\nHoàn tất! Đã cập nhật {updated_count:,} bản ghi.")
        
        # Save changed pronoun IDs
        if self.changed_pronouns_ids:
            with open("changed_pronouns_ids.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(map(str, self.changed_pronouns_ids)))
            print(f"Danh sách ID thay đổi xưng hô đã được lưu vào changed_pronouns_ids.txt ({len(self.changed_pronouns_ids)} bản ghi)")

if __name__ == "__main__":
    standardizer = DatabaseStandardizer(DB_PATH)
    standardizer.run()
