# FM26 Scripts Directory

Thư mục này chứa các công cụ hỗ trợ cho dự án dịch thuật Football Manager 2026. Các kịch bản đã được đánh giá và lọc ra những công cụ hữu ích nhất.

## 📊 Diagnostics (Chẩn đoán)
Các công cụ kiểm tra dữ liệu và theo dõi tiến độ.

- `check_progress.py`: Xem tóm tắt tiến độ dịch thuật (bao nhiêu dòng đã xong, bao nhiêu dòng còn lại).
- `diagnose_db.py`: Kiểm tra chi tiết các vấn đề trong Database SQLite.
- `check_all_statuses.py`: Thống kê số lượng bản ghi theo từng trạng thái (Status 1, 2, 3...).
- `check_tags_v2.py`: Kiểm tra tính hợp lệ của các thẻ đặc biệt của game FM trong bản dịch.
- `analyze_errors.py`: Phân tích các lỗi định dạng phổ biến trong nội dung dịch.
- `find_tags_stats.py`: Thống kê tần suất xuất hiện của các thẻ game.
- `analyze_text_length.py`: So sánh độ dài văn bản gốc và bản dịch.

## 🛠 Fixes (Sửa lỗi)
Các công cụ dọn dẹp và chuẩn hóa bản dịch.

- `final_polish.py`: **(Quan trọng)** Tập hợp các logic dọn dẹp tối ưu nhất để chạy cuối cùng.
- `apply_specific_mappings_v4.py`: Áp dụng các quy tắc mapping đại từ và thẻ đặc biệt mới nhất.
- `apply_final_tag_mapping.py`: Sửa lỗi ánh xạ thẻ game FM.
- `repair_and_rescue.py`: Cứu hộ và khôi phục các bản ghi bị lỗi nặng hoặc mất dữ liệu.
- `standardize_database.py`: Chuẩn hóa cấu trúc và dữ liệu trong Database.
- `remove_trailing_garbage.py`: Loại bỏ các ký tự thừa, rác sinh ra bởi AI ở cuối câu.
- `fix_tags.py`: Sửa các lỗi sai định dạng thẻ `[%...]`.
- `revalidate_records.py`: Kiểm tra lại tính hợp lệ của tất cả các bản ghi đã dịch.

## 🔄 Migrations (Đồng bộ)
Các công cụ trích xuất và chuyển đổi dữ liệu.

- `extract_target_ids.py`: Trích xuất danh sách ID cần xử lý ra file text.
- `sync_pronouns_to_main_v2.py`: Đồng bộ hóa các bản sửa lỗi đại từ vào Database chính.
- `extract_pronouns.py`: Trích xuất các câu có chứa đại từ cần lưu ý.
- `extract_you_your.py`: Trích xuất các câu chứa từ "you/your" để dịch chuẩn xác.

---
*Ghi chú: Các script cũ hoặc ít dùng đã được chuyển vào `archive/scripts/` để lưu trữ.*
