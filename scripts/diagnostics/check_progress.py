import sys
import os
from pathlib import Path

# Thêm dự án gốc vào sys.path để có thể import core
root = Path(__file__).parent.parent.parent.absolute()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Fix lỗi hiển thị tiếng Việt trên Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

import sqlite3
from core.config import DB_PATH

import os

def check():
    db_file = DB_PATH
    if not os.path.exists(db_file):
        print("Database not found!")
        return
        
    try:
        conn = sqlite3.connect(db_file, timeout=20)
        c = conn.cursor()
        
        # Check total
        c.execute('SELECT COUNT(*) FROM records')
        total = c.fetchone()[0]
        
        # Check done
        c.execute('SELECT COUNT(*) FROM records WHERE status = 1')
        done = c.fetchone()[0]
        
        # Check in progress
        c.execute('SELECT COUNT(*) FROM records WHERE status = 2')
        processing = c.fetchone()[0]
        
        # Check breakdown by model
        model_breakdown = []
        try:
            c.execute('SELECT model_name, COUNT(*) FROM records WHERE status = 1 GROUP BY model_name')
            model_breakdown = c.fetchall()
        except:
            pass
        
        print("\n=== TIẾN ĐỘ DỊCH THUẬT ===")
        print(f"- Tổng số dòng: {total:,}")
        print(f"- Đã hoàn thành: {done:,}")
        
        if model_breakdown:
            print("  [Chi tiết theo Model]:")
            for model, count in model_breakdown:
                model_label = model if model else "Không rõ (Cũ)"
                print(f"   + {model_label}: {count:,} câu")
        
        print(f"- Đang xử lý dở dang: {processing:,}")
        print(f"- Còn lại: {total - done - processing:,}")
        
        if total > 0:
            percentage = (done / total) * 100
            print(f"- Tỷ lệ hoàn thành: {percentage:.2f}%")
        
        conn.close()
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    check()
