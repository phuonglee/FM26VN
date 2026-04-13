import sqlite3
from core.config import DB_PATH

import re
import collections
import sys

# Đảm bảo in được tiếng Việt trên console Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def diagnose_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("--- CHƯƠNG TRÌNH CHẨN ĐOÁN LỖI DỊCH THUẬT ---")
    
    # 1. Kiểm tra Status 1 (Đã dịch)
    c.execute("SELECT id, english_text, translated_text, model_name FROM records WHERE status = 1")
    rows = c.fetchall()
    
    total_checked = len(rows)
    errors = []
    
    sq_tag_pattern = re.compile(r'\[%[^\]]+\]')
    cu_tag_pattern = re.compile(r'\{[^\}]+\}')
    
    for row_id, eng, trans, model in rows:
        if not trans:
            errors.append({
                "id": row_id,
                "reason": "Bản dịch bị trống (Null/Empty)",
                "eng": eng,
                "trans": trans
            })
            continue

        # 1. Chuẩn hóa Unicode
        import unicodedata
        eng_norm = unicodedata.normalize('NFC', eng)
        tra_norm = unicodedata.normalize('NFC', trans)
        
        # 2. Phân loại thẻ
        # Thẻ dữ liệu (Data Tags) - BẮT BUỘC phải khớp tiền tố
        data_prefixes = {'[%team', '[%cash', '[%number', '[%stadium', '[%club', '[%nationality', '[%nation'}
        # Thẻ đại từ (Pronoun Tags) - Có thể lược bỏ trong tiếng Việt
        pronoun_prefixes = {'[%person', '[%male', '[%female', '[%player', '[%manager', '[%referee', '[%chairman', '[%job'}

        def get_categorized_tags(text):
            all_tags = re.findall(sq_tag_pattern, text)
            data_tags = []
            pronoun_tags = []
            for t in all_tags:
                prefix = t.lower().rsplit('-', 1)[0] if '-' in t else t.lower().rstrip(']')
                if any(prefix.startswith(p) for p in data_prefixes):
                    data_tags.append(prefix + ']')
                else:
                    pronoun_tags.append(prefix + ']')
            return collections.Counter(data_tags), collections.Counter(pronoun_tags)

        eng_data, eng_pronoun = get_categorized_tags(eng_norm)
        tra_data, tra_pronoun = get_categorized_tags(tra_norm)
        
        # KIÊM TRA THẺ DỮ LIỆU (Bắt buộc khớp)
        diff_data_eng = eng_data - tra_data
        diff_data_tra = tra_data - eng_data
        
        # KIỂM TRA THẺ ĐẠI TỪ (Cho phép thiếu ở bản dịch, nhưng không cho phép thẻ lạ)
        # diff_pronoun_eng = eng_pronoun - tra_pronoun # Bỏ qua việc thiếu đại từ
        diff_pronoun_tra = tra_pronoun - eng_pronoun # Chỉ báo nếu có thẻ đại từ lạ không có trong gốc
        
        has_sq_error = False
        reason_sq = "Lỗi thẻ [%...]"
        if diff_data_eng or diff_data_tra:
            has_sq_error = True
            if diff_data_eng: reason_sq += f" | Thiếu thẻ dữ liệu: {list(diff_data_eng.elements())}"
            if diff_data_tra: reason_sq += f" | Thẻ dữ liệu sai: {list(diff_data_tra.elements())}"
        
        if diff_pronoun_tra:
            has_sq_error = True
            reason_sq += f" | Thẻ đại từ lạ: {list(diff_pronoun_tra.elements())}"

        if has_sq_error:
            errors.append({"id": row_id, "reason": reason_sq, "eng": eng_norm, "trans": tra_norm})
            continue

        # 3. Tìm thẻ {...} và chuẩn hóa
        def get_canonical_cu_tags(text):
            tags = re.findall(cu_tag_pattern, text)
            return [t.lower() for t in tags]

        eng_cu = get_canonical_cu_tags(eng_norm)
        trans_cu = get_canonical_cu_tags(tra_norm)
        
        cnt_eng_cu = collections.Counter(eng_cu)
        cnt_trans_cu = collections.Counter(trans_cu)
        
        diff_cu_eng = cnt_eng_cu - cnt_trans_cu
        diff_cu_trans = cnt_trans_cu - cnt_eng_cu
        
        # Lỗi 2: Sai lệch số lượng hoặc nội dung Thẻ {...}
        ignorable_curly = {'{s}', '{upper}', '{lower}', '{an}', '{a}', '{the}', '{scoreline}', '{ordinal}'}
        accepted_vi_curly = {'{một}', '{thứ}', '{một tỷ số}', '{}', '{s}'}
        
        for tag in ignorable_curly:
            if tag in diff_cu_eng: del diff_cu_eng[tag]
        for tag in accepted_vi_curly:
            if tag in diff_cu_trans: del diff_cu_trans[tag]

        if diff_cu_eng or diff_cu_trans:
            reason = "Lỗi thẻ {...}"
            if diff_cu_eng:
                reason += f" | Thiếu/Bị dịch: {list(diff_cu_eng.elements())}"
            if diff_cu_trans:
                reason += f" | Thẻ lạ/Sai: {list(diff_cu_trans.elements())}"
                
            errors.append({
                "id": row_id,
                "reason": reason,
                "eng": eng,
                "trans": trans
            })
            continue

            
        # Lỗi 3: Dịch cả Comment (thường bắt đầu bằng [COMMENT: ...])
        # Chỉ coi là lỗi nếu nội dung trong thẻ [COMMENT...] ở bản dịch khác với bản gốc (tức đã bị dịch nhầm)
        eng_comments = re.findall(r'(\[COMMENT[^\]]*\])', eng)
        trans_comments = re.findall(r'(\[COMMENT[^\]]*\])', trans)
        
        if collections.Counter(eng_comments) != collections.Counter(trans_comments):
            errors.append({
                "id": row_id,
                "reason": "Lỗi thẻ Chú thích ([COMMENT]) | Nội dung bị thay đổi hoặc thiếu",
                "eng": eng,
                "trans": trans
            })
            continue


        # Lỗi 4: Kiểm tra ngoặc vuông mồ côi (dấu hiệu thẻ bị gãy)
        # Nếu số lượng '[' hoặc ']' không khớp hoặc không lẻ loi trong văn bản game
        if trans.count('[') != trans.count(']') or trans.count('{') != trans.count('}'):
            errors.append({
                "id": row_id,
                "reason": "Ngoặc vuông hoặc ngoặc nhọn không cân đối (Dấu hiệu thẻ bị gãy)",
                "eng": eng,
                "trans": trans
            })
            continue

    # Tổng kết
    print(f"\nSỐ LIỆU TỔNG QUAN:")
    print(f"- Đã kiểm tra: {total_checked} dòng.")
    print(f"- Số dòng lỗi: {len(errors)} dòng.")
    
    if errors:
        print("\nDANH SÁCH CHI TIẾT CÁC LỖI ĐIỂN HÌNH (Theo loại lỗi):")
        
        # Nhóm lỗi theo lý do
        by_reason = collections.defaultdict(list)
        for err in errors:
            by_reason[err['reason'].split('|')[0].strip()].append(err)
            
        for reason, err_list in by_reason.items():
            print(f"\n--- LOẠI LỖI: {reason} (Ví dụ 3 dòng) ---")
            for i, err in enumerate(err_list[:3]):
                print(f"[{i+1}] ID: {err['id']}")
                print(f"    Chi tiết: {err['reason']}")
                print(f"    Gốc: {err['eng']}")
                print(f"    Dịch: {err['trans']}")
            
        # Thống kê loại lỗi
        reasons = [e['reason'].split('|')[0].strip() for e in errors]
        stats = collections.Counter(reasons)
        print("\nTHỐNG KÊ LOẠI LỖI:")
        for r, count in stats.items():
            print(f"- {r}: {count} dòng")
            
        # Hỏi user có muốn chuyển status 1 -> 3 cho các dòng này không?
        print("\n[HÀNH ĐỘNG GỢI Ý]: Nên chuyển các dòng này về Status 3 để dịch lại.")
    else:
        print("\nChúc mừng! Tất cả các dòng đã dịch đều tuân thủ quy tắc thẻ.")

    conn.close()

if __name__ == "__main__":
    diagnose_db()
