---
description: Kích hoạt Agent dịch thuật cho dự án FM26
---

# FM Translate

Workflow này điều phối việc chạy các Agent dịch thuật để tiếp tục dự án translation.

## Guardrails
- Kiểm tra kết nối Internet và API Keys trong `.env`.
- Luôn hỏi xác nhận trước khi chạy với Model tốn phí (Pro Tier).

## Steps

### 1. Xác định cấu hình
Hỏi người dùng:
- Bạn muốn chạy bản **Free Tier** hay **Pro Tier**?
- Số lượng bản ghi muốn dịch trong đợt này?

### 2. Kiểm tra Ready State
- Kiểm tra file `.env` đã có đầy đủ key chưa.
- Kiểm tra database có bản ghi nào cần dịch không (status = 0).

### 3. Thực thi // turbo
Chạy script tương ứng:
- Nếu Free Tier: `python 2_run_agents.py --model free_tier`
- Nếu Pro: `python 2_run_agents.py --model pro_tier`
- **Lưu ý:** Trên Windows, nên dùng `$env:PYTHONUTF8=1;` trước lệnh để tránh lỗi font.

### 4. Giám sát
- Theo dõi log đầu ra qua `command_status`.
- Nếu gặp lỗi Crash hoặc Quota Limit, hãy dừng lại và ghi log vào `.agent/logs/error-today.txt`.
- Cập nhật tiến độ định kỳ cho người dùng.

### 5. Tạm dừng & Dọn dẹp // turbo
Khi người dùng yêu cầu dừng hoặc tiến trình bị crash:
- Dừng process đang chạy.
- Chạy script reset để trả lại các bản ghi đang dở dang về hàng đợi:
  ```powershell
  python scripts/maintenance/reset_status.py
  ```

## Principles
- Đảm bảo tuân thủ `rules.md` (Persona "Ngài", tag hệ thống).
- Ưu tiên tính ổn định hơn tốc độ.
