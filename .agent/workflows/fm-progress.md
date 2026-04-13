---
description: Báo cáo nhanh tiến độ dịch thuật FM26
---

# FM Progress Check

Workflow này giúp kiểm tra trạng thái database và tiến độ dịch thuật hiện tại của dự án Football Manager 2026.

## Guardrails
- Không thay đổi dữ liệu trong database.
- Đảm bảo môi trường Python đã được thiết lập.

## Steps

### 1. Phân tích môi trường
Kiểm tra file cấu hình và database:
- Kiểm tra file `.env` hoặc `core/config.py` để xác định đường dẫn DB.
- Kiểm tra sự tồn tại của `scripts/diagnostics/check_progress.py`.

### 2. Thực thi kiểm tra // turbo
Chạy script kiểm tra tiến độ:
```powershell
python scripts/diagnostics/check_progress.py
```

### 3. Hiển thị báo cáo
AI sẽ tóm tắt kết quả:
- Tổng số câu.
- Số câu đã hoàn thành (kèm tỷ lệ %).
- Breakdown theo Model (nếu có).
- Dự đoán thời gian hoàn thành (nếu cần).

## Principles
- Luôn báo cáo số liệu chính xác từ database.
- Cảnh báo nếu có quá nhiều bản ghi "Processing" bị treo.
