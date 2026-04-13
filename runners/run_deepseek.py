import sqlite3
from core.config import DB_PATH

import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Cấu hình OpenRouter (Dùng DeepSeek-V3)
API_KEY = os.getenv("MOONSHOT_API_KEY") # Vẫn dùng key cũ bạn đã nạp $5
BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://openrouter.ai/api/v1")

if not API_KEY:
    print("Dừng: Chưa cấu hình MOONSHOT_API_KEY trong file .env")
    exit(1)

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=300)

DB_NAME = DB_PATH
# DeepSeek-V3 rất nhanh và ổn định, ta có thể chạy mẻ 300-400 dòng.
BATCH_SIZE = 300 
NUM_AGENTS = 5 

PROMPT_TEMPLATE = """
Bạn là một chuyên gia dịch thuật tiếng Việt xuất sắc cho game bóng đá Football Manager.
Luật bắt buộc:
1. TUYỆT ĐỐI KHÔNG BAO GIỜ dịch, xóa bỏ hoặc làm biến dạng các Thẻ Định Dạng (Tags). Các thẻ này vô cùng quan trọng đối với code, bao gồm:
   - Thẻ biến động trong ngoặc vuông (vd: [%person#1-I], [%team#1-nickname], v.v.).
   - Thẻ định dạng cú pháp trong ngoặc nhọn (vd: {upper}, {s}, {lower}, v.v.).
Bạn BẮT BUỘC phải sao chép nguyên xi và đặt các thẻ này vào vị trí tương ứng trong câu dịch. KHÔNG ĐƯỢC LÀM MẤT BẤT CỨ THẺ NÀO. Cấu trúc cụm từ như `{upper}[%team#1-nickname]{s}` phải được bưng nguyên vẹn vào bản dịch.
2. Dựa vào từ khóa trong thẻ để phán đoán xưng hô cho mềm mại. Ví dụ: [%person#1-I] được hiểu ngầm là 'Tôi', [%person#1-my] là 'của mình'.
3. Không dịch các từ đóng vai trò là tên riêng, địa danh, hoặc các từ VIẾT HOA HOÀN TOÀN. 
4. Trả về kết quả dưới dạng JSON object. KHÔNG kèm theo lời giải thích.

Tôi cung cấp cho bạn một chuỗi JSON gồm { "id": "Văn bản tiếng Anh" }. 
Hãy dịch sang tiếng Việt và trả về chuỗi JSON gồm { "id": "Văn bản tiếng Việt" }.
"""

async def translate_batch(batch):
    # Tạo từ điển {id: text}
    input_json = {str(item[0]): item[1] for item in batch}
    
    try:
        # Gọi DeepSeek-V3 qua OpenRouter
        response = await client.chat.completions.create(
            model="deepseek/deepseek-chat", # DeepSeek V3 (Reasoning)
            messages=[
                {"role": "system", "content": PROMPT_TEMPLATE},
                {"role": "user", "content": json.dumps(input_json, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"},
            max_tokens=8000
        )
        
        text = response.choices[0].message.content
        if not text:
            return None
            
        # Tìm và bóc tách lõi JSON
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                text = text[start_idx:end_idx]
            
            output_json = json.loads(text)
            return output_json
        except Exception:
            print(f"\n[Lỗi JSON] Không thể trích xuất JSON. Thử lại...")
            return None
            
    except Exception as e:
        err = str(e).lower()
        print(f"\n[Lỗi API] {err}")
        if "insufficient_balance" in err or "out of quota" in err:
            return "STOP_SYSTEM"
        return None

async def worker_agent(agent_name):
    print(f"[{agent_name}] Bắt đầu làm việc...")
    conn = sqlite3.connect(DB_NAME, timeout=60)
    cursor = conn.cursor()
    
    while True:
        # Lock dữ liệu
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
            print(f"[{agent_name}] Đã hết hàng. Hoàn tất toàn bộ công việc!")
            break
            
        print(f"[{agent_name}] Nhận được {len(batch)} dòng. Đang dịch...")
        translated_data = await translate_batch(batch)
        
        ids = [item[0] for item in batch]
        placeholders = ','.join('?' * len(ids))
        
        if translated_data == "STOP_SYSTEM":
            print(f"[{agent_name}] 🚨 HỆ THỐNG DỪNG: Hết số dư OpenRouter!")
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            os._exit(1)
        elif translated_data:
            update_data = []
            for item in batch:
                row_id = str(item[0])
                if row_id in translated_data:
                    update_data.append((translated_data[row_id], 1, item[0]))
                else:
                    update_data.append((item[1], 1, item[0])) 
                    
            cursor.executemany("UPDATE records SET translated_text = ?, status = ? WHERE id = ?", update_data)
            conn.commit()
            
            print(f"[{agent_name}] ✅ Dịch thành công {len(batch)} dòng!")
            await asyncio.sleep(5)
        else:
            # Revert status
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            await asyncio.sleep(20)

    conn.close()

async def main():
    print(f"🚀 Khởi chạy {NUM_AGENTS} Agent với DeepSeek-V3 qua OpenRouter (Khởi động so le)...")
    tasks = []
    for i in range(NUM_AGENTS):
        tasks.append(worker_agent(f"Agent {i+1}"))
        await asyncio.sleep(5) # Mỗi agent khởi động cách nhau 5s
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("=== KHỞI ĐỘNG HỆ THỐNG DỊCH THUẬT (DEEPSEEK V3 EDITION) ===")
    asyncio.run(main())
