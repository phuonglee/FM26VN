---
description: Tự động sửa lỗi và nâng cao điểm chất lượng (Rate < 1.0)
---

# FM Fix (Quality Recovery)

Workflow này hỗ trợ rà soát và tự động sửa các lỗi phổ biến để nâng cao điểm chất lượng cho bản dịch dựa trên các quy tắc mới nhất tại `rules.md`.

## Guardrails
- Đảm bảo môi trường xử lý UTF-8: `$env:PYTHONUTF8=1`.
- Luôn báo cáo số lượng bản ghi bị ảnh hưởng trước và sau khi fix.
- Khuyến khích chạy `--dry-run` trước khi áp dụng `--fix` thực sự.

## Steps

### 1. Phân tích hiện trạng
Kiểm tra database để xem có bao nhiêu bản ghi có `Rate < 1.0` và phân loại lỗi:
```powershell
python scripts/diagnostics/check_progress.py
python scratch/error_summary.py
```

### 2. Thực thi sửa lỗi tự động // turbo
Chạy lần lượt các script "phẫu thuật" chuyên sâu:

```powershell
# BƯỚC A: Việt hóa hậu tố đại từ trong thẻ (e.g. [%-I] -> [%-Tôi])
python scripts/fixes/fix_tag_suffixes.py --fix

# BƯỚC B: Khôi phục các thẻ dữ liệu bị mất (team/club hidden tags)
python scripts/fixes/fix_missing_tags.py --fix

# BƯỚC C: Sửa lỗi xưng hô 'anh' dựa trên ngữ cảnh thẻ tiếng Anh
python scripts/fixes/fix_anh_pronoun.py --fix

# BƯỚC D: Sửa lỗi lặp từ và các cấu trúc tồn dư khác
python scripts/fixes/surgical_fix_residuals.py
```

### 3. Kiểm định lại kết quả // turbo
Cập nhật lại điểm số (Rate) cho các bản ghi vừa sửa hoặc toàn bộ database:
```powershell
# Chấm điểm nhanh cho các câu vừa dịch/sửa
python scripts/database/reevaluate_new.py

# HOẶC chấm điểm lại toàn bộ database (khuyên dùng sau khi fix lớn)
python scripts/database/reevaluate_all.py
```

### 4. Hiển thị báo cáo cuối cùng
Xác nhận chất lượng bản dịch đã được cải thiện:
```powershell
python scripts/diagnostics/check_progress.py
```

## Principles
- **Linguistic Context:** Ưu tiên sử dụng thẻ gốc tiếng Anh để xác định đại từ tương ứng (Ngài/Tôi/Anh ấy).
- **Tag Integrity:** Tuyệt đối không xóa thẻ, chỉ chèn thêm hoặc sửa hậu tố sau dấu gạch ngang `-`.
- **Optimization:** Sử dụng các script reevaluate tối ưu để tiết kiệm thời gian vận hành.
