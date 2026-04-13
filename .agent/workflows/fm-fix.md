---
description: Tự động sửa lỗi và nâng cao điểm chất lượng (Rate < 1.0)
---

# FM Fix (Quality Recovery)

Workflow này hỗ trợ rà soát và tự động sửa các lỗi phổ biến để nâng cao điểm chất lượng cho bản dịch.

## Guardrails
- Phải chạy `runners/run_reviewer.py` trước khi thực hiện để có số liệu Rate mới nhất.
- Luôn báo cáo số lượng bản ghi bị ảnh hưởng trước và sau khi fix.

## Steps

### 1. Phân tích hiện trạng
Kiểm tra database để xem có bao nhiêu bản ghi có `Rate < 1.0`:
```powershell
python scripts/diagnostics/check_progress.py
```

### 2. Thực thi sửa lỗi tự động // turbo
Chạy lần lượt các script "phẫu thuật" để xử lý các lỗi lặp từ, cấu trúc xưng hô và thẻ tag:
```powershell
# Sửa lỗi lặp từ và cấu trúc câu
python scripts/fixes/surgical_fix_residuals.py

# Sửa cấu trúc đại từ cho Manager
python scripts/fixes/fix_pronoun_structure.py
```

### 3. Kiểm định lại kết quả // turbo
Sau khi sửa, cần chấm điểm lại toàn bộ để cập nhật Rate lên 1.0:
```powershell
python runners/run_reviewer.py
```

### 4. Hiển thị báo cáo cuối cùng
Kiểm tra lại tiến độ để xác nhận số câu lỗi đã giảm xuống:
```powershell
python scripts/diagnostics/check_progress.py
```

## Principles
- **Chính xác tuyệt đối:** Chỉ sửa những gì được Regex định nghĩa an toàn.
- **Không làm hỏng thẻ:** Luôn giữ nguyên thẻ dữ liệu game.
- **Tự động hóa:** Giảm thiểu việc sửa thủ công bằng các script chuyên biệt.
