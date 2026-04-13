import sqlite3
from core.config import DB_PATH

import os
import glob
from tqdm import tqdm

DB_NAME = DB_PATH

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_source TEXT,
            key_id TEXT,
            english_text TEXT,
            translated_text TEXT DEFAULT '',
            status INTEGER DEFAULT 0
        )
    ''')
    # Create index for fast query
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON records(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_key ON records(file_source, key_id)')
    conn.commit()
    return conn

def import_file(conn, file_path):
    print(f"Bắt đầu đọc file {file_path}...")
    cursor = conn.cursor()
    
    file_source = os.path.basename(file_path)
    
    # Xoá data cũ mấu file này nếu có (tránh duplicate khi chạy lại)
    cursor.execute("DELETE FROM records WHERE file_source = ?", (file_source,))
    conn.commit()
    
    records_to_insert = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        # Chúng ta không dùng split line vì file quá lớn, chúng ta duyệt từng dòng thay vì readlines
        for line in tqdm(f, desc=f"Parsing {file_source}"):
            line = line.strip()
            if line.startswith('KEY-'):
                # Cấu trúc: 'KEY-227312: Worldwide[COMMENT club reputation]'
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key_id = parts[0].strip()
                    english_text = parts[1].strip()
                    
                    records_to_insert.append((file_source, key_id, english_text))
                    
                    # Chèn theo lô 10.000 dòng để tránh đầy RAM
                    if len(records_to_insert) >= 10000:
                        cursor.executemany(
                            "INSERT INTO records (file_source, key_id, english_text) VALUES (?, ?, ?)",
                            records_to_insert
                        )
                        records_to_insert.clear()
                        
    # Chèn nốt số lượng còn lại
    if records_to_insert:
        cursor.executemany(
            "INSERT INTO records (file_source, key_id, english_text) VALUES (?, ?, ?)",
            records_to_insert
        )
    
    conn.commit()
    print(f"Đã import thành công {file_source} vào Database.")

def main():
    conn = init_db()
    files = glob.glob(os.path.join('languages', '*.ltf'))
    if not files:
        print("Không tìm thấy file .ltf nào trong thư mục 'languages'. Vui lòng kiểm tra lại.")
        return

    for file in files:
        import_file(conn, file)
        
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM records")
    total = cursor.fetchone()[0]
    print(f"\n✅ Hoàn tất! Tổng số dòng KEY cần dịch trong Database: {total}")
    conn.close()

if __name__ == "__main__":
    main()
