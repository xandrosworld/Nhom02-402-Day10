# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Đặng Tùng Anh  
**Vai trò:** Ingestion / Cleaning (Xây dựng bộ quy tắc làm sạch dữ liệu)  
**Ngày nộp:** 15/04/2026

---

## 1. Tôi phụ trách phần nào?

**File / module:**
Tôi chịu trách nhiệm chính việc xây dựng dữ liệu nền tảng cho hệ thống RAG ở module `transform/cleaning_rules.py`. Đặc thù của file này là nhận dữ liệu thô (raw) và trả về 2 tập dữ liệu: `cleaned` (sạch) và `quarantine` (cách ly). Tôi đã đọc hiểu baseline và phát triển thêm 3 rule mới đúng chuẩn yêu cầu "không trivial" và có hướng tới điểm Distinction (không fix cứng ngày tháng):

1. **Rule 1:** Đẩy bản ghi chứa lỗi hệ thống (`lỗi migration`, `bản nháp`) vào khu vực cách ly.
2. **Rule 2:** Dùng Regex cắt bỏ các tiền tố thừa (`FAQ bổ sung: `, `Lưu ý: `) làm nhiễu token của LLM.
3. **Rule 3:** Lọc policy lạc hậu bằng cách lấy cấu hình `HR_CUTOFF_DATE` từ môi trường (env) thay vì hard-code.

**Kết nối với thành viên khác:**
Quá trình làm việc của tôi gắn kết trực tiếp với Mai Tấn Thành (người ghép nối pipeline `etl_pipeline.py`) và Hồ Nhất Khoa (bạn nhận dữ liệu từ output module của tôi để cấu hình `quality/expectations.py`).

**Bằng chứng:**
Tôi đã làm việc trên branch `feat/cleaning-tunganh` và commit trọn vẹn sự thay đổi trong file `transform/cleaning_rules.py`. Các comments `metric_impact` được tôi ghi chép đầy đủ phía trên mỗi rule đúng chuẩn yêu cầu.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật cốt lõi lớn nhất của tôi là **phá bỏ việc hard-code thời gian (Hard-coded Cutoff Date)** trong baseline cũ và thay bằng **Biến môi trường (Environment Variable)**.

Baseline đang chặn cứng các policy của HR có ngày hiệu lực trước `2026-01-01`. Ở môi trường thực tế, năm tài chính luôn thay đổi qua từng chu kỳ. Tôi đã quyết định tích hợp thêm module `os.environ.get("HR_CUTOFF_DATE", "2026-01-01")`. Việc này đảm bảo Data Pipeline của nhóm tôi sở hữu **Dynamic Window**. Bất cứ khi nào phòng HR đưa ra niên hạn policy mới, Mai Tấn Thành (pipeline owner) chỉ việc đổi file `.env`, module của tôi sẽ lập tức thích ứng và tự động thay đổi kết quả `quarantine` mà không cần phải chạm vào sửa code python nữa. Quyết định này giúp quy trình linh hoạt và đáp ứng đúng tiêu chí điểm Distinction trong SCORING.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Trong quá trình soi nội dung file raw `data/raw/policy_export_dirty.csv`, tôi phát hiện một anomaly:

- **Triệu chứng:** Dòng `policy_refund_v4` có chứa một đoạn thông tin nội bộ cực kỳ độc hại: `(ghi chú: bản sync cũ policy-v3 — lỗi migration)`. Phía sau pipeline, LLM sẽ đọc nhầm các đoạn ghi chú rác này của kỹ sư hệ thống cũ, gây hiện tượng hallucination (ảo giác) cho bot RAG.
- **Cách phát hiện:** Xem bằng mắt thường ở bản xuất CSV raw và test log pipeline lần đầu tiên.
- **Xử lý:** Tôi bổ sung Rule 1, quét chuỗi `lỗi migration` hoặc `bản nháp`. Ngay lập tức dòng policy lỗi này bị chặn đứng, đánh cờ lý do `contains_system_error_note` và bị tước quyền đi tiếp vào VectorDB.

---

## 4. Bằng chứng trước / sau

Bằng chứng hiệu quả làm sạch được thể hiện rõ rệt qua artifact final:

- **Run sạch:** `run_id=2026-04-15T10-16Z` có `cleaned_records=5`, `quarantine_records=5`.
- **Run inject:** `run_id=inject-bad` vẫn giữ `cleaned_records=5`, `quarantine_records=5`.

Trong cả hai file `artifacts/quarantine/quarantine_2026-04-15T10-16Z.csv` và `artifacts/quarantine/quarantine_inject-bad.csv`, dòng policy có ghi chú migration đã bị cách ly với lý do:

`contains_system_error_note`

Ví dụ dòng thật trong CSV:

`3,policy_refund_v4,"Yêu cầu hoàn tiền được chấp nhận ... (ghi chú: bản sync cũ policy-v3 — lỗi migration).",...,contains_system_error_note`

Kết quả này xác nhận rule mới của tôi hoạt động ổn định ở cả kịch bản clean và inject.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ nâng cấp Rule 2 (gọt rác tiền tố). Thay vì dùng Regex đơn thuần, tôi sẽ biến nó thành một lớp bộ lọc tự động bằng NLP (spaCy hoặc LLM nhỏ) để phát hiện và gọt bỏ mọi dạng câu rào đón vô nghĩa ("Xin lưu ý", "Chú ý rằng"), giúp tiết kiệm thêm 5-10% không gian token vô ích bị lãng phí trong mạng chroma_db.
