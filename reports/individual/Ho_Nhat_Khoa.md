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

**Anomaly**: Freshness báo `FAIL` dù pipeline vừa chạy và publish thành công.

Ở run final `run_id=2026-04-15T10-16Z`, tôi quan sát trạng thái `publish_boundary=PASS` nhưng tổng kết freshness vẫn `FAIL`. Ban đầu dễ nhầm đây là lỗi monitor. Khi đối chiếu dữ liệu nguồn, tôi xác nhận nguyên nhân nằm ở ingest boundary: `latest_exported_at` của sample CSV là `2026-04-10T08:00:00`, đã quá SLA 24h.

Tôi xử lý bằng cách tách rõ hai ranh giới trong `freshness_check.py`:

- ingest boundary phản ánh độ tươi dữ liệu nguồn,
- publish boundary phản ánh độ tươi vận hành pipeline.

Nhờ đó, báo cáo freshness vừa đúng kỹ thuật vừa hữu ích cho vận hành: biết chính xác fail do upstream stale data hay do pipeline không chạy.

---

## 4. Bằng chứng trước / sau

**run_id `2026-04-15T10-16Z`** và **run_id `inject-bad`**:

```
freshness_check=FAIL {
	"sla_hours": 24.0,
	"ingest_boundary": {"status": "FAIL", ...},
	"publish_boundary": {"status": "PASS", ...},
	"pipeline_lag_hours": ...,
	"reason": "freshness_sla_exceeded"
}
```

Điểm quan trọng là cấu trúc output hiện đã thể hiện đầy đủ hai boundary để giải thích đúng nguyên nhân fail.

Kết quả grading final trong `artifacts/eval/grading_run.jsonl`:

- `gq_d10_01`: `contains_expected=true`, `hits_forbidden=false`
- `gq_d10_03`: `top1_doc_matches=true`

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ đọc `sla_hours` trực tiếp từ `contracts/data_contract.yaml` (field `freshness.sla_hours`) thay vì chỉ từ env var `FRESHNESS_SLA_HOURS`. Lợi ích: SLA được version cùng với data contract — khi team cập nhật contract (ví dụ thắt SLA từ 24h xuống 12h), freshness check tự động phản ánh mà không cần đổi env. Đây là bước tiến tới "rule versioning không hard-code" theo tiêu chí Distinction của SCORING.
