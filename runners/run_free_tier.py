import sqlite3
from core.config import DB_PATH

import os
import asyncio
import json
import re
from google import genai
from dotenv import load_dotenv
import sys
import time
from core.sot_engine import SOTEngine

# Đảm bảo in được tiếng Việt trên console Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load biến môi trường
load_dotenv()

# SỬ DỤNG KEY MIỄN PHÍ RIÊNG
API_KEY = os.getenv("GEMINI_API_KEY_FREE") 
if not API_KEY:
    print("Dừng: Chưa cấu hình GEMINI_API_KEY_FREE trong file .env")
    exit(1)

client = genai.Client(api_key=API_KEY)

# Khởi tạo SOT Engine nếu được yêu cầu
SOT_INSTANCE = SOTEngine() if os.getenv("USE_SOT") == "1" else None
if SOT_INSTANCE:
    print("[*] SOT Engine đã sẵn sàng trong Runner.")

DB_NAME = DB_PATH

# --- CẤU HÌNH TỐI ƯU SIÊU CẤP CHO FREE TIER ---
# Dựa trên: 15 RPM, 250k TPM, 500 RPD
NUM_AGENTS = 5     # 5 Agent chạy gối đầu nhau để duy trì RPM ổn định
FETCH_CANDIDATES = 1000 # Tăng kho nguyên liệu để thuật toán nhặt được nhiều câu hơn
WAIT_BETWEEN_BATCH = 20 # Nghỉ 20 giây mỗi Agent (Tổng RPM toàn hệ thống ~12-14, cực kỳ tối ưu)
MAX_CHARS_PER_BATCH = 35000 # Đẩy sát trần: 35k ký tự (~8000 tokens) để tận dụng tối đa TPM.

# Biến toàn cục để theo dõi tiến độ
STATS = {
    "total": 0,
    "done": 0,
    "start_time": 0
}

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite-preview",         # Sếp sòng: Chịu tải chính (15 RPM, 500 RPD)
    "gemini-2.5-flash-lite",                 # Dự phòng 1 (10 RPM, 20 RPD)
    "gemini-2.5-flash",                      # Dự phòng 2 (5 RPM, 20 RPD)
    "gemini-2.0-flash-lite-preview-09-2024", # Dự phòng 3
    "gemini-1.5-flash-lite"                  # Ôm chót
]

PROMPT_TEMPLATE = """
Bạn là một chuyên gia dịch thuật tiếng Việt cực kỳ cẩn thận cho game Football Manager.
NGÔN NGỮ: Chuyên nghiệp, sang trọng nhưng gần gũi trong môi trường bóng đá.

LUẬT BẮT BUỘC (Vi phạm sẽ làm hỏng file game):
1. QUY TẮC XƯNG HÔ (Diction & Pronouns):
   - Người quản lý (Manager/You): Luôn dùng "Ngài". Tuyệt đối không dùng "Bạn", "Anh", "Cậu", "Hắn", "Y".
   - Người nói (I): Luôn dùng "Tôi".
   - Nam giới (He/Him/His): "Anh ấy" hoặc "Anh ta".
   - Nữ giới (She/Her/Hers): "Cô ấy" hoặc "Cô ta".
   - Sự vật (It/Its): "Nó / Của nó".
   - Đám đông (They/Them/Their): "Họ / Của họ".

2. QUY TẮC THẺ (Tag Logic):
   - Thẻ Square [%...]: Giữ nguyên thẻ dữ liệu (team, cash, number, stadium...). Việt hóa hậu tố đại từ: [%person#1-you] -> [%person#1-Ngài], [%male#1-him] -> [%male#1-anh ấy]. Xóa khoảng trắng dư thừa trong thẻ: [% person] -> [%person].
   - Thẻ Curly {...}: Việt hóa: {an}/{a} -> {một}, {An}/{A} -> {Một}, {scoreline} -> {một tỷ số}, {ordinal} -> {thứ}.
   - Sở hữu cách: [%team#1]{s} -> của [%team#1].
   - Thẻ {the} -> {}.
   - Số lượng dấu '[' và ']' hoặc '{' và '}' phải khớp tuyệt đối với câu gốc.

3. DỌN DẸP KỸ THUẬT (Cleanup):
   - XÓA BỎ hoàn toàn các đoạn chú thích [COMMENT ...] hoặc [COMMENT: ...]. Không được dịch hay giữ lại thẻ này.
   - Viết hoa đầu câu và sau dấu câu (. ! ?). Nếu thẻ nhân xưng đứng đầu câu, viết hoa hậu tố: [%person#1-Ngài].
   - Khử lặp từ (ví dụ: "của nó của nó"), sửa lỗi dính chữ (tôiđã -> tôi đã).
   - Không dịch tên riêng, địa danh, hoặc các từ VIẾT HOA HOÀN TOÀN.

4. CHỈ TRẢ VỀ JSON ĐÚNG QUY CHUẨN. Tuyệt đối không dùng markdown block (```json) và không giải thích thêm.

Tôi cung cấp cho bạn một chuỗi JSON gồm { "id": "Văn bản tiếng Anh" }. 
Hãy dịch sang tiếng Việt và trả về chuỗi JSON gồm { "id": "Văn bản tiếng Việt" }:

JSON input:
"""

