# Handoff Checklist for @dev-agent (2026-04-13)

- **Người yêu cầu:** Tech Lead (Antigravity)
- **Mục tiêu:** Hoàn tất 23,666 bản ghi còn lại trong database bằng Free Tier.
- **Ràng buộc:** 
  - Tuân thủ nghiêm ngặt `data/rules.md`.
  - Persona xưng hô "Ngài" cho Manager.
  - Bảo toàn tuyệt đối các thẻ game (Tags).
  - Không dịch tên riêng, địa danh viết hoa.

## Checklist thực hiện:

1. [ ] **Kích hoạt Agent Dịch thuật (Free Tier):**
   ```powershell
   python 2_run_agents.py --model free_tier
   ```
   *Lưu ý: Script này chạy 5 agents gối đầu, dự kiến hoàn thành sau khoảng 3-4 tiếng tùy vào giới hạn API.*

2. [ ] **Chấm điểm chất lượng (The Lean Judge):**
   ```powershell
   python runners/run_reviewer.py
   ```
   *Mục đích: Đảm bảo các câu mới dịch không bị lỗi thẻ hoặc xưng hô.*

3. [ ] **Xuất bản release (Tùy chọn):**
   ```powershell
   python core/3_export_to_ltf.py
   ```

4. [ ] **Kiểm tra tiến độ cuối cùng:**
   ```powershell
   python scripts/diagnostics/check_progress.py
   ```

## Files liên quan:
- Database: [database.sqlite](file:///d:/Me/Workspaces/FM26/data/database.sqlite)
- Rules: [rules.md](file:///d:/Me/Workspaces/FM26/data/rules.md)
- Runner: [run_free_tier.py](file:///d:/Me/Workspaces/FM26/runners/run_free_tier.py)

---
*Kế hoạch được lập bởi @tech-lead. Người dùng sẽ trực tiếp kích hoạt @dev-agent.*
