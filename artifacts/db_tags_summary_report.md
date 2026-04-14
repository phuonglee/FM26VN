# Phân Loại & Phương Án Xử Lý Thẻ (Tags) Trong Database FM26

Báo cáo này liệt kê danh sách các nhóm thẻ (`[%...]` và `{...}`) thực tế được trích xuất từ cột `english_text` trong cơ sở dữ liệu (`records` table), và đối chiếu với các quy tắc xử lý hiện tại (`rules.md`).

---

## 1. Nhóm Thẻ Xưng Hô & Đại Từ (Pronoun & Modifier Tags)
*Tần suất xuất hiện: Cực kỳ cao (hàng chục nghìn lượt)*

Đây là nhóm thẻ dùng để xưng hô, có đặc điểm nhận dạng là **phần hậu tố sau dấu gạch ngang (`-`)**.
- **Danh sách tiêu biểu:** 
  - `[%male#-I]`, `[%female#-I]`, `[%person#-I]`
  - `[%male#-you]`, `[%female#-you]`, `[%person#-you]`, `[%male#-You]`
  - `[%male#-your]`, `[%female#-your]`, `[%person#-your]`
  - `[%male#-he]`, `[%female#-she]`, `[%person#-he]`, `[%person#-He]`
  - `[%male#-him]`, `[%female#-her]`, `[%person#-him]`
  - `[%male#-his]`, `[%female#-her]`, `[%person#-his]`
  - `[%male#-me]`, `[%female#-me]`, `[%male#-my]`, `[%female#-my]`
  - `[%male#-himself]`, `[%female#-herself]`, `[%person#-himself]`

👉 **Phương Án Xử Lý (Status: Đã có quy định):**
- **Quy tắc thay thế:** Toàn bộ thẻ có hậu tố đại từ này phải được thay thế 100% bằng **văn bản tiếng Việt tương ứng**.
- **Đại từ cụ thể:**
  - Manager / You / Your: Bắt buộc dùng **"Ngài" / "của Ngài" / "chính Ngài"**.
  - I / me / my: **"Tôi" / "của tôi" / "chính tôi"**.
  - He / him / his: **"Anh ấy" (Anh ta) / "của anh ấy" / "chính anh ấy"**.
  - She / her / hers: **"Cô ấy" (Cô ta) / "của cô ấy" / "chính cô ấy"**.

---

## 2. Nhóm Thẻ Gọi Tên / Thực Thể (Data Entity Tags)
*Tần suất xuất hiện: Cao*

Đây là nhóm thẻ chứa dữ liệu động của game, **không có hậu tố phía sau** (hoặc chỉ đứng một mình như `[%male#1]`).
- **Danh sách tiêu biểu:** 
  - `[%team#]`, `[%club#]`, `[%nation#]`, `[%nationality#]`, `[%continent#]`
  - `[%person#]`, `[%male#]`, `[%female#]`
  - `[%number#]`, `[%cash#]`, `[%date#]`, `[%time#]`
  - `[%job#]`, `[%position#]`, `[%tactical_role#]`
  - `[%comp#]`, `[%stadium#]`, `[%injury#]`, `[%media_source#]`
  - `[%fixture_name#]`, `[%stage_name#]`

👉 **Phương Án Xử Lý (Status: Đã có quy định):**
- **BẮT BUỘC:** Giữ nguyên 100% format thẻ và đặt ở vị trí phù hợp trong câu. KHÔNG ĐƯỢC xóa đổi thành văn bản cứng.
- Nếu các thẻ chỉ định người (`[%male#1]`, `[%person#1]`) đứng **độc lập không có hậu tố**, bắt buộc phải được giữ lại để game gọi đúng tên nhân vật/người chơi.

---

## 3. Nhóm Thẻ Định Dạng Kỹ Thuật (Technical Modifiers)
*Tần suất xuất hiện: Cao*

Các thẻ có hậu tố kỹ thuật dùng để quyết định định dạng của từ vựng (viết hoa/thường, dạng số nhiều, gọi tên họ...).
- **Danh sách tiêu biểu:** 
  - Hiển thị tên: `-short`, `-surname`, `-first`, `-nickname`, `-six_letter`, `-nickname_no_the_english_only`
  - Ẩn đối tượng (Logic game): `-hidden`
  - Kiểu chữ: `-lowercase`, `-text`
  - Kiểu số liệu/Thời gian: `-nth`, `-typeonly`, `-roundlarge`, `-long-roundlarge`, `-month`, `-day`, `-long_no_day`, `-month_and_year`

👉 **Phương Án Xử Lý (Status: Đã có quy định nghiêm ngặt):**
- **Tuyệt đối KHÔNG DỊCH các hậu tố này**. (Ví dụ: KHÔNG ĐƯỢC phép dịch `[%team#1-short]` thành `[%team#1-ngắn]`).
- Các thẻ này phải được **giữ nguyên y hệt bản gốc tiếng Anh** và đặt ở vị trí ngữ nghĩa tương ứng trong bản dịch tiếng Việt. 

---

## 4. Nhóm Thẻ Ngoặc Nhọn (Curly Tags)
*Tần suất xuất hiện: Từ thấp đến cao*

Thay đổi mạo từ, hình thức hay sở hữu cách theo ngữ pháp.
- **Danh sách tiêu biểu:**
  - Sở hữu cách: `{s}` (xuất hiện hơn 44,000 lần)
  - Mạo từ: `{an}`, `{a}`, `{An}`, `{A}`
  - Viết hoa/Thường: `{upper}`, `{lower}`
  - Modifiers khác: `{scoreline}`, `{ordinal}`, `{the}`

👉 **Phương Án Xử Lý (Status: Đã có quy định):**
- `{s}`: Biến đổi thành dạng cấu trúc tiếng Việt, phổ biến nhất là thêm chữ **"của"** đằng trước thẻ được sở hữu. (VD: `[%team#1]{s} stadium` -> `sân vận động của [%team#1]`).
- `{a}`/`{an}`: Dịch thành **`{một}`** hoặc **`{Một}`**, hoặc lược bỏ hoàn toàn tùy vào ngữ cảnh để câu tiếng Việt mượt mà.
- `{upper}`/`{lower}`: Giữ nguyên hoàn toàn.

---

## 5. Các Thẻ Đặc Biệt (Danh Sách / Cấu trúc đặc thù)
*Tần suất xuất hiện: Trung bình*

- **Danh sách tiêu biểu:** 
  - `[%team_list#]`, `[%person_list#]`: Liệt kê danh sách (VD: "Man Utd, Arsenal và Chelsea").
  - `[%team_description#]`, `[%player_description#]`: Cụm mô tả dài.
  - `[%male#author-I]`, `[%person#author-I]`: Gọi tác giả phát ngôn.
  - Các biến thể Social Media: `#[%...]`, `#[%...-hashtag]`, `[%...]In`, `[%...]Out`

👉 **Phương Án Xử Lý (Status: Đã có quy định một phần):**
- Thẻ Hashtag / Định dạng Social media: **Giữ nguyên 100%, dính liền với dấu `#`**, không được cắt hoặc thêm khoảng trắng để tránh lỗi UI mạng xã hội trong game.
- Các thẻ `list`, `description`, `author-I`: Giữ nguyên vị trí trong cấu trúc ngữ pháp như cụm danh từ thông thường. `author-I` thì phần hậu tố `-I` dịch thành "tôi" y hệt như các đại từ khác.
