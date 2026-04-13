import sqlite3
from core.config import DB_PATH

import os
import asyncio
import json
import re
from google import genai
from dotenv import load_dotenv

import time

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY or API_KEY == "your_api_key_here":
    print("Dừng: Chưa cấu hình GEMINI_API_KEY trong file .env")
    exit(1)

client = genai.Client(api_key=API_KEY)

DB_NAME = DB_PATH
# --- CẤU HÌNH SIÊU TỐC ĐỘ (MAX PERFORMANCE) ---
# Tận dụng tối đa 4,000,000 TPM và 4,000 RPM của Paid Tier 1
NUM_AGENTS = 50  # 50 Agents chạy song song tối đa hóa băng thông
BATCH_SIZE = 60  # Giữ ở mức 60 để đảm bảo Output không bao giờ trạm trần 8k token (gây lỗi JSON)
# Tổng thông lượng dự kiến: ~4,000 - 5,000 câu / phút (Dứt điểm 250k câu trong ~1 tiếng)
# Biến toàn cục để theo dõi tiến độ
STATS = {
    "total": 0,
    "done": 0,
    "start_time": 0
}

# Pay-As-You-Go setup: 2.0-flash-lite bị khóa với user mới, dùng 2.5-flash-lite là chuẩn nhất hiện tại
FALLBACK_MODELS = [
    "gemini-2.5-flash-lite", # Giá rẻ đáy: $0.10 (In) / $0.40 (Out)
    "gemini-3.1-flash-lite-preview",
    "gemini-2.0-flash", 
    "gemini-2.5-flash"
]

PROMPT_TEMPLATE = """
Bạn là một chuyên gia dịch thuật tiếng Việt xuất sắc cho game bóng đá Football Manager.
Luật bắt buộc:
1. TUYỆT ĐỐI KHÔNG BAO GIỜ dịch, thay đổi, xóa bỏ hoặc làm biến dạng các Thẻ Định Dạng (Tags). Các thẻ này vô cùng quan trọng đối với code, bao gồm:
   - Thẻ biến động trong ngoặc vuông (vd: [%person#1-I], [%team#1-nickname], v.v.).
   - LỖI THƯỜNG GẶP CẦN TRÁNH: Tuyệt đối không dịch chữ bên trong ngoặc vuông. Ví dụ: KHÔNG ĐƯỢC biến [%male#1-I] thành [%male#1-Tôi]. Bạn phải giữ im bản gốc là [%male#1-I].
   - Thẻ định dạng cú pháp trong ngoặc nhọn (vd: {upper}, {s}, {lower}, {CAPS}, v.v.). BẠN PHẢI GIỮ NGUYÊN THẺ NÀY, KHÔNG ĐƯỢC XÓA ĐỂ TỰ VIẾT HOA.
Bạn BẮT BUỘC phải sao chép nguyên xi và đặt các thẻ này vào vị trí tương ứng trong câu dịch. KHÔNG ĐƯỢC LÀM MẤT HOẶC MÓP MÉO BẤT CỨ THẺ NÀO.
2. Dựa vào từ khóa trong thẻ để phán đoán xưng hô bên ngoài mạch văn cho mềm mại. Ví dụ: thấy [%person#1-I] thì tự hiểu nội dung ngoài thẻ là xưng 'Tôi'.
3. Không dịch các từ đóng vai trò là tên riêng, địa danh, hoặc các từ VIẾT HOA HOÀN TOÀN. 
4. Nếu văn bản gốc có đoạn chú thích như [COMMENT ...], bạn không cần đưa phần chú thích đó vào bản dịch, chỉ dịch phần văn bản chính tả. Nếu không tự tin, hãy giữ nguyên.
5. CHỈ TRẢ VỀ JSON theo đúng định dạng được cấp. Không kèm theo giải thích hoặc markdown block như ```json.

Tôi cung cấp cho bạn một chuỗi JSON gồm { "id": "Văn bản tiếng Anh" }. 
Hãy dịch sang tiếng Việt và trả về chuỗi JSON gồm { "id": "Văn bản tiếng Việt" }:

JSON input:
"""

