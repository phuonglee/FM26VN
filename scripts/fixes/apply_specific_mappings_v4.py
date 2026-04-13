import sqlite3
from core.config import DB_PATH

import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def apply_specific_mappings_all_status():
    db_path = DB_PATH
    conn = sqlite3.connect(db_path, timeout=60)
    c = conn.cursor()
    
    mappings = {
        '[%person#4-I]': 'tôi',
        '[%person#2-you]': 'ngài',
        '[%male#3-him]': 'anh ấy',
        '[%male#1-he]': 'anh ta'
    }
    
    total_updated = 0
    
    # Quét toàn bộ các dòng CÓ nội dung bản dịch (bất kể Status nào)
    c.execute("SELECT id, translated_text FROM records WHERE translated_text IS NOT NULL AND translated_text != ''")
    rows = c.fetchall()
    
    print(f"Đang kiểm tra {len(rows)} câu có nội dung bản dịch...")
    updates = []
    
    for rid, text in rows:
        new_text = text
        found = False
        for tag, replacement in mappings.items():
            if tag in new_text:
                new_text = new_text.replace(tag, replacement)
                found = True
        
        if found:
            # Chuẩn hóa viết hoa đầu câu
            if new_text.startswith('tôi '): new_text = 'Tôi ' + new_text[4:]
            elif new_text.startswith('ngài '): new_text = 'Ngài ' + new_text[5:]
            elif new_text.startswith('anh ấy '): new_text = 'Anh ấy ' + new_text[7:]
            elif new_text.startswith('anh ta '): new_text = 'Anh ta ' + new_text[7:]
            
            updates.append((new_text, rid))

    if updates:
        print(f"Tìm thấy {len(updates)} dòng cần cập nhật. Đang đồng bộ...")
        batch_size = 2000
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            c.executemany("UPDATE records SET translated_text = ? WHERE id = ?", batch)
            conn.commit()
        total_updated = len(updates)
    else:
        print("Không tìm thấy các thẻ này trong phần dịch.")

    print(f"Hoàn tất! Đã cập nhật xong {total_updated} dòng.")
    conn.close()

if __name__ == "__main__":
    apply_specific_mappings_all_status()
