# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Phạm Lê Hoàng Nam  
**Vai trò:** Documentation & Contract Owner (Data contract, docs vận hành, báo cáo nhóm)  
**Ngày nộp:** 15/04/2026

---

## 1. Tôi phụ trách phần nào?

**File / module:**
Tôi phụ trách các hạng mục tài liệu và chuẩn hóa contract, gồm: `contracts/data_contract.yaml`, `docs/data_contract.md`, `docs/pipeline_architecture.md`, `docs/runbook.md`, và `reports/group_report.md`. Mục tiêu của tôi là bảo đảm phần mô tả bám sát đúng mã nguồn đang chạy, tránh tình trạng tài liệu đúng về hình thức nhưng lệch logic xử lý thực tế.

**Kết nối với thành viên khác:**
Tôi phối hợp trực tiếp với bạn Đặng Tùng Anh (module `transform/cleaning_rules.py`) và Hồ Nhất Khoa (module `quality/expectations.py`, `monitoring/freshness_check.py`) để đối chiếu rule mới, expectation E1–E8 và cơ chế freshness 2 ranh giới. Tôi cũng đồng bộ với Mai Tấn Thành để giữ thống nhất entrypoint và artifact pipeline khi chốt báo cáo nhóm.

**Bằng chứng (commit / comment trong code):**
Nhánh làm việc của tôi là `NamPLH/contract_doc`; sau đó đã được hợp nhất bằng lệnh `git merge NamPLH/contract_doc`. Các file tôi chịu trách nhiệm đều đã được cập nhật và loại bỏ placeholder trước khi merge.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất của tôi là ưu tiên nguyên tắc “docs phải phản ánh src code”, không ghi theo giả định. Cụ thể, tôi chọn cập nhật tài liệu theo hướng mô tả đúng hành vi thực tế thay vì mô tả lý tưởng. Ví dụ, phần freshness trong mã hiện tại đo ở 2 ranh giới (`ingest_boundary` và `publish_boundary`) và trả thêm `pipeline_lag_hours`; do đó tôi đã sửa toàn bộ tài liệu liên quan để không còn mô tả cũ kiểu một ranh giới duy nhất. Tương tự, expectation trong code đã mở rộng đến E8 và có phân tầng `halt/warn`, nên tài liệu contract và runbook cũng phải ghi đúng logic này. Cách làm này giúp đội tránh rủi ro chấm điểm thấp vì “report không khớp repo”, đồng thời giúp người đọc mới có thể chạy và debug đúng ngay từ lần đầu.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly lớn nhất tôi xử lý là tình trạng tài liệu bị lệch so với mã sau khi team cập nhật src. Triệu chứng cụ thể: file `docs/data_contract.md` bị vỡ bảng schema (lệch cột do ký tự `|`), và một số mục trong `reports/group_report.md` còn placeholder nên gây mơ hồ khi đối chiếu rubric. Ngoài ra, phần mô tả freshness trong tài liệu cũ chưa phản ánh đầy đủ output mới của `check_manifest_freshness()`.

Tôi phát hiện các điểm này bằng cách đọc chéo 3 lớp: source (`etl_pipeline.py`, `quality/expectations.py`, `monitoring/freshness_check.py`), artifact (`manifest_ci-smoke*.json`) và tài liệu. Sau đó, tôi chuẩn hóa lại bảng schema, bổ sung các rule mới vào tài liệu, cập nhật runbook theo đúng signal vận hành, và dọn các đoạn placeholder trong báo cáo nhóm. Kết quả là bộ docs hiện tại đã nhất quán với pipeline thực thi.

---

## 4. Bằng chứng trước / sau

Tôi dùng cả manifest và artifact eval/grading đã có để chứng minh tính ổn định sau khi tài liệu được đồng bộ theo code:

- `run_id=2026-04-15T10-16Z`: `raw_records=10`, `cleaned_records=5`, `quarantine_records=5`, `cleaned_csv=artifacts/cleaned/cleaned_2026-04-15T10-16Z.csv`.
- `run_id=inject-bad`: `raw_records=10`, `cleaned_records=5`, `quarantine_records=5`, `cleaned_csv=artifacts/cleaned/cleaned_inject-bad.csv`.

Từ `artifacts/eval/before_after_eval.csv` và `artifacts/eval/after_inject_bad.csv`, cả 4 câu hỏi đều đạt `contains_expected=yes`, `hits_forbidden=no`; với `q_leave_version` giữ `top1_doc_expected=yes`.

Trong `artifacts/eval/grading_run.jsonl`, 3 câu `gq_d10_01`, `gq_d10_02`, `gq_d10_03` đều pass, và `gq_d10_03` có `top1_doc_matches=true`.

Các mốc này cho thấy tài liệu hiện đã bám đúng hiện trạng pipeline final, tránh lệch giữa report và artifact nộp kèm.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ bổ sung một checklist “Doc-Source Consistency” thành bước bắt buộc trước merge (ví dụ: expectation count, freshness fields, quarantine reasons). Như vậy, mỗi khi code thay đổi, đội có thể rà nhanh tài liệu theo checklist để giảm nguy cơ lệch tài liệu ở các vòng nộp sau.
