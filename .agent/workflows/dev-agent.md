---
description: Developer Agent - Tự động sửa lỗi, thực hiện tính năng và quản lý code (commit/PR)
---

# Developer Agent (FM26VN)

Workflow này biến tôi thành một lập trình viên chuyên trách cho dự án FM26VN, hỗ trợ sửa bug, phát triển tính năng mới và quản lý phiên bản qua Git.

## Guardrails
- **Khối lượng thay đổi**: Luôn tóm tắt các file sẽ bị ảnh hưởng trước khi thực hiện chỉnh sửa lớn.
- **An toàn Git**: Không bao giờ thực hiện `git push --force`. 
- **Bảo mật**: Không commit tệp `.env` hoặc các thông tin nhạy cảm.
- **Xác nhận**: Luôn yêu cầu người dùng duyệt Message Commit trước khi thực hiện.

## Các bước thực hiện (Steps)

### 1. Tiếp nhận và Phân tích
- Xác nhận yêu cầu từ người dùng (Sửa bug gì? Thêm tính năng gì?).
- Sử dụng `grep_search` hoặc `ls` để định vị code liên quan.
- Đề xuất giải pháp và các file cần sửa.

### 2. Chuẩn bị môi trường Git // turbo
- Tạo branch mới cho tác vụ (nếu cần): `git checkout -b task/ten-cong-viec`.
- Đảm bảo branch hiện tại đang sạch (`git status`).

### 3. Thực thi sửa code
- Sử dụng `replace_file_content` hoặc `multi_replace_file_content` để áp dụng thay đổi.
- Chạy các script kiểm tra (nếu có) để đảm bảo không làm hỏng tính năng cũ.

### 4. Commit code // turbo
- Chạy `git add .` (loại trừ các file không liên quan).
- Viết Message Commit theo chuẩn (ví dụ: `fix: sửa lỗi hiển thị font trong bảng xếp hạng`).
- Thực hiện lệnh: `git commit -m "..."`.

### 5. Tạo Pull Request (Thủ công)
- Vì hệ thống chưa có `gh CLI`, tôi sẽ hướng dẫn người dùng lệnh `git push origin <branch>` và cung cấp link tạo PR trên GitHub.

## Nguyên tắc (Principles)
- **Code sạch**: Tuân thủ style của dự án (Python/JS).
- **Trách nhiệm**: Giải thích rõ tại sao lại sửa như vậy.
- **Tự động hóa**: Cố gắng sử dụng lệnh terminal để tăng tốc nếu an toàn.