async def translate_batch(batch, agent_name):
    input_json = {str(item[0]): item[1] for item in batch}
    
    current_prompt = PROMPT_TEMPLATE
    
    # Tích hợp SOT Context nếu có
    if SOT_INSTANCE:
        sample_query = " ".join([item[1] for item in batch[:10]])
        sot_context = SOT_INSTANCE.query_instruction(sample_query)
        if sot_context:
            current_prompt += f"\n[HƯỚNG DẪN BỔ SUNG TỪ DATABASE GỐC (SOT)]:\n{sot_context}\n\n"

    prompt = current_prompt + json.dumps(input_json, ensure_ascii=False)
    
    for model_name in FALLBACK_MODELS:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            text = response.text
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                try:
                    text = match.group(0)
                    output_json = json.loads(text)
                    return output_json, model_name
                except json.JSONDecodeError:
                    if not text.strip().endswith('}'):
                        print(f"\n[{agent_name}] [Lỗi JSON] Văn bản bị cắt cụt do vượt mốc giới hạn Output! (Cách ly Status 3)")
                    else:
                        print(f"\n[{agent_name}] [Lỗi JSON] Cú pháp lỗi. (Cách ly Status 3)")
                    return "ISOLATE_ERROR", None
            else:
                print(f"\n[{agent_name}] [Lỗi Định dạng] AI trả lời vô nghĩa, không chứa JSON. (Cách ly Status 3)")
                return "ISOLATE_ERROR", None
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "resource_exhausted" in err:
                print(f"\n[{agent_name}] [Limit - {model_name}] Đợi hồi phục...")
                await asyncio.sleep(30)
                continue
            if "quota" in err or "402" in err:
                return "STOP_SYSTEM", None
                
            # Bắt lỗi Service API / Network (Trả về để làm lại)
            if any(k in err for k in ["503", "500", "504", "502", "timeout", "network", "connection", "deadline"]):
                print(f"\n[{agent_name}] [Lỗi Service API] Quá tải máy chủ ({err[:50]}...). (Đẩy về Status 0 thử lại)")
                return "RETRY_LATER", None
                
            print(f"\n[{agent_name}] [Lỗi API] {err[:100]}... (Đẩy về Status 0 thử lại)")
            return "RETRY_LATER", None
            
    # Trường hợp tất cả Models đều 429
    return "RETRY_LATER", None

