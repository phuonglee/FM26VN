#!/usr/bin/env python3
"""
Mô tả: Script reset các bản ghi đang ở trạng thái 'Processing' (Status 2) về 'Pending' (Status 0).
Sử dụng khi hệ thống agents bị crash hoặc người dùng chủ động dừng tiến trình.
"""

import sqlite3
import os
import sys

# Đảm bảo PYTHONPATH trỏ về root dự án nếu cần
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from core.config import DB_PATH
except ImportError:
    # Dự phòng nếu không import được từ core.config
    DB_PATH = "data/database.sqlite"

def reset_processing_status():
    """Reset status 2 -> 0"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Lỗi: Không tìm thấy database tại {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Đếm số lượng trước khi reset
        cursor.execute("SELECT COUNT(*) FROM records WHERE status = 2")
        count_before = cursor.fetchone()[0]
        
        if count_before == 0:
            print("✅ Không có bản ghi nào ở trạng thái Processing (2). Không cần reset.")
            conn.close()
            return

        # Thực hiện reset
        cursor.execute("UPDATE records SET status = 0 WHERE status = 2")
        conn.commit()
        
        print(f"🔄 Đã reset {count_before} bản ghi từ Processing (2) về Pending (0) thành công.")
        conn.close()
        
    except Exception as e:
        print(f"❌ Lỗi khi thao tác với database: {e}")

if __name__ == "__main__":
    # Đảm bảo in được tiếng Việt
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass
            
    reset_processing_status()
