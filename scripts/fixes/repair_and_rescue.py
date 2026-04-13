import sqlite3
from core.config import DB_PATH

import re
import collections
import sys

# Ensure UTF-8 for console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def repair_and_rescue():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("--- CHƯƠNG TRÌNH SỬA LỖI VÀ KHÔI PHỤC (REPAIR & RESCUE) ---")
    
    # Lấy các dòng status 3 có nội dung dịch
    c.execute("SELECT id, english_text, translated_text FROM records WHERE status = 3 AND translated_text IS NOT NULL AND translated_text != ''")
    rows = c.fetchall()
    
    total = len(rows)
    fixed_count = 0
    updated_records = []

    sq_tag_pattern = re.compile(r'\[%[^\]]+\]')
    cu_tag_pattern = re.compile(r'\{[^\}]+\}')
    base_id_pattern = re.compile(r'\[%[a-zA-Z0-9_]+(?:#\d+)?')
    ignorable_curly = {'{s}', '{upper}', '{lower}', '{an}', '{An}', '{a}'}

    for row_id, eng, trans in rows:
        original_trans = trans
        
        # 1. Map [%...] tags (Sửa lỗi dịch nhầm nội dung thẻ)
        eng_sq = re.findall(sq_tag_pattern, eng)
        trans_sq = list(set(re.findall(sq_tag_pattern, trans)))
        
        eng_sq_map = {}
        for tag in eng_sq:
            m = base_id_pattern.search(tag)
            if m:
                eng_sq_map[m.group(0)] = tag
        
        # Sửa các tag bị dịch sai
        for tag in trans_sq:
            if tag not in eng_sq:
                m = base_id_pattern.search(tag)
                if m and m.group(0) in eng_sq_map:
                    # Thay thế tag sai bằng tag đúng từ English
                    trans = trans.replace(tag, eng_sq_map[m.group(0)])

        # 2. Khôi phục thẻ vuông bị "nuốt"
        # Lấy lại danh sách tag sau khi đã sửa ở bước 1
        current_trans_sq = re.findall(sq_tag_pattern, trans)
        cnt_eng_sq = collections.Counter(eng_sq)
        cnt_trans_sq = collections.Counter(current_trans_sq)
        
        missing_sq = cnt_eng_sq - cnt_trans_sq
        if missing_sq:
            # Chèn các thẻ thiếu vào cuối câu
            padding = ""
            for tag, count in missing_sq.items():
                padding += tag * count
            trans = trans.rstrip() + padding

        # 3. Kiểm tra tính hợp lệ sau khi sửa (Dựa trên logic diagnose_db mới)
        eng_cu = re.findall(cu_tag_pattern, eng)
        final_trans_sq = re.findall(sq_tag_pattern, trans)
        final_trans_cu = re.findall(cu_tag_pattern, trans)
        
        cnt_final_sq = collections.Counter(final_trans_sq)
        cnt_final_cu = collections.Counter(final_trans_cu)
        cnt_eng_cu = collections.Counter(eng_cu)

        # Kiểm soát lỗi thẻ vuông (bắt buộc khớp 100%)
        is_valid = (cnt_eng_sq == cnt_final_sq)
        
        # Kiểm soát lỗi thẻ nhọn (bỏ qua ignorable)
        if is_valid:
            diff_cu_eng = cnt_eng_cu - cnt_final_cu
            diff_cu_trans = cnt_final_cu - cnt_eng_cu
            for tag in ignorable_curly:
                if tag in diff_cu_eng: del diff_cu_eng[tag]
                if tag in diff_cu_trans: del diff_cu_trans[tag]
            
            if diff_cu_eng or diff_cu_trans:
                is_valid = False
        
        # Kiểm soát lỗi ngoặc cân đối
        if is_valid:
            if trans.count('[') != trans.count(']') or trans.count('{') != trans.count('}'):
                is_valid = False
                
        # 4. Lưu lại nếu hợp lệ
        if is_valid:
            fixed_count += 1
            updated_records.append((trans, row_id))
            
    # Cập nhật database hàng loạt
    if updated_records:
        print(f"Đang cập nhật {len(updated_records)} dòng vào database...")
        c.executemany("UPDATE records SET translated_text = ?, status = 1 WHERE id = ?", updated_records)
        conn.commit()

    print(f"\n--- KẾT QUẢ ---")
    print(f"- Tổng số dòng Status 3 đã quét: {total}")
    print(f"- Số dòng đã sửa và cứu thành công (về Status 1): {fixed_count}")
    print(f"- Số dòng vẫn còn lỗi (giữ Status 3): {total - fixed_count}")

    conn.close()

if __name__ == "__main__":
    repair_and_rescue()
