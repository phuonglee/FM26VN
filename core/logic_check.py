import re

class LogicCheck:
    @staticmethod
    def extract_tags(text, pattern):
        """Trích xuất tất cả các thẻ khớp với pattern."""
        return re.findall(pattern, text)

    @staticmethod
    def validate_tags(eng, vi):
        """Kiểm tra tính toàn vẹn của thẻ, phân biệt thẻ Dữ liệu và thẻ Đại từ."""
        eng_square = set(re.findall(r'(\[%[^\]]+\])', eng))
        vi_square = set(re.findall(r'(\[%[^\]]+\])', vi))
        
        # Danh sách các hậu tố đại từ linh hoạt (có thể biến thành chữ)
        flexible_suffixes = ["-i", "-me", "-my", "-you", "-your", "-he", "-him", "-his", "-she", "-her"]
        
        def is_flexible(tag):
            tag_lower = tag.lower()
            return any(suffix in tag_lower for suffix in flexible_suffixes)

        critical_missing = []
        for tag in eng_square:
            # Nếu là thẻ linh hoạt, bỏ qua nếu không tìm thấy trong vi_square
            if is_flexible(tag):
                continue
            
            # Nếu là thẻ dữ liệu (không linh hoạt), phải kiểm tra ID
            tag_id = tag.split('-')[0].split('#')[0] + "]"
            vi_ids = {t.split('-')[0].split('#')[0] + "]" for t in vi_square}
            
            if tag_id not in vi_ids:
                critical_missing.append(tag)

        if critical_missing:
            return False, f"Thiếu thẻ dữ liệu bắt buộc: {critical_missing}"

        # 2. Kiểm tra thẻ Curly {...}
        eng_curly = set(re.findall(r'(\{[^\}]+\})', eng))
        vi_curly = set(re.findall(r'(\{[^\}]+\})', vi))
        
        critical_curly = {"{scoreline}", "{number}", "{ordinal}", "{date}"}
        missing_critical = (eng_curly & critical_curly) - vi_curly
        if missing_critical:
            return False, f"Thiếu thẻ định dạng quan trọng: {missing_critical}"

        return True, "Tags OK"

    @staticmethod
    def validate_pronouns(vi):
        """Kiểm tra xưng hô cấm bằng Regex (tránh bắt nhầm 'anh ấy', 'anh ta')."""
        vi_lower = f" {vi.lower()} "
        
        # Danh sách lỗi và regex tương ứng
        # \b có nghĩa là ranh giới từ (word boundary)
        # (?! ấy| ta) là negative lookahead: không được theo sau bởi ' ấy' hoặc ' ta'
        rules = [
            (r'\b(bạn|em|mày|tao)\b', "Phát hiện xưng hô không phù hợp"),
            (r'\b(anh)\b(?!( ấy| ta))', "Dùng 'anh' đơn lẻ cho Manager (phải dùng 'Ngài')")
        ]
        
        found_errs = []
        for pattern, msg in rules:
            match = re.search(pattern, vi_lower)
            if match:
                found_errs.append(f"{msg}: '{match.group(1)}'")
        
        if found_errs:
            return False, "; ".join(found_errs)
        return True, "Pronouns OK"

        """Kiểm tra lỗi trình bày, bỏ qua nội dung trong [COMMENT]."""
        # 1. Loại bỏ phần comment [...] trước khi kiểm tra lặp từ
        text_to_check = re.sub(r'\[COMMENT:[^\]]+\]', '', vi)
        
        import unicodedata
        text_to_check = unicodedata.normalize('NFC', text_to_check)
        
        # 2. Kiểm tra lặp từ (Double words)
        # Danh sách từ láy Tiếng Việt (Dùng mã Unicode để tránh lỗi encoding trên Windows)
        whitelist_raw = (
            "bla,buồn,băng,ca,chiến,chung,chất,chằm,chỉ,cách,có,của,cười,cạnh,cấp,cần,cầu,draft,dần,gian,giá,giải,goal,golazo,gần,hay,hiện,hướng,hạng,khi,không,khăng,khả,kể,kỳ,luôn,làm,lâng,lương,lại,mãi,một,mới,ngày,người,nhiều,nhất,nào,nói,năm,quen,quá,rất,sai,sau,song,số,thành,thể,thủ,tin,toán,trước,trừ,tuyển,tích,tại,tất,tập,từ,vi,vui,vân,vòng,vù,xa,xem,xinh,ít,đang,đi,đó,đùng,đưa,được,đầu,đến,để,định,đối,đồng,đội,ừm"
        )
        whitelist = set(whitelist_raw.split(','))
        
        # Sử dụng regex linh hoạt hơn cho Unicode
        matches = re.finditer(r'(?<!\w)(\w+)\s+\1(?!\w)', text_to_check, re.IGNORECASE | re.UNICODE)
        for m in matches:
            word = m.group(1).lower()
            if word not in whitelist:
                return False, f"Phát hiện lặp từ (Double words): '{word} {word}'"
        
        # 2. Khoảng trắng kép
        if "  " in vi:
            return False, "Có khoảng trắng kép"
            
        return True, "Cleanup OK"

    @classmethod
    def evaluate(cls, eng, vi):
        """Tổng hợp điểm số dựa trên logic."""
        score = 1.0
        feedbacks = []
        
        # Kiểm tra Tags (Trọng số lớn nhất)
        tag_ok, tag_msg = cls.validate_tags(eng, vi)
        if not tag_ok:
            score -= 0.5
            feedbacks.append(tag_msg)
            
        # Kiểm tra Xưng hô
        pro_ok, pro_msg = cls.validate_pronouns(vi)
        if not pro_ok:
            score -= 0.2
            feedbacks.append(pro_msg)
            
        # Kiểm tra Cleanup
        cln_ok, cln_msg = cls.validate_cleanup(vi)
        if not cln_ok:
            score -= 0.1
            feedbacks.append(cln_msg)
            
        return round(max(0.0, score), 2), "; ".join(feedbacks) if feedbacks else "Perfect"

if __name__ == "__main__":
    # Test nhanh
    eng_test = "Manager [%person#1-I] will go to the [%stadium#1]."
    vi_test = "HLV [%person#1-Ngài] sẽ đi đến [%stadium#1]."
    print(f"Test 1 (Good): {LogicCheck.evaluate(eng_test, vi_test)}")
    
    vi_bad = "Bạn [%person#1] sẽ đến sân."
    print(f"Test 2 (Bad): {LogicCheck.evaluate(eng_test, vi_bad)}")
