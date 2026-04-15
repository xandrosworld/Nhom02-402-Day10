# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Đức Hoàng Phúc  
**Vai trò:** Embed / Evaluation / Grading — Retrieval Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

File / module:

- eval_retrieval.py
- grading_run.py
- docs/quality_report.md

Tôi chịu trách nhiệm đánh giá retrieval sau pipeline ETL, kiểm tra hit_correct và hits_forbidden, đồng thời xây dựng grading JSONL.

Kết nối:

- Nhận dữ liệu từ ETL pipeline
- Dựa vào expectation suite
- Output dùng cho report

Bằng chứng:

=== EVAL SUMMARY ===

{'total': 4, 'hit_correct_rate': 1.0, 'hits_forbidden_rate': 0.0}

=== GRADING SUMMARY ===

{'total': 3, 'pass_rate': 1.0}

---

## 2. Một quyết định kỹ thuật

Tôi sử dụng hai metric: hit_correct và hits_forbidden thay vì chỉ accuracy. Điều này giúp phát hiện trường hợp context chứa dữ liệu sai dù answer đúng. Đây là yếu tố quan trọng trong RAG system.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly tôi gặp ở vòng final là kết quả inject không còn làm tăng `hits_forbidden` như kỳ vọng ban đầu của kịch bản demo. Tôi đối chiếu `after_inject_bad.csv` với `before_after_eval.csv` và thấy cả hai file đều cho kết quả sạch (`hits_forbidden=no` cho 4/4 câu). Sau khi kiểm tra thêm `quarantine_inject-bad.csv`, tôi xác nhận nguyên nhân là dòng stale refund đã bị chặn từ bước clean do `reason=contains_system_error_note`, nên không đi vào Chroma kể cả khi chạy `--no-refund-fix --skip-validate`.

Tôi cập nhật lại phần diễn giải trong `docs/quality_report.md` theo đúng hiện trạng: lớp bảo vệ đã chuyển lên cleaning/quarantine, vì vậy before/after retrieval ổn định thay vì suy giảm. Việc này giúp báo cáo phản ánh trung thực với artifact final.

---

## 4. Bằng chứng trước / sau (80–120 từ)

**run_id clean:** `2026-04-15T10-16Z`  
**run_id inject:** `inject-bad`

Từ `artifacts/eval/before_after_eval.csv` và `artifacts/eval/after_inject_bad.csv`:

- `q_refund_window`: `contains_expected=yes`, `hits_forbidden=no`
- `q_leave_version`: `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`

Tổng hợp định lượng:

| Scenario   | hit_correct_rate | hits_forbidden_rate |
| ---------- | ---------------- | ------------------- |
| Clean run  | 1.0              | 0.0                 |
| Inject run | 1.0              | 0.0                 |

Thêm bằng chứng chấm điểm từ `artifacts/eval/grading_run.jsonl`: cả `gq_d10_01`, `gq_d10_02`, `gq_d10_03` đều pass; riêng `gq_d10_03` có `top1_doc_matches=true`.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm thời gian, tôi sẽ triển khai một dashboard đơn giản để visualize các metric như `hit_correct` và `hits_forbidden` theo từng run_id. Điều này giúp theo dõi xu hướng chất lượng retrieval theo thời gian và phát hiện regression nhanh hơn khi pipeline thay đổi.