async def translate_batch(batch):
    # Tạo từ điển {id: text}
    input_json = {str(item[0]): item[1] for item in batch}
    prompt = PROMPT_TEMPLATE + json.dumps(input_json, ensure_ascii=False)
    
    for model_name in FALLBACK_MODELS:
        try:
            # Gọi Gemini async client mới 
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            text = response.text
            # Sử dụng Regex để tìm khối { ... } trong trường hợp AI trả lời thừa chữ
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                text = match.group(0)
                output_json = json.loads(text)
                return output_json, model_name
            else:
                print(f"\n[Lỗi Định dạng] AI không trả về JSON hợp lệ. Nội dung: {text[:100]}...")
                return None, None
        except json.JSONDecodeError as e:
            print(f"\n[Lỗi JSON] Không thể phân tích cú pháp. Sẽ thử lại...")
            return None, None
        except Exception as e:
            err = str(e)
            if "429" in err or "resource_exhausted" in err.lower() or "resource exhausted" in err.lower():
                # Bắt lỗi 429 (hết token phút/ngày trên 1 model)
                print(f"\n[Rate Limit - {model_name}] Đã hết phiên dịch tạm thời (429). Chuyển sang model tiếp theo...")
                continue # Nhảy sang model tiếp theo trong FALLBACK_MODELS vòng lặp
            
            print(f"\n[Lỗi API] {model_name}: {err[:150]}...")
            # CHỈ dừng hẳn hệ thống nếu thực sự hết Quota ngày (Daily Quota) mà không tìm được lối thoát
            if "quota" in err.lower() and "exhausted" not in err.lower():
                return "STOP_SYSTEM", None
            return None, None
            
    # Nếu chạy qua toàn bộ list FALLBACK_MODELS mà cái nào cũng vướng 429 thì chịu thua, nghỉ 60s
    print(f"\n[Auto-Switch] Toàn bộ {len(FALLBACK_MODELS)} model đều bị kiệt sức! Agent cần nghỉ ngơi 60s.")
    return None, None

async def worker_agent(agent_name):
    print(f"[{agent_name}] Bắt đầu làm việc...")
    conn = sqlite3.connect(DB_NAME, timeout=30) # time out cao để nhiều agent không tranh giành CSDL
    cursor = conn.cursor()
    
    while True:
        # Lấy 1 batch CHƯA DỊCH (0), VÀ LẬP TỨC AUTO KHÓA CHÚNG (chuyển sang trạng thái ĐANG DỊCH - 2) bằng cơ chế Atomic Lock để Agent khác không nhảy vào cướp việc.
        cursor.execute('''
            UPDATE records 
            SET status = 2 
            WHERE id IN (
                SELECT id FROM records WHERE status = 0 LIMIT ?
            )
            RETURNING id, english_text
        ''', (BATCH_SIZE,))
        
        batch = cursor.fetchall()
        conn.commit() # BẮT BUỘC PHẢI COMMIT ĐỂ NHẢ KHÓA (RELEASE LOCK) CHO DATABASE TRƯỚC KHI GỌI API
        if not batch:
            print(f"[{agent_name}] Đã hết hàng. Hoàn tất toàn bộ công việc!")
            break
            
        print(f"[{agent_name}] Nhận được {len(batch)} dòng. Bắt đầu dịch...")
        translated_data, model_used = await translate_batch(batch)
        
        ids = [item[0] for item in batch]
        placeholders = ','.join('?' * len(ids))
        
        if translated_data == "STOP_SYSTEM":
            print(f"[{agent_name}] 🚨 HỆ THỐNG DỪNG KHẨN CẤP: Chạm giới hạn (Limit) hoặc kiệt sức (Exhausted/503)!")
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            os._exit(1)
        elif translated_data and model_used:
            # Cập nhật database thành DỊCH THÀNH CÔNG (1)
            update_data = []
            for item in batch:
                row_id = str(item[0])
                if row_id in translated_data:
                    update_data.append((translated_data[row_id], 1, model_used, item[0]))
                else:
                    # Fallback neu AI quen
                    update_data.append((item[1], 1, model_used, item[0])) 
                    
            cursor.executemany("UPDATE records SET translated_text = ?, status = ?, model_name = ? WHERE id = ?", update_data)
            conn.commit()
            
            # Cập nhật tiến độ
            STATS["done"] += len(batch)
            elapsed = time.time() - STATS["start_time"]
            speed_per_min = (STATS["done"] / elapsed) * 60
            progress = (STATS["done"] / STATS["total"]) * 100 if STATS["total"] > 0 else 100
            
            # Tính thời gian còn lại (ETA)
            remaining_count = STATS["total"] - STATS["done"]
            eta_seconds = (remaining_count / (STATS["done"] / elapsed)) if STATS["done"] > 0 else 0
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))
            
            print(f"Tiến độ hệ thống: {progress:.2f}% | Đã dịch: {STATS['done']}/{STATS['total']} | Speed: {speed_per_min:.1f} câu/phút | ETA: {eta_str}", end="\r")
            
            # Agent hoàn thành nhiệm vụ, giải lao 8 giây
            await asyncio.sleep(8)
        else:
            # Trả số lượng dòng này về lại trạng thái CHƯA DỊCH (0) để lát Agent khác làm
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            await asyncio.sleep(60)

    conn.close()

async def main():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM records WHERE status = 0")
    STATS["total"] = c.fetchone()[0]
    STATS["start_time"] = time.time()
    conn.close()
    
    print(f"=== KHỞI ĐỘNG HỆ THỐNG {NUM_AGENTS} AGENT DỊCH THUẬT ===")
    print(f"- Tổng số câu cần xử lý: {STATS['total']:,}")
    
    tasks = [worker_agent(f"Agent {i+1}") for i in range(NUM_AGENTS)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
