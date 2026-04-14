import sqlite3
import time
import sys
import os
from pathlib import Path

# Thêm dự án gốc vào sys.path
root = Path(__file__).parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from core.logic_check import LogicCheck
from core.config import DB_PATH

# Fix Unicode console
if sys.stdout.encoding != 'utf-8':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

def run_reviewer():
    print("=== BẮT ĐẦU CHƯƠNG TRÌNH KIỂM SOÁT CHẤT LƯỢNG (THE LEAN JUDGE) ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Đếm số lượng cần chấm điểm
    cursor.execute("SELECT COUNT(*) FROM records WHERE status = 1 AND rate = 0.0")
    total_to_review = cursor.fetchone()[0]
    print(f"[*] Tìm thấy {total_to_review:,} bản ghi cần chấm điểm.")

    if total_to_review == 0:
        print("[+] Mọi bản ghi đã được chấm điểm. Kết thúc.")
        return

    batch_size = 5000
    report_interval = 50000
    reviewed_count = 0
    start_time = time.time()
    
    stats = {"1.0": 0, "low_rate": 0, "quarantined": 0}

    while True:
        cursor.execute("SELECT id, english_text, translated_text FROM records WHERE status = 1 AND rate = 0.0 LIMIT ?", (batch_size,))
        rows = cursor.fetchall()
        if not rows:
            break

        updates = []
        for row_id, eng, vi in rows:
            # Xử lý trường hợp vi bị NULL trong DB
            if vi is None:
                vi = ""
            
            rate, feedback, fixed_vi = LogicCheck.evaluate(eng, vi)
            
            # Quyết định trạng thái
            status = 1
            if rate < 0.5:
                status = 3 # Quarantine
                stats["quarantined"] += 1
            
            if rate == 1.0:
                stats["1.0"] += 1
            elif rate < 0.9:
                stats["low_rate"] += 1

            updates.append((rate, status, feedback, fixed_vi, row_id))

        cursor.executemany("UPDATE records SET rate = ?, status = ?, review_feedback = ?, translated_text = ? WHERE id = ?", updates)
        conn.commit()
        
        reviewed_count += len(rows)
        
        # Báo cáo mỗi 50,000 câu
        if reviewed_count % report_interval == 0 or reviewed_count == total_to_review:
            elapsed = time.time() - start_time
            speed = reviewed_count / elapsed if elapsed > 0 else 0
            print(f"\n--- BÁO CÁO TIẾN ĐỘ ({reviewed_count:,} / {total_to_review:,}) ---")
            print(f"- Tuyệt vời (1.0): {stats['1.0']:,}")
            print(f"- Cần cải thiện (< 0.9): {stats['low_rate']:,}")
            print(f"- Đã Cách ly (Quarantine): {stats['quarantined']:,}")
            print(f"- Tốc độ xử lý: {speed:.0f} câu/giây")
            
    conn.close()
    print("\n[+] Hoàn thành toàn bộ quá trình chấm điểm.")

if __name__ == "__main__":
    run_reviewer()
