import sqlite3
from core.config import DB_PATH

import os
import json
import requests
import time

# Cấu hình Ollama Local
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" # Quay lại Llama 3 theo yêu cầu
DB_NAME = DB_PATH
BATCH_SIZE = 8 # Hạ xuống 8 dòng để đạt tốc độ phản hồi nhanh nhất trên Card 8GB VRAM.

PROMPT_TEMPLATE = """
Bạn là một chuyên gia dịch thuật tiếng Việt xuất sắc cho game bóng đá Football Manager.
Luật bắt buộc:
1. TUYỆT ĐỐI KHÔNG BAO GIỜ dịch, thay đổi, xóa bỏ hoặc làm biến dạng các Thẻ Định Dạng (Tags). Các thẻ này vô cùng quan trọng đối với code, bao gồm:
   - Thẻ biến động trong ngoặc vuông (vd: [%person#1-I], [%team#1-nickname], v.v.).
   - LỖI THƯỜNG GẶP CẦN TRÁNH: Tuyệt đối không dịch chữ bên trong ngoặc vuông. Ví dụ: KHÔNG ĐƯỢC biến [%male#1-I] thành [%male#1-Tôi]. ĐÂY LÀ LỖI HỎNG GAME NGHIÊM TRỌNG. Bạn phải giữ im bản gốc là [%male#1-I].
   - Thẻ định dạng cú pháp trong ngoặc nhọn (vd: {upper}, {s}, {lower}, v.v.).
Bạn BẮT BUỘC phải sao chép nguyên xi và đặt các thẻ này vào vị trí tương ứng trong câu dịch. KHÔNG ĐƯỢC LÀM MẤT HOẶC MÓP MÉO BẤT CỨ THẺ NÀO.
2. Dựa vào từ khóa trong thẻ để phán đoán xưng hô bên ngoài mạch văn cho mềm mại. Ví dụ: thấy [%person#1-I] thì tự hiểu nội dung ngoài thẻ là xưng 'Tôi'.
3. Không dịch các từ đóng vai trò là tên riêng, địa danh, hoặc các từ VIẾT HOA HOÀN TOÀN. 
4. Nếu văn bản gốc có đoạn chú thích như [COMMENT ...], bạn không cần đưa phần chú thích đó vào bản dịch, chỉ dịch phần văn bản chính tả. Nếu không tự tin, hãy giữ nguyên.
5. CHỈ TRẢ VỀ JSON theo đúng định dạng được cấp { "id": "Văn bản đã dịch" }. Không kèm theo giải thích hoặc markdown block như ```json.

JSON input:
"""

def translate_batch_local(batch):
    input_json = {str(item[0]): item[1] for item in batch}
    prompt = PROMPT_TEMPLATE + json.dumps(input_json, ensure_ascii=False)
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json" 
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=300) # Tăng timeout lên 5 phút
        result = response.json()
        output_text = result.get("response", "")
        
        return json.loads(output_text)
    except Exception as e:
        print(f"\n[Lỗi Local LLM] {e}. Đảm bảo bạn đã chạy 'ollama run {MODEL_NAME}'")
        return None

def main():
    if not os.path.exists(DB_NAME):
        print("Không tìm thấy database!")
        return
        
    conn = sqlite3.connect(DB_NAME, timeout=60)
    cursor = conn.cursor()
    
    # Đếm tổng số câu còn lại để theo dõi tiến độ
    cursor.execute("SELECT COUNT(*) FROM records WHERE status = 0")
    total_to_translate = cursor.fetchone()[0]
    translated_count = 0
    start_time_process = time.time()
    
    print(f"=== KHỞI ĐỘNG DỊCH OFFLINE (GPU: RTX 4060 - MODEL: {MODEL_NAME}) ===")
    print(f"- Tổng số câu cần dịch: {total_to_translate:,}")
    
    while True:
        # Lấy 1 batch chưa dịch và khóa lại
        cursor.execute('''
            UPDATE records 
            SET status = 2 
            WHERE id IN (
                SELECT id FROM records WHERE status = 0 LIMIT ?
            )
            RETURNING id, english_text
        ''', (BATCH_SIZE,))
        
        batch = cursor.fetchall()
        conn.commit()
        
        if not batch:
            print("\nChúc mừng! Đã hoàn thành toàn bộ bản dịch.")
            break
            
        batch_start_time = time.time()
        translated_data = translate_batch_local(batch)
        
        if translated_data:
            update_data = []
            for item in batch:
                row_id = str(item[0])
                if row_id in translated_data:
                    update_data.append((translated_data[row_id], 1, MODEL_NAME, item[0]))
                else:
                    update_data.append((item[1], 1, MODEL_NAME, item[0]))
            
            cursor.executemany("UPDATE records SET translated_text = ?, status = ?, model_name = ? WHERE id = ?", update_data)
            conn.commit()
            
            translated_count += len(batch)
            elapsed_all = time.time() - start_time_process
            speed_per_min = (translated_count / elapsed_all) * 60
            progress = (translated_count / total_to_translate) * 100 if total_to_translate > 0 else 100
            
            # Tính thời gian còn lại (ETA)
            remaining_count = total_to_translate - translated_count
            eta_seconds = (remaining_count / (translated_count / elapsed_all)) if translated_count > 0 else 0
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
            
            print(f"Tiến độ: {progress:.2f}% | Đã dịch: {translated_count}/{total_to_translate} | Speed: {speed_per_min:.1f} câu/phút | ETA: {eta_str}", end="\r")
        else:
            ids = [item[0] for item in batch]
            placeholders = ','.join('?' * len(ids))
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            time.sleep(5)

    conn.close()

if __name__ == "__main__":
    main()
