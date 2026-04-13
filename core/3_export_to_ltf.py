# KHÔNG TỰ Ý UPDATE FILE NÀY TRỪ KHI CÓ YÊU CẦU TỪ NGƯỜI DÙNG!
import sqlite3
from core.config import DB_PATH

import os
import re
import sys

# Đảm bảo terminal hiển thị được tiếng Việt
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

DB_NAME = DB_PATH

def get_latest_version(release_dir):
    if not os.path.exists(release_dir):
        return None
    subdirs = [d for d in os.listdir(release_dir) if os.path.isdir(os.path.join(release_dir, d))]
    
    def parse_version(v):
        # Cố gắng bóc tách các chữ số từ folder có định dạng vX.Y
        v_str = v[1:] if v.startswith('v') else v
        parts = []
        for p in v_str.split('.'):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        return tuple(parts)
        
    valid_subdirs = [d for d in subdirs if d.startswith('v')]
    if not valid_subdirs:
        return None
        
    return sorted(valid_subdirs, key=parse_version)[-1]

def main():
    if not os.path.exists(DB_NAME):
        print("Chưa có database. Vui lòng chạy 1_import_to_db.py và 2_run_agents.py trước!")
        return
        
    release_dir = 'release'
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)
        
    latest_version = get_latest_version(release_dir)
    print("--- QUẢN LÝ VERSION RELEASE ---")
    if latest_version:
        print(f"Version mới nhất hiện tại trong folder release là: {latest_version}")
    else:
        print("Hiện chưa có version release nào trong folder release.")
        
    print("LƯU Ý: Luôn hỏi người dùng xem muốn release version nào, không được tự ý tăng version hoặc sub version!")
    version_input = input("Vui lòng nhập tên thư mục version bạn muốn xuất dữ liệu (VD: v1.0, v1.1, ...): ").strip()
    
    if not version_input:
        print("Tên version không hợp lệ. Đã hủy quá trình export.")
        return
        
    out_dir = os.path.join(release_dir, version_input)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("Đang truy xuất toàn bộ dữ liệu (Bao gồm dữ liệu đã dịch và các câu gốc chưa dịch)...")
    cursor.execute("SELECT key_id, english_text, translated_text FROM records")
    
    translations = {}
    for row in cursor.fetchall():
        key_id = row[0]
        original = str(row[1]) if row[1] is not None else ""
        translated = str(row[2]) if row[2] is not None else ""
        
        # Nếu chưa có bản dịch (Agent mới đi được 57%), dùng lại tiếng Anh gốc để game chạy không rớt nửa chữ
        trans = translated if translated.strip() != "" else original
        translations[key_id] = trans

    out_file = os.path.join(out_dir, 'vietnamese.ltf')
    print(f"Đang tổng hợp và xuất ra file duy nhất: {out_file}...")

    files_to_merge = ['vnm_p1.ltf', 'vnm_p2.ltf']
    header_written = False

    with open(out_file, 'w', encoding='utf-8') as fout:
        for file_name in files_to_merge:
            in_file = os.path.join('languages', file_name)
            if not os.path.exists(in_file):
                print(f"Bỏ qua {file_name} vì không tồn tại trong thư mục languages.")
                continue
                
            with open(in_file, 'r', encoding='utf-8', errors='ignore') as fin:
                current_key = None
                writing_body = False
                
                for line in fin:
                    if line.startswith('KEY-'):
                        writing_body = True
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            current_key = parts[0].strip()
                        fout.write(line)
                        
                    elif line.startswith('STR-1:') and current_key:
                        trans = translations.get(current_key, "")
                        fout.write(f"STR-1: {trans}\n")
                        current_key = None
                        
                    else:
                        # Khu vực Header hoặc các dòng trống xen kẽ
                        if not writing_body:
                            if not header_written:
                                # Điều chỉnh LANGNAME trên Header thành Vietnamese
                                if line.startswith('LANGNAME:'):
                                    fout.write('LANGNAME: Vietnamese\n')
                                elif line.startswith('LANGUAGE'):
                                    fout.write('LANGUAGE "Vietnamese"\n')
                                else:
                                    fout.write(line)
                        else:
                            # Ghi những dòng trống, chú thích nằm xen kẽ bên dưới nội dung
                            fout.write(line)
                            
            # Sau khi đọc xong file p1, các file p2, p3... tiếp theo sẽ bị bỏ qua Header để chỉ dán nối phần nội dung vào đuôi nhau
            header_written = True

    conn.close()
    print(f"HOÀN TẤT! Đã gộp thành công file {out_file}")

if __name__ == "__main__":
    main()
