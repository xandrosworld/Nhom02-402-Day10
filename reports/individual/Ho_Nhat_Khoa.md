# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Hồ Nhất Khoa  
**Vai trò:** Monitoring / Quality — Quality Expectations & Freshness Check  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** 400–650 từ

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách hai module:

- **`quality/expectations.py`** — hàm `run_expectations(cleaned_rows)`: định nghĩa toàn bộ expectation suite (E1–E8), bao gồm 6 expectation baseline và 2 expectation mới do tôi thêm: `corpus_completeness` (E7, warn) và `chunk_id_unique_non_empty` (E8, halt).
- **`monitoring/freshness_check.py`** — hàm `check_manifest_freshness(manifest_path, sla_hours, now)`: nâng cấp từ đo 1 ranh giới lên **2 ranh giới** (ingest boundary và publish boundary), bổ sung `pipeline_lag_hours`.

Kết nối với thành viên khác: module của tôi được gọi trực tiếp từ `etl_pipeline.py` (Mai Tan Thanh) sau bước clean. Kết quả expectation quyết định pipeline halt hay tiếp tục embed. Dữ liệu freshness được ghi vào manifest, phục vụ `docs/runbook.md` (Pham Le Hoang Nam). Số liệu `metric_impact` từ E7, E8 được cung cấp cho `reports/group_report.md`.

---

## 2. Một quyết định kỹ thuật

**Chọn `severity="halt"` cho E8 (`chunk_id_unique_non_empty`) thay vì `"warn"`.**

`chunk_id` là primary key cho ChromaDB `upsert`. Nếu hai row có cùng `chunk_id`, ChromaDB sẽ ghi đè chunk cũ bằng chunk mới một cách im lặng — không có lỗi, không có cảnh báo. Điều này phá vỡ tính idempotency của embed: chạy lại pipeline hai lần sẽ cho kết quả khác nhau tùy thứ tự row. Trong grading, nếu chunk đúng bị ghi đè bởi chunk stale, `hits_forbidden` có thể bật lên mà không có dòng log nào giải thích tại sao.

Vì lý do đó, tôi quyết định `severity="halt"`: dừng pipeline ngay khi phát hiện ID trùng, yêu cầu fix nguồn gốc (lỗi trong `_stable_chunk_id` hoặc dữ liệu inject) thay vì để corruption đi vào vector store. Đây là trường hợp mà "fail early" bảo vệ tính tin cậy của toàn bộ retrieval stack.

---

## 3. Một lỗi hoặc anomaly đã xử lý

**Anomaly**: `freshness_check=FAIL` ngay cả khi pipeline vừa chạy xong.

Sau lần chạy đầu tiên với `run_id=standard-v1`, log ghi `freshness_check=FAIL {"age_hours": 127.2}`. Ban đầu tôi nghĩ đây là lỗi code. Sau khi đọc kỹ `freshness_check.py`, tôi phát hiện hàm cũ dùng `latest_exported_at` (timestamp trong CSV nguồn, ngày `2026-04-10T08:00:00`) làm **duy nhất** mốc đo — không phải `run_timestamp` (khi pipeline chạy).

Vấn đề: `latest_exported_at` phản ánh **độ tươi của dữ liệu nguồn**, không phải **độ tươi của pipeline**. Với CSV mẫu có `exported_at=2026-04-10`, freshness sẽ luôn FAIL sau 24 giờ dù pipeline chạy bất cứ lúc nào.

Fix: nâng cấp lên 2-boundary — đo cả `latest_exported_at` (ingest boundary) lẫn `run_timestamp` (publish boundary). Sau khi fix, log hiển thị rõ: `"ingest_boundary": {"status": "FAIL", "age_hours": 127.2}` và `"publish_boundary": {"status": "PASS", "age_hours": 0.5}`. Đây là hành vi **đúng và có chủ đích**: dữ liệu nguồn cũ (FAIL) nhưng pipeline đã chạy gần đây (PASS). Runbook giải thích SLA áp cho ingest, không áp cho publish.

---

## 4. Bằng chứng trước / sau

**run_id `standard-v1`** — log `artifacts/logs/run_standard-v1.log`:

```
# TRƯỚC (freshness_check.py cũ — 1 boundary):
freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 127.2, "sla_hours": 24}

# SAU (freshness_check.py mới — 2 boundary):
freshness_check=FAIL {"sla_hours": 24, "ingest_boundary": {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 127.2, "status": "FAIL"}, "publish_boundary": {"run_timestamp": "2026-04-15T09:30:00+00:00", "age_hours": 0.481, "status": "PASS"}, "pipeline_lag_hours": 126.719, "reason": "freshness_sla_exceeded"}
```

`pipeline_lag_hours` dương (~127 giờ) vì pipeline chạy sau khi dữ liệu được export 5 ngày — đây là bình thường. FAIL đến từ ingest boundary (data cũ), publish boundary vẫn PASS (pipeline vừa chạy).

Kết quả grading (`run_id=standard-v1`): `gq_d10_01 contains_expected=yes, hits_forbidden=no`; `gq_d10_03 top1_doc_matches=yes`.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ đọc `sla_hours` trực tiếp từ `contracts/data_contract.yaml` (field `freshness.sla_hours`) thay vì chỉ từ env var `FRESHNESS_SLA_HOURS`. Lợi ích: SLA được version cùng với data contract — khi team cập nhật contract (ví dụ thắt SLA từ 24h xuống 12h), freshness check tự động phản ánh mà không cần đổi env. Đây là bước tiến tới "rule versioning không hard-code" theo tiêu chí Distinction của SCORING.
