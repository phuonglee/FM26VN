import sqlite3
from core.config import DB_PATH

import re
import sys
import time

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def apply_final_tag_mapping():
    db_path = DB_PATH
    conn = sqlite3.connect(db_path, timeout=60)
    c = conn.cursor()
    
    # Định nghĩa các quy tắc theo Hậu tố (Suffix)
    # Cấu trúc: {Suffix: (Dạng thường, Dạng hoa)}
    rules = {
        'i': ('tôi', 'Tôi'),
        'you': ('ngài', 'Ngài'),
        'he': ('anh ta', 'Anh ta'),
        'him': ('anh ấy', 'Anh ấy')
    }
    
    # Regex tìm thẻ [%...-suffix]
    # Group 1: Nội dung trước dấu gạch ngang (ví dụ person#4)
    # Group 2: Hậu tố (ví dụ i, you, You, he, He)
    tag_pattern = re.compile(r'\[%([^\]]+)-([a-zA-Z]+)\]')
    
    c.execute("SELECT id, translated_text FROM records WHERE translated_text IS NOT NULL AND translated_text != ''")
    rows = c.fetchall()
    
    print(f"Đang xử lý {len(rows)} câu để chuẩn hóa toàn bộ các thẻ đại từ...")
    updates = []
    
    for rid, text in rows:
        new_text = text
        matches = list(tag_pattern.finditer(text))
        if not matches:
            continue
            
        changed = False
        # Duyệt ngược để không làm hỏng index khi thay thế
        for match in reversed(matches):
            full_tag = match.group(0)
            suffix = match.group(2).lower()
            original_suffix = match.group(2)
            
            if suffix in rules:
                # Quyết định viết hoa hay thường dựa trên ký tự đầu của hậu tố gốc
                is_capital = original_suffix[0].isupper()
                replacement = rules[suffix][1] if is_capital else rules[suffix][0]
                
                new_text = new_text[:match.start()] + replacement + new_text[match.end():]
                changed = True
        
        if changed:
            # Sửa lỗi lặp từ sau khi thay thế (nếu có) và chuẩn hóa đầu câu
            if new_text.startswith('tôi '): new_text = 'Tôi ' + new_text[4:]
            elif new_text.startswith('ngài '): new_text = 'Ngài ' + new_text[5:]
            elif new_text.startswith('anh ta '): new_text = 'Anh ta ' + new_text[7:]
            elif new_text.startswith('anh ấy '): new_text = 'Anh ấy ' + new_text[7:]
            
            updates.append((new_text, rid))

    if updates:
        print(f"Tìm thấy {len(updates)} dòng cần cập nhật. Đang đồng bộ...")
        batch_size = 2000
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            c.executemany("UPDATE records SET translated_text = ? WHERE id = ?", batch)
            conn.commit()
    else:
        print("Không tìm thấy thẻ nào phù hợp quy tắc.")

    print(f"Hoàn tất! Đã cập nhật {len(updates)} dòng.")
    conn.close()

if __name__ == "__main__":
    apply_final_tag_mapping()
