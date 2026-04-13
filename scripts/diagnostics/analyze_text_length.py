import sqlite3
from core.config import DB_PATH


try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Thống kê trên các dòng CÒN CHƯA DỊCH
    c.execute("SELECT COUNT(*), SUM(LENGTH(english_text)) FROM records WHERE status = 0")
    total_rows, total_chars = c.fetchone()
    
    if total_rows and total_chars:
        avg_chars = total_chars / total_rows
        # 1 token tiếng Anh thường tương đương khoảng 4 ký tự
        avg_tokens = avg_chars / 4 
        print("=== KẾT QUẢ PHÂN TÍCH TEXT TRONG DATABASE ===")
        print(f"- Tổng số dòng: {total_rows:,}")
        print(f"- Tổng số ký tự (characters): {total_chars:,}")
        print(f"- Cỡ chữ trung bình: {avg_chars:.2f} ký tự/dòng")
        print(f"- Số Token trung bình (ước tính): {avg_tokens:.2f} token/dòng")
        
        # Thử tính cho lô 7000 dòng
        est_7000_tokens = 7000 * avg_tokens
        print(f"\n=> 7.000 dòng sẽ chứa khoảng: {est_7000_tokens:,.0f} Tokens")
    else:
        print("Không có dữ liệu.")
    conn.close()
except Exception as e:
    print("Lỗi:", e)
