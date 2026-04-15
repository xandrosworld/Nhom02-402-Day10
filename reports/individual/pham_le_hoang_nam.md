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

Tôi dùng bằng chứng tương đương từ manifest (do nhánh hiện tại chưa có `before_after_eval.csv`) để chứng minh tính ổn định sau khi tài liệu được đồng bộ theo code:

- `run_id=ci-smoke`: `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`, `cleaned_csv=artifacts/cleaned/cleaned_ci-smoke.csv`.
- `run_id=ci-smoke2`: `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`, `cleaned_csv=artifacts/cleaned/cleaned_ci-smoke2.csv`.

Hai mốc này cho thấy baseline vận hành nhất quán giữa các lần chạy; từ đó tôi có cơ sở để viết phần kiến trúc, contract và runbook theo số liệu thực tế thay vì suy diễn.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ bổ sung một checklist “Doc-Source Consistency” thành bước bắt buộc trước merge (ví dụ: expectation count, freshness fields, quarantine reasons). Như vậy, mỗi khi code thay đổi, đội có thể rà nhanh tài liệu theo checklist để giảm nguy cơ lệch tài liệu ở các vòng nộp sau.
