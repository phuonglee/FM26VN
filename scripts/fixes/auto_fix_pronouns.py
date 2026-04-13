import sqlite3
import re
import sys
import os
from pathlib import Path

# Thêm dự án gốc vào sys.path
root = Path(__file__).parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from core.config import DB_PATH
from core.logic_check import LogicCheck

def auto_fix():
    print("[*] Bắt đầu tự động sửa lỗi xưng hô 'anh' -> 'ngài'...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tìm các bản ghi bị lỗi xưng hô 'anh'
    # Lưu ý: Do trước đó bị lỗi 'None', chúng ta sẽ tìm theo pattern tin nhắn lỗi
    cursor.execute("SELECT id, english_text, translated_text FROM records WHERE review_feedback LIKE ?", ('%Dùng \'anh\' đơn lẻ%',))
    rows = cursor.fetchall()
    
    if not rows:
        print("[+] Không tìm thấy bản ghi nào cần sửa.")
        return

    print(f"[*] Tìm thấy {len(rows):,} bản ghi cần xử lý.")
    
    updates = []
    fixed_count = 0
    
    for row_id, eng, vi in rows:
        # Thực hiện thay thế anh -> ngài (giữ nguyên case)
        # 1. Thay 'Anh' -> 'Ngài'
        new_vi = re.sub(r'\bAnh\b(?!( ấy| ta))', 'Ngài', vi)
        # 2. Thay 'anh' -> 'ngài'
        new_vi = re.sub(r'\banh\b(?!( ấy| ta))', 'ngài', new_vi)
        
        if new_vi != vi:
            # Sau khi sửa, chấm điểm lại ngay
            new_rate, new_feedback = LogicCheck.evaluate(eng, new_vi)
            updates.append((new_vi, new_rate, new_feedback, row_id))
            fixed_count += 1

    if updates:
        cursor.executemany("UPDATE records SET translated_text = ?, rate = ?, review_feedback = ? WHERE id = ?", updates)
        conn.commit()
    
    conn.close()
    print(f"[+] Hoàn tất! Đã sửa và nâng cấp điểm cho {fixed_count:,} bản ghi.")

if __name__ == "__main__":
    auto_fix()
