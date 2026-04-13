import sqlite3
from core.config import DB_PATH

import os
import asyncio
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Cấu hình Moonshot AI (Kimi)
API_KEY = os.getenv("MOONSHOT_API_KEY")
BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")

if not API_KEY:
    print("Dừng: Chưa cấu hình MOONSHOT_API_KEY trong file .env")
    exit(1)

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=600)

DB_NAME = DB_PATH
# Moonshot (K2.5) thường có giới hạn TPM/RPM cao hơn nếu đã nạp tiền.
# Bạn có thể nâng BATCH_SIZE lên để tối ưu throughput.
BATCH_SIZE = 5 
NUM_AGENTS = 1 

PROMPT_TEMPLATE = """
Bạn là một chuyên gia dịch thuật tiếng Việt xuất sắc cho game bóng đá Football Manager.
Luật bắt buộc:
1. TUYỆT ĐỐI KHÔNG BAO GIỜ dịch, xóa bỏ hoặc làm biến dạng các Thẻ Định Dạng (Tags). Các thẻ này vô cùng quan trọng đối với code, bao gồm:
   - Thẻ biến động trong ngoặc vuông (vd: [%person#1-I], [%team#1-nickname], v.v.).
   - Thẻ định dạng cú pháp trong ngoặc nhọn (vd: {upper}, {s}, {lower}, v.v.).
Bạn BẮT BUỘC phải sao chép nguyên xi và đặt các thẻ này vào vị trí tương ứng trong câu dịch. KHÔNG ĐƯỢC LÀM MẤT BẤT CỨ THẺ NÀO. Cấu trúc cụm từ như `{upper}[%team#1-nickname]{s}` phải được bưng nguyên vẹn vào bản dịch.
2. Dựa vào từ khóa trong thẻ để phán đoán xưng hô cho mềm mại. Ví dụ: [%person#1-I] được hiểu ngầm là 'Tôi', [%person#1-my] là 'của mình'.
3. Không dịch các từ đóng vai trò là tên riêng, địa danh, hoặc các từ VIẾT HOA HOÀN TOÀN. 
4. Nếu văn bản gốc có đoạn chú thích như [COMMENT ...], bạn không cần đưa phần chú thích đó vào bản dịch, chỉ dịch phần văn bản chính tả. Nếu không tự tin, hãy giữ nguyên.
5. Trả về kết quả dưới dạng JSON object.

Tôi cung cấp cho bạn một chuỗi JSON gồm { "id": "Văn bản tiếng Anh" }. 
Hãy dịch sang tiếng Việt và trả về chuỗi JSON gồm { "id": "Văn bản tiếng Việt" }.
"""

async def translate_batch(batch):
    # Tạo từ điển {id: text}
    input_json = {str(item[0]): item[1] for item in batch}
    
    try:
        # Gọi Moonshot API (Kimi) theo chuẩn OpenAI
        response = await client.chat.completions.create(
            model="moonshotai/kimi-k2.5", # Định danh đầy đủ trên OpenRouter
            messages=[
                {"role": "system", "content": PROMPT_TEMPLATE},
                {"role": "user", "content": json.dumps(input_json, ensure_ascii=False)}
            ],
            response_format={"type": "json_object"}, # Kimi hỗ trợ chế độ JSON
            max_tokens=16000 # Nâng giới hạn để chứa 800 dòng dịch
        )
        
        text = response.choices[0].message.content
        if not text:
            return None
            
        # Tìm vị trí JSON thực sự (bắt đầu bằng { và kết thúc bằng })
        try:
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                text = text[start_idx:end_idx]
            
            output_json = json.loads(text)
            return output_json
        except Exception:
            print(f"\n[Lỗi JSON] Không thể trích xuất JSON. Thử lại...")
            print(f"--- PREVIEW ---")
            print(text[:500] if text else "None")
            print(f"---------------")
            return None
    except json.JSONDecodeError as e:
        print(f"\n[Lỗi JSON] Dữ liệu trả về không đúng định dạng. Đang thử lại...")
        # In ra 100 ký tự đầu để debug nếu cần
        # print(f"Preview: {text[:100]}...") 
        return None
    except Exception as e:
        err = str(e).lower()
        print(f"\n[Lỗi API] {err}")
        # Xử lý lỗi Rate Limit hoặc hết tiền (Quota)
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
            
        print(f"[{agent_name}] Nhận được {len(batch)} dòng. Bắt đầu dịch...")
        translated_data = await translate_batch(batch)
        
        ids = [item[0] for item in batch]
        placeholders = ','.join('?' * len(ids))
        
        if translated_data == "STOP_SYSTEM":
            print(f"[{agent_name}] 🚨 HỆ THỐNG DỪNG: Hết số dư hoặc lỗi nghiêm trọng!")
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
            
            # Giải lao ngắn giữa các batch
            await asyncio.sleep(5)
        else:
            # Revert status nếu lỗi
            cursor.execute(f"UPDATE records SET status = 0 WHERE id IN ({placeholders})", ids)
            conn.commit()
            await asyncio.sleep(30)

    conn.close()

async def main():
    print(f"🚀 Khởi chạy {NUM_AGENTS} Agent với Moonshot AI...")
    tasks = [worker_agent(f"Agent {i+1}") for i in range(NUM_AGENTS)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("=== KHỞI ĐỘNG HỆ THỐNG DỊCH THUẬT (MOONSHOT EDITION) ===")
    asyncio.run(main())
