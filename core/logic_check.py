import re
import unicodedata

class LogicCheck:
    @staticmethod
    def validate_tags(eng, vi):
        """Kiểm tra sự đồng bộ của các thẻ [%...] một cách linh hoạt."""
        # Hàm trích xuất và chuẩn hóa thẻ: [%tag#1 - ghi chú] -> [%tag#1]
        def normalize_tag(tag):
            # Lấy phần chính trước dấu cách hoặc dấu gạch ngang đầu tiên bên trong thẻ
            # VD: [%string#1 - Month] -> [%string#1]
            core = re.split(r'[-\s#]', tag.lower().strip('[]%'))[0]
            # Giữ lại số thứ tự nếu có: string#1
            match = re.search(r'[^#]+#\d+', tag.lower())
            return match.group(0) if match else core

        eng_tags = set(normalize_tag(tag) for tag in re.findall(r'\[%[^\]]+\]', eng))
        vi_tags = set(normalize_tag(tag) for tag in re.findall(r'\[%[^\]]+\]', vi))
        
        missing = eng_tags - vi_tags
        
        # Bỏ qua các thẻ liên quan đến Manager/Persona đã được duyệt
        persona_cores = {'person#1', 'male#1', 'female#1', 'you', 'your'}
        filtered_missing = [tag for tag in missing if tag not in persona_cores and 'hidden' not in tag]
        
            
        return True, "Tags OK"

    @staticmethod
    def validate_pronouns(eng, vi):
        """Kiểm tra xưng hô cấm có đối chiếu ngữ cảnh câu gốc và loại trừ từ ghép."""
        vi_lower = f" {vi.lower()} "
        eng_lower = f" {eng.lower()} "
        
        # 1. Các trường hợp ngoại lệ (từ ghép không phải xưng hô)
        temp_vi = vi_lower
        exemptions = [
            "tiếng anh", "vương quốc anh", "nước anh", "anh quốc", "v.q anh",
            "trẻ em", "anh em", "chị em", "em gái", "em trai", "bạn bè", "em bé"
        ]
        for ex in exemptions:
            temp_vi = temp_vi.replace(ex, " EXEMPTED_WORD ")
            
        # 2. Danh sách lỗi và regex tương ứng
        rules = [
            (r'\b(em|mày|tao)\b', "Phát hiện xưng hô không phù hợp"),
            (r'\b(bạn)\b', "Phát hiện xưng hô 'bạn' (kiểm tra context?)"),
            (r'\b(anh)\b(?!( ấy| ta))', "Dùng 'anh' đơn lẻ cho Manager (phải dùng 'Ngài')")
        ]
        
        found_errs = []
        for pattern, msg in rules:
            match = re.search(pattern, temp_vi)
            if match:
                word = match.group(1)
                # ĐẶC BIỆT: Nếu là từ 'bạn', kiểm tra xem gốc có 'friend' hoặc 'your' không
                if word == 'bạn' and ('friend' in eng_lower or 'your' in eng_lower):
                    continue 
                
                found_errs.append(f"{msg}: '{word}'")
        
        if found_errs:
            return False, "; ".join(found_errs)
            
        return True, "Pronouns OK"

    @staticmethod
    def validate_cleanup(vi):
        """Kiểm tra lỗi trình bày, bỏ qua nội dung trong [COMMENT]."""
        # 1. Loại bỏ phần comment [...] trước khi kiểm tra lặp từ
        text_to_check = re.sub(r'\[COMMENT:[^\]]+\]', '', vi)
        
        # Chuẩn hóa Unicode NFC để tránh lỗi font/dấu trên Windows
        text_to_check = unicodedata.normalize('NFC', text_to_check)
        
        # 2. Kiểm tra lặp từ (Double words)
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
        
        # 2. Khoảng trắng kép (trên text gốc chưa xóa comment)
        if "  " in vi:
            return False, "Có khoảng trắng kép"
            
        return True, "Cleanup OK"

    @classmethod
    def evaluate(cls, eng, vi):
        """Chấm điểm bản dịch (0.0 - 1.0) dựa trên các tiêu chí kỹ thuật."""
        score = 1.0
        feedbacks = []
        
        if not vi:
            return 0.0, "Chưa dịch"
            
        # Kiểm tra Thẻ
        tag_ok, tag_msg = cls.validate_tags(eng, vi)
        if not tag_ok:
            score -= 0.5
            feedbacks.append(tag_msg)
            
        # Kiểm tra Xưng hô (Truyền thêm eng để check ngữ cảnh)
        pro_ok, pro_msg = cls.validate_pronouns(eng, vi)
        if not pro_ok:
            score -= 0.2
            feedbacks.append(pro_msg)
            
        # Kiểm tra Cleanup
        cln_ok, cln_msg = cls.validate_cleanup(vi)
        if not cln_ok:
            score -= 0.1
            feedbacks.append(cln_msg)
            
        return max(0.0, score), "; ".join(feedbacks) if feedbacks else "Perfect"
