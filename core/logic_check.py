import re
import unicodedata

class LogicCheck:
    @staticmethod
    def validate_tags(eng, vi):
        """Kiểm tra sự đồng bộ của các thẻ [%...] một cách linh hoạt, kiểm tra thứ tự và tự động điền thẻ thiếu."""
        def normalize_tag(tag):
            # Loại bỏ ngoặc và ký hiệu % ở cả hai đầu trước khi xử lý
            cleaned = tag.lower().strip('[]%')
            # Lấy phần chính trước dấu cách hoặc dấu gạch ngang
            core = re.split(r'[-\s#]', cleaned)[0]
            # Giữ lại số thứ tự nếu có: male#2
            match = re.search(r'[^#]+#\d+', cleaned)
            return match.group(0) if match else core

        # Trích xuất danh sách thẻ (theo thứ tự)
        eng_tags_raw = re.findall(r'\[%[^\]]+\]', eng)
        vi_tags_raw = re.findall(r'\[%[^\]]+\]', vi)
        
        persona_prefix = {'person', 'male', 'female', 'you', 'your', 'eprson', 'poerson', 'perso', 'erson', 'fm_pedia'}
        
        # Chỉ lấy Data Tags (Bỏ qua Persona tags có thể đã dịch)
        def filter_data_tags(tags_raw):
            data_tags = []
            for t in tags_raw:
                if 'hidden' in t: continue
                norm = normalize_tag(t)
                core = norm.split('#')[0]
                if core in persona_prefix: continue
                data_tags.append((t, norm))
            return data_tags
            
        eng_data = filter_data_tags(eng_tags_raw)
        vi_data = filter_data_tags(vi_tags_raw)
        
        # 1. Tự động nội suy vị trí và điền thẻ thiếu
        fixed_vi = vi
        vi_norms = [norm for _, norm in vi_data]
        missing_count = 0
        error_msgs = []
        
        for i, (tag_raw, norm) in enumerate(eng_data):
            if norm not in vi_norms:
                missing_count += 1
                # Auto-fix: Tìm vị trí chèn tối ưu dựa trên hàng xóm gần nhất (trước hoặc sau)
                inserted = False
                
                # Thử tìm hàng xóm phía trước (Phải tìm từ i-1 ngược về 0)
                for prev_idx in range(i - 1, -1, -1):
                    prev_tag_raw, _ = eng_data[prev_idx]
                    pos = fixed_vi.find(prev_tag_raw)
                    if pos != -1:
                        insert_pos = pos + len(prev_tag_raw)
                        fixed_vi = fixed_vi[:insert_pos] + f" {tag_raw}" + fixed_vi[insert_pos:]
                        inserted = True
                        break
                
                # Nếu không tìm thấy hàng xóm phía trước, thử tìm hàng xóm phía sau (Phải tìm từ i+1 đến hết)
                if not inserted:
                    for next_idx in range(i + 1, len(eng_data)):
                        next_tag_raw, _ = eng_data[next_idx]
                        pos = fixed_vi.find(next_tag_raw)
                        if pos != -1:
                            # Chèn vào trước thẻ hàng xóm
                            fixed_vi = fixed_vi[:pos] + f"{tag_raw} " + fixed_vi[pos:]
                            inserted = True
                            break
                
                # Cuối cùng nếu đơn độc, chèn vào cuối câu
                if not inserted:
                    fixed_vi = fixed_vi.strip() + f" {tag_raw}"
                
                # Cập nhật vi_norms để tránh chèn lặp trong vòng lặp này (mặc dù eng_data thường unique)
                vi_norms.append(norm)
        
        if missing_count > 0:
            error_msgs.append(f"Tự động bổ sung {missing_count} thẻ bị thiếu")
            
        # 2. Kiểm tra thứ tự thẻ Data sau khi đã fix
        # Lấy lại danh sách tag từ fixed_vi để kiểm tra thứ tự
        fixed_vi_tags_raw = re.findall(r'\[%[^\]]+\]', fixed_vi)
        fixed_vi_data = filter_data_tags(fixed_vi_tags_raw)
        fixed_vi_norms = [norm for _, norm in fixed_vi_data]
        
        eng_norms = [norm for _, norm in eng_data]
        
        # So sánh thứ tự các tag chung
        common_eng = [n for n in eng_norms if n in fixed_vi_norms]
        common_vi = [n for n in fixed_vi_norms if n in eng_norms]
        
        if common_eng != common_vi and eng_norms:
            error_msgs.append("Sai thứ tự thẻ dữ liệu")
            
        # 3. Kiểm tra hậu tố đại từ tiếng Anh còn sót trong thẻ [%...-suffix]
        # Theo rules.md: hậu tố đại từ BẮT BUỘC phải Việt hóa
        ENGLISH_PRONOUN_SUFFIXES = {
            '-i]', '-me]', '-my]',
            '-you]', '-your]',
            '-he]', '-him]', '-his]',
            '-she]', '-her]',
            '-they]', '-them]', '-their]',
        }
        for tag in fixed_vi_tags_raw:
            tag_lower = tag.lower()
            for eng_suffix in ENGLISH_PRONOUN_SUFFIXES:
                if tag_lower.endswith(eng_suffix):
                    error_msgs.append(f"Hậu tố đại từ tiếng Anh chưa Việt hóa: {tag}")
                    break
            
        is_ok = len(error_msgs) == 0
        return is_ok, "; ".join(error_msgs) if error_msgs else "Tags OK", fixed_vi

    @staticmethod
    def validate_pronouns(eng, vi):
        """Kiểm tra xưng hô cấm có đối chiếu ngữ cảnh câu gốc và loại trừ từ ghép."""
        vi_lower = f" {vi.lower()} "
        eng_lower = f" {eng.lower()} "
        
        # 1. Các trường hợp ngoại lệ (từ ghép không phải xưng hô)
        temp_vi = vi_lower
        exemptions = [
            "tiếng anh", "vương quốc anh", "nước anh", "anh quốc", "v.q anh",
            "trẻ em", "anh em", "chị em", "em gái", "em trai", "bạn bè", "em bé",
            "mày mò", "đội tuyển anh", "đội tuyển vương quốc anh", "anh-scotland",
            "anh hùng", "anh minh", "anh dũng", "anh tài", "anh hào", "anh tuấn",
            "lông mày", "nhướng mày", "chau mày", "mày râu", "chân mày", "gờ chân mày",
            "bạn đọc", "bạn hữu", "bạn đồng hành", "bạn đời", "đám bạn", "bạn thân", "người bạn", "tình bạn", "những người bạn", "kết bạn", "người bạn",
            "anh/chị/em", "em ruột", "anh ruột", "chị ruột",
            "cầu thủ", "ông chủ", "chú ý", "hắn ta", "nhu cầu", "chiều cao", "cậu bé", "cậu quý tử", "yêu cầu", "y tế", "y thuật", "chú trọng", "chú giải",
        ]
        for ex in exemptions:
            temp_vi = temp_vi.replace(ex, " EXEMPTED_WORD ")
            
        # 2. Danh sách lỗi và regex tương ứng
        rules = [
            (r'\b(em|mày|tao)\b', "Phát hiện xưng hô không phù hợp"),
            (r'\b(bạn)\b', "Phát hiện xưng hô 'bạn' (kiểm tra context?)"),
            (r'\b(anh)\b(?!( ấy| ta))', "Dùng 'anh' đơn lẻ cho Manager (phải dùng 'Ngài')"),
            (r'\b(cậu|hắn|y|chú)\b', "Phát hiện xưng hô lách luật"),
            (r'^Của \[\%', "Lỗi cấu trúc 'Của [Đội bóng]' đứng đầu câu")
        ]
        
        found_errs = []
        for pattern, msg in rules:
            match = re.search(pattern, temp_vi)
            if match:
                word = match.group(1)
                
                # Ngoại lệ cho "anh" khi là tên quốc gia dựa trên context tiếng Anh
                if word == 'anh' and any(c in eng_lower for c in ['england', 'britain', 'uk', 'english', 'british']):
                    continue
                
                # ĐẶC BIỆT: Nếu là từ 'bạn', kiểm tra xem gốc có 'friend' hoặc 'your' không
                if word == 'bạn' and ('friend' in eng_lower or 'your' in eng_lower):
                    continue 
                
                found_errs.append(f"{msg}: '{word}'")
                
        # 3. Kiểm tra viết hoa chữ "Ngài" / "ngài" (Capitalization)
        # Sử dụng chuỗi vi (nguyên bản, có phân biệt hoa/thường)
        matches = re.finditer(r'\b([Nn]gài)\b', vi)
        for match in matches:
            word = match.group(1)
            start_idx = match.start()
            
            is_start = False
            prefix = vi[:start_idx].strip()
            
            if not prefix:
                is_start = True
            elif prefix[-1] in ['.', '!', '?'] or prefix.endswith('...'):
                is_start = True
            elif prefix[-1] in ['"', "'", '[', '{', '('] and len(prefix) >= 2 and prefix[-2] in ['.', '!', '?']:
                is_start = True
                
            if is_start and word == 'ngài':
                found_errs.append("Chữ 'ngài' đứng đầu hoặc sau ngắt câu phải viết hoa (Ngài)")
            elif not is_start and word == 'Ngài':
                found_errs.append("Chữ 'Ngài' giữa câu phải viết thường (ngài)")
        
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
            return 0.0, "Chưa dịch", vi
            
        # Kiểm tra Thẻ
        tag_ok, tag_msg, fixed_vi = cls.validate_tags(eng, vi)
        if not tag_ok:
            score -= 0.5
            feedbacks.append(tag_msg)
            
        # Kiểm tra Xưng hô (Truyền thêm eng để check ngữ cảnh)
        pro_ok, pro_msg = cls.validate_pronouns(eng, fixed_vi)
        if not pro_ok:
            score -= 0.2
            feedbacks.append(pro_msg)
            
        # Kiểm tra Cleanup
        cln_ok, cln_msg = cls.validate_cleanup(fixed_vi)
        if not cln_ok:
            score -= 0.1
            feedbacks.append(cln_msg)
            
        return max(0.0, score), "; ".join(feedbacks) if feedbacks else "Perfect", fixed_vi
