# Football Manager 2026 (FM26) Translation Project

Dự án dịch thuật tự động cho Football Manager 2026 sử dụng Agentic AI Pipeline.

## 🏗 Cấu trúc thư mục

- **`core/`**: Chứa các script cốt lõi của pipeline (Import, Export, Reporter).
  - `config.py`: Quản lý cấu hình tập trung (đường dẫn Database, môi trường).
- **`runners/`**: Chứa các agent runner riêng biệt cho từng loại Model/Provider (Deepseek, GPT, Moonshot, v.v.).
- **`scripts/`**: Các công cụ hỗ trợ vận hành.
  - `diagnostics/`: Kiểm tra sức khỏe dữ liệu, phân tích tiến độ.
  - `fixes/`: Sửa lỗi dữ liệu, chuẩn hóa tags, xử lý hậu kỳ.
  - `migrations/`: Trích xuất và đồng bộ hóa dữ liệu.
- **`data/`**: Lưu trữ Database chính (`database.sqlite`) và các quy tắc dịch thuật (`rules.md`).
- **`archive/`**: Lưu trữ lịch sử (backups, script cũ, logs báo cáo).
- **`release/`**: Chứa các bản export LTF cuối cùng.

## 🚀 Cách vận hành

### 1. Chạy Agent Dịch thuật
Sử dụng script trung tâm để chạy các mô hình khác nhau:

```bash
# Chạy mặc định
python 2_run_agents.py --model default

# Chạy với Deepseek
python 2_run_agents.py --model deepseek

# Chạy với GPT-mini
python 2_run_agents.py --model gpt_mini

# Chạy kèm SOT Engine (Khuyên dùng để tăng chất lượng)
python 2_run_agents.py --model free_tier --use-sot
```

Các model hỗ trợ: `default`, `deepseek`, `free_tier`, `gpt_mini`, `local`, `moonshot`.

### 2. Hệ thống Tri thức (Source of Truth - SOT)
Để đảm bảo AI dịch đồng nhất và dùng đúng xưng hô xị xò, cần nạp tri thức vào SOT trước khi chạy:
- **Build Index**: `python scripts/database/build_sot_index.py` (Nạp quy tắc từ `rules.md` và các bản dịch 1.0 vào bộ nhớ vector).

### 3. Kiểm soát Chất lượng (Quality Control)
Sử dụng "The Lean Judge" để chấm điểm tự động và cách ly lỗi:
- **Chấm điểm hàng loạt**: `python runners/run_reviewer.py` (Tự động gán `rate` và `status 3` cho các câu sai thẻ game hoặc sai xưng hô).

### 4. Các lệnh hữu ích khác
- **Chẩn đoán tiến độ**: `python scripts/diagnostics/check_progress.py`
- **Tự động sửa xưng hô**: `python scripts/fixes/auto_fix_pronouns.py`
- **Xuất file LTF**: `python core/3_export_to_ltf.py`

## ⚙️ Cấu hình (Configuration)

Tất cả các script hiện đều sử dụng `core.config.DB_PATH` để kết nối tới database. 
- Nếu file `database.sqlite` nằm trong `data/`, hệ thống sẽ ưu tiên sử dụng.
- Nếu file nằm ở thư mục gốc (do lỗi chiếm dụng tài nguyên), hệ thống sẽ tự động fallback về thư mục gốc để đảm bảo không bị gián đoạn.

---
*Dự án được tối ưu hóa bởi Antigravity AI.*
