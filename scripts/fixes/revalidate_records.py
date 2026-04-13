import sqlite3
from core.config import DB_PATH

import re

def revalidate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("Đang rà soát lại các câu dịch cũ đang ở trạng thái chờ (status = 0)...")
    # Lấy những câu có kết quả dịch nhưng đang bị để ở status 0
    c.execute("SELECT id, english_text, translated_text FROM records WHERE status = 0 AND translated_text IS NOT NULL AND translated_text != ''")
    rows = c.fetchall()

    if not rows:
        print("Không tìm thấy câu nào ở trạng thái chờ dịch nhưng đã có nội dung dịch cũ.")
        conn.close()
        return

    validated_ids = []
    
    for row in rows:
        row_id, eng, trans = row
        
        # 1. Kiểm tra thẻ định dạng ngoặc vuông [%...]
        eng_sq_tags = re.findall(r'\[%[^\]]+\]', eng)
        trans_sq_tags = re.findall(r'\[%[^\]]+\]', trans)
        
        # 2. Kiểm tra thẻ định dạng ngoặc nhọn {...}
        eng_cu_tags = re.findall(r'\{[^\}]+\}', eng)
        trans_cu_tags = re.findall(r'\{[^\}]+\}', trans)
        
        # Quy tắc: Số lượng và nội dung thẻ phải khớp tuyệt đối
        if eng_sq_tags == trans_sq_tags and eng_cu_tags == trans_cu_tags:
            validated_ids.append((row_id,))

    if validated_ids:
        print(f"Đã xác minh và cứu sống thành công: {len(validated_ids)} câu đạt chuẩn.")
        c.executemany("UPDATE records SET status = 1 WHERE id = ?", validated_ids)
        conn.commit()
    else:
        print("Không có câu nào đủ điều kiện để phục hồi (Hầu hết đều sai logic tags).")

    conn.close()

if __name__ == "__main__":
    revalidate()
