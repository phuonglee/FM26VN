import sqlite3
from core.config import DB_PATH

import re

def fix_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Đang quét toàn bộ dữ liệu...")
    c.execute("SELECT id, english_text, translated_text FROM records WHERE status = 1 AND english_text LIKE '%[%'")
    rows = c.fetchall()

    auto_fixed = 0
    reset_to_zero = 0
    unaffected = 0

    update_batch = []
    reset_batch = []

    for row in rows:
        row_id, eng, trans = row
        
        # Tìm các thẻ [%...]
        eng_tags = re.findall(r'\[%[^\]]+\]', eng)
        trans_tags = re.findall(r'\[%[^\]]+\]', trans)
        
        if eng_tags != trans_tags:
            if len(eng_tags) == len(trans_tags):
                # Auto-heal: thay thế các tag bị sai trong bản dịch bằng các tag đúng theo thứ tự
                eng_tags_copy = list(eng_tags)
                def replacer(match):
                    return eng_tags_copy.pop(0)
                    
                new_trans = re.sub(r'\[%[^\]]+\]', replacer, trans)
                update_batch.append((new_trans, row_id))
                auto_fixed += 1
            else:
                # Nếu số lượng thẻ bị lệch, trả về trạng thái 0 để máy dịch lại từ đầu
                reset_batch.append((row_id,))
                reset_to_zero += 1
        else:
            unaffected += 1

    if update_batch:
        c.executemany("UPDATE records SET translated_text = ? WHERE id = ?", update_batch)
    if reset_batch:
        c.executemany("UPDATE records SET status = 0 WHERE id = ?", reset_batch)

    conn.commit()
    conn.close()

    print("\n=== KẾT QUẢ SỬA LỖI TAGS ===")
    print(f"- Đã phát hiện và dùng Tool sửa tự động (Thay lại thẻ gốc): {auto_fixed:,} câu.")
    print(f"- Bị hỏng câu trúc thẻ nặng (Đã reset về trạng thái 0 để AI dịch lại): {reset_to_zero:,} câu.")
    print(f"- An toàn (Không sai): {unaffected:,} câu.")

if __name__ == "__main__":
    fix_database()