async def worker_agent(agent_name):
    print(f"[{agent_name}] Đang khởi động chế độ Tiết Kiệm (Free Tier)...")
    conn = sqlite3.connect(DB_NAME, timeout=30)
    cursor = conn.cursor()
    
    while True:
        # Bước 1: Kéo một lượng lớn câu (500 câu) để làm kho nguyên liệu
        cursor.execute("SELECT id, english_text FROM records WHERE status = 0 LIMIT ?", (FETCH_CANDIDATES,))
        candidate_batch = cursor.fetchall()
        
        if not candidate_batch:
            print(f"\n[{agent_name}] Đã hết hàng!")
            break
            
        # Bước 2: Gom mẻ (Batch) động dựa trên hạn mức ký tự MAX_CHARS_PER_BATCH
        batch = []
        current_chars = 0
        for item in candidate_batch:
            text_len = len(item[1])
            if not batch: # Bắt buộc nhét ít nhất 1 dòng đầu tiên, dù nó siêu dài
                batch.append(item)
                current_chars += text_len
            else:
                if current_chars + text_len > MAX_CHARS_PER_BATCH:
                    break # Chặt mẻ tại đây, số câu còn dư nhường Agent khác
                batch.append(item)
                current_chars += text_len

        # Bước 3: Lock (status = 2) dành riêng cho các ID đã được duyệt độ dài
        ids = [item[0] for item in batch]
        placeholders = ','.join('?' * len(ids))
        cursor.execute(f"UPDATE records SET status = 2 WHERE id IN ({placeholders})", ids)
        conn.commit()
            
        print(f"[{agent_name}] Đang xử lý {len(batch)} dòng (Gói: {current_chars} ký tự)...")
        translated_data, model_used = await translate_batch(batch, agent_name)
        
        ids = [item[0] for item in batch]
        placeholders = ','.join('?' * len(ids))
        
        if translated_data == "STOP_SYSTEM":
            print(f"[{agent_name}] 🚨 ĐÃ HẾT QUOTA! Dừng hệ thống.")
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            break
            
        elif translated_data == "ISOLATE_ERROR":
            # Lỗi liên quan đến JSON gãy hoặc báo data ảo -> Trục xuất (Cách ly)
            cursor.execute(f"UPDATE records SET status = 3 WHERE id IN ({placeholders})", ids)
            conn.commit()
            print(f"[{agent_name}] ⚠️ Đã cách ly {len(batch)} câu sang Status 3. Thử mẻ mới...")
            await asyncio.sleep(WAIT_BETWEEN_BATCH)
            
        elif translated_data == "RETRY_LATER" or not translated_data:
            # Lỗi đứt cáp, mạng, Google ngáp -> Nhả ra lại vào kho để thử lại sau
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            print(f"[{agent_name}] 🔄 Trả lại {len(batch)} câu về kho (Status 0) do lỗi giao tiếp API.")
            await asyncio.sleep(WAIT_BETWEEN_BATCH)
            
        else:
            # Thành công rực rỡ
            update_data = []
            for item in batch:
                row_id = str(item[0])
                val = translated_data.get(row_id, item[1])
                update_data.append((val, 1, model_used, item[0]))
                    
            cursor.executemany("UPDATE records SET translated_text = ?, status = ?, model_name = ? WHERE id = ?", update_data)
            conn.commit()
            
            STATS["done"] += len(batch)
            elapsed = time.time() - STATS["start_time"]
            speed = (STATS["done"] / elapsed) * 60
            progress = (STATS["done"] / STATS["total"]) * 100 if STATS["total"] > 0 else 0
            
            remaining = STATS["total"] - STATS["done"]
            eta_s = (remaining / (STATS["done"] / elapsed)) if STATS["done"] > 0 else 0
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_s))

            print(f"\n[{agent_name}] Thành công! Tiến độ: {progress:.2f}% | Dịch: {STATS['done']}/{STATS['total']} | Speed: {speed:.1f} dòng/phút | ETA: {eta_str}")
            
            await asyncio.sleep(WAIT_BETWEEN_BATCH)

    conn.close()

async def main():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM records WHERE status = 0")
    STATS["total"] = c.fetchone()[0]
    STATS["start_time"] = time.time()
    conn.close()
    
    print(f"=== KHỞI ĐỘNG HỆ THỐNG FREE TIER VỚI {NUM_AGENTS} AGENTS ===")
    print(f"- Tổng số câu cần dịch: {STATS['total']:,}")
    
    tasks = [worker_agent(f"FREE_AGENT_{i+1}") for i in range(NUM_AGENTS)]
    await asyncio.gather(*tasks)

    # In kết quả sau thi kết thúc phiên chạy
    print(f"\n=== BẢNG TỔNG KẾT PHIÊN CHẠY ===")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM records WHERE status = 0")
    remain = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM records WHERE status = 1")
    done = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM records WHERE status = 3")
    errors = c.fetchone()[0]
    
    print(f"✅ Hoàn thành (Status 1): {done:,}")
    print(f"🛑 Từ chối/Lỗi (Status 3): {errors:,}")
    print(f"⏳ Chưa xử lý (Status 0): {remain:,}")
    conn.close()
if __name__ == "__main__":
    asyncio.run(main())
