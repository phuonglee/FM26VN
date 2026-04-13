import sqlite3
from core.config import DB_PATH

import re
import collections
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def final_polish():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("--- CHƯƠNG TRÌNH KHÔI PHỤC TOÀN DIỆN (FINAL POLISH) ---")
    
    # Xử lý tất cả các câu đã dịch (Status 1 và 3)
    c.execute("SELECT id, english_text, translated_text, status FROM records WHERE (status = 1 OR status = 3) AND translated_text IS NOT NULL AND translated_text != ''")
    rows = c.fetchall()
    
    total = len(rows)
    fixed_count = 0
    updated_records = []

    sq_tag_pattern = re.compile(r'\[%[^\]]+\]')
    cu_tag_pattern = re.compile(r'\{[^\}]+\}')
    base_id_pattern = re.compile(r'\[%[a-zA-Z0-9_]+(?:#\d+)?')
    comment_pattern = re.compile(r'(\[COMMENT[^\]]*\])')
    ignorable_curly = {'{s}', '{upper}', '{lower}', '{an}', '{An}', '{a}'}

    for row_id, eng, trans, status in rows:
        modified = False
        
        # 1. Fix [%...] tags
        eng_sq = re.findall(sq_tag_pattern, eng)
        trans_sq = list(set(re.findall(sq_tag_pattern, trans)))
        
        eng_sq_map = {}
        for tag in eng_sq:
            m = base_id_pattern.search(tag)
            if m: eng_sq_map[m.group(0)] = tag
        
        for tag in trans_sq:
            if tag not in eng_sq:
                m = base_id_pattern.search(tag)
                if m and m.group(0) in eng_sq_map:
                    trans = trans.replace(tag, eng_sq_map[m.group(0)])
                    modified = True

        # 2. Khôi phục thẻ vuông [%...] bị thiếu
        current_trans_sq = re.findall(sq_tag_pattern, trans)
        cnt_eng_sq = collections.Counter(eng_sq)
        cnt_trans_sq = collections.Counter(current_trans_sq)
        missing_sq = cnt_eng_sq - cnt_trans_sq
        if missing_sq:
            padding = ""
            for tag, count in missing_sq.items():
                padding += tag * count
            trans = trans.rstrip() + padding
            modified = True

        # 3. Khôi phục thẻ [COMMENT...] bị thiếu
        eng_comments = re.findall(comment_pattern, eng)
        trans_comments = re.findall(comment_pattern, trans)
        cnt_eng_comm = collections.Counter(eng_comments)
        cnt_trans_comm = collections.Counter(trans_comments)
        missing_comm = cnt_eng_comm - cnt_trans_comm
        if missing_comm:
            padding = ""
            for tag, count in missing_comm.items():
                padding += tag * count
            trans = trans.rstrip() + padding
            modified = True

        # Kiểm định
        final_trans_sq = re.findall(sq_tag_pattern, trans)
        final_trans_cu = re.findall(cu_tag_pattern, trans)
        final_trans_comm = re.findall(comment_pattern, trans)
        
        cnt_final_sq = collections.Counter(final_trans_sq)
        cnt_final_cu = collections.Counter(final_trans_cu)
        cnt_final_comm = collections.Counter(final_trans_comm)
        cnt_eng_cu = collections.Counter(re.findall(cu_tag_pattern, eng))

        # Phải khớp vuông và comment
        valid = (cnt_eng_sq == cnt_final_sq) and (cnt_eng_comm == cnt_final_comm)
        
        if valid:
            diff_cu_eng = cnt_eng_cu - cnt_final_cu
            diff_cu_trans = cnt_final_cu - cnt_eng_cu
            for tag in ignorable_curly:
                if tag in diff_cu_eng: del diff_cu_eng[tag]
                if tag in diff_cu_trans: del diff_cu_trans[tag]
            if diff_cu_eng or diff_cu_trans: valid = False
            
        if valid and (trans.count('[') != trans.count(']') or trans.count('{') != trans.count('}')):
            valid = False
                
        if valid and modified:
            fixed_count += 1
            # Chuyển về Status 1 nếu nó từng là 3
            updated_records.append((trans, 1, row_id))
        elif not valid and status == 1:
            # Nếu lỡ Status 1 mà giờ phát hiện không valid (sau khi đã cố fix), chuyển về 3
            updated_records.append((trans, 3, row_id))
            
    if updated_records:
        print(f"Đang cập nhật {len(updated_records)} dòng...")
        c.executemany("UPDATE records SET translated_text = ?, status = ? WHERE id = ?", updated_records)
        conn.commit()

    print(f"\n--- KẾT QUẢ ---")
    print(f"- Tổng số dòng đã quét: {total}")
    print(f"- Số dòng đã được sửa và cứu: {fixed_count}")

    conn.close()

if __name__ == "__main__":
    final_polish()
