# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Mai Tấn Thành  
**Vai trò:** Ingestion / Embed / Integration — Pipeline & Provider Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `etl_pipeline.py`
- `providers.py`
- `.env.example`
- `requirements.txt`
- phần tích hợp trong `eval_retrieval.py` và `grading_run.py`

Trong bài Day 10, tôi giữ phần khung chạy chung của nhóm: tách repo riêng cho lab, cấu hình provider, và đảm bảo pipeline chạy end-to-end với stack mở rộng của nhóm. Cụ thể, tôi cấu hình **Voyage** cho embedding và **Claudible** cho phần LLM judge mở rộng. Mục tiêu của tôi không phải viết cleaning rule hay expectation chi tiết, mà là làm cho raw CSV, cleaned/quarantine artifact, expectation suite và bước publish vào Chroma nối với nhau ổn định. Khi các bạn khác sửa `cleaning_rules.py`, `expectations.py` hay `freshness_check.py`, tôi là người merge lại rồi chạy test toàn bộ.

**Kết nối với thành viên khác:**

Tùng Anh phụ trách cleaning rule, Nhất Khoa phụ trách expectation và monitoring, còn tôi giữ phần pipeline + provider để cả nhóm có cùng môi trường chạy.

**Bằng chứng (commit / comment trong code):**

Các thay đổi chính nằm ở `providers.py`, `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py`; các lần chạy kiểm chứng gần nhất dùng `run_id` `2026-04-15T10-16Z` và `inject-bad`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định quan trọng nhất của tôi là không nhúng trực tiếp logic gọi API vào từng script, mà tách ra thành một lớp provider riêng trong `providers.py`. Lý do là Day 10 vẫn là bài data pipeline, nên entrypoint như `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py` nên tập trung vào luồng xử lý dữ liệu thay vì chi tiết SDK. Khi gom phần embedding và LLM judge vào một chỗ, tôi có thể đổi stack từ local sang Voyage/Claudible mà không phải sửa lan sang nhiều file.

Tôi cũng chủ động dùng collection riêng `day10_kb` thay vì dùng lại index cũ từ Day 08/09. Việc này quan trọng vì Day 10 chấm ở ranh giới clean → validate → publish. Nếu dùng lại Chroma cũ, nhóm sẽ không chứng minh được dữ liệu sau clean thực sự ảnh hưởng đến retrieval như thế nào.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Anomaly đáng chú ý ở vòng final là: tôi kỳ vọng kịch bản `inject-bad` sẽ làm retrieval giảm chất lượng, nhưng kết quả thực tế vẫn ổn định (không tăng `hits_forbidden`). Ban đầu điều này dễ bị hiểu nhầm là lệnh inject không hoạt động. Khi đối chiếu `cleaned_inject-bad.csv`, `quarantine_inject-bad.csv` và expectation log, tôi xác nhận pipeline vẫn chạy đúng; khác biệt nằm ở chỗ rule mới đã quarantine sớm dòng stale refund có ghi chú migration (`contains_system_error_note`) trước khi vào embed. Vì vậy, dù bật `--no-refund-fix`, chunk sai vẫn không đi vào Chroma. Đây là tín hiệu tốt cho kiến trúc hiện tại: phòng thủ dữ liệu được đẩy lên sớm ở lớp cleaning/quarantine thay vì chờ tới lớp retrieval mới phát hiện.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Tôi dùng hai lần chạy thật:

- run sạch: `2026-04-15T10-16Z`
- run inject: `inject-bad`

Trong `artifacts/eval/before_after_eval.csv`, câu `q_refund_window` có:

`contains_expected=yes, hits_forbidden=no`

Sau inject và eval lại ở `artifacts/eval/after_inject_bad.csv`, kết quả vẫn là:

`contains_expected=yes, hits_forbidden=no`

Với toàn bộ 4 câu hỏi, cả hai file eval đều cho `4/4 contains_expected=yes` và `0/4 hits_forbidden=yes`. Kết quả này phản ánh đúng trạng thái pipeline final: dữ liệu stale đã bị chặn tại bước clean/quarantine trước khi embed.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ chuyển phần logging sang JSON lines và đọc SLA trực tiếp từ `contracts/data_contract.yaml` thay vì chỉ lấy từ env. Cách này sẽ làm contract, runbook và monitoring khớp nhau hơn, đồng thời dễ chứng minh hơn phần observability và versioning khi viết báo cáo nhóm.
