import sqlite3
from core.config import DB_PATH

import time
import os

DB_NAME = DB_PATH
LOG_FILE = 'reporter_log.md'

def get_stats():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM records WHERE status = 1")
        done = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM records")
        total = c.fetchone()[0]
        conn.close()
        return done, total
    except:
        return None, None

def report():
    last_done, total = get_stats()
    start_time = time.time()
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("# 📡 BÁO CÁO GIÁM SÁT DỊCH THUẬT (LIVE)\n\n")
        f.write(f"**Bắt đầu giám sát:** {time.strftime('%H:%M:%S')}\n")
    
    while True:
        time.sleep(300) # 5 minutes
        current_done, total = get_stats()
        if current_done is None: continue
        
        delta = current_done - last_done
        speed = delta / 5
        percent = (current_done / total) * 100
        
        timestamp = time.strftime('%H:%M:%S')
        report_line = f"| {timestamp} | {current_done:,} | +{delta:,} | {speed:.1f} câu/p | {percent:.2f}% |\n"
        
        # Append to log
        if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) < 100:
             with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write("\n| Thời gian | Tổng đã xong | Tăng thêm | Tốc độ | Tiến độ |\n")
                f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(report_line)
            
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        print(f"\n[REPORTER] Cập nhật lúc {timestamp}: {current_done} câu ({percent:.2f}%)")
        last_done = current_done

if __name__ == '__main__':
    report()
