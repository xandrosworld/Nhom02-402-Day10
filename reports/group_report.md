# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** ___________  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| ___ | Ingestion / Raw Owner | ___ |
| ___ | Cleaning & Quality Owner | ___ |
| ___ | Embed & Idempotency Owner | ___ |
| ___ | Monitoring / Docs Owner | ___ |

**Ngày nộp:** ___________  
**Repo:** ___________  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

_________________

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

_________________

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

<!-- 
  BẢNG NÀY LÀ GÌ VÀ DÙNG ĐỂ LÀM GÌ?
  ---
  Theo SCORING.md, mỗi rule/expectation mới phải có "tác động đo được" trên ít nhất một
  trong: CSV mẫu, inject Sprint 3, hoặc bảng này. Nếu không điền → GV coi là trivial
  → trừ tối đa -4 điểm. Bảng này là bằng chứng các expectation E7, E8 (do Hồ Nhất Khoa
  thêm vào quality/expectations.py) có ảnh hưởng thực sự, không phải placeholder.
-->

| Rule / Expectation mới | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ |
|------------------------|-----------------|----------------------------|----------|
| **E7 `corpus_completeness`** (severity: warn) — kiểm tra tất cả 4 `ALLOWED_DOC_IDS` phải có ít nhất 1 chunk sau clean | Standard run `run_id=standard-v1`: `missing_doc_ids=[]` → **PASS** | Custom inject (xoá toàn bộ sla_p1_2026 khỏi CSV): `missing_doc_ids=['sla_p1_2026']` → **WARN fires** | Log: `expectation[corpus_completeness] OK (warn) :: missing_doc_ids=[]`; unit test inject xác nhận `passed=False` |
| **E8 `chunk_id_unique_non_empty`** (severity: halt) — `chunk_id` là primary key ChromaDB, phải không rỗng và duy nhất | Standard run `run_id=standard-v1`: `empty_chunk_ids=0, duplicate_ids=0` → **PASS** | Inject duplicate chunk_id (mock `_stable_chunk_id` trả cùng ID): `duplicate_ids=1` → **HALT fires**, `should_halt=True` | Log: `expectation[chunk_id_unique_non_empty] OK (halt) :: empty_chunk_ids=0, duplicate_ids=0`; unit test inject xác nhận halt |

**Rule chính (baseline + mở rộng):**

- …

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

_________________

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

_________________

**Kết quả định lượng (từ CSV / bảng):**

_________________

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

<!-- 
  PHẦN NÀY LÀ GÌ?
  Giải thích kết quả freshness_check trong log — bắt buộc theo SCORING mục 3 (quality report
  có run_id + interpret). Dữ liệu do Hồ Nhất Khoa cung cấp từ monitoring/freshness_check.py.
-->

**SLA đã chọn:** 24 giờ (env var `FRESHNESS_SLA_HOURS=24`, khớp `contracts/data_contract.yaml`).

**Freshness check đo ở 2 ranh giới (Distinction criterion):**

- **Boundary 1 — ingest** (`latest_exported_at`): độ tươi của dữ liệu nguồn (CSV export).
- **Boundary 2 — publish** (`run_timestamp`): thời điểm pipeline chạy và embed vào ChromaDB.

**Kết quả trên sample CSV (`run_id=standard-v1`):**

```
freshness_check=FAIL {
  "ingest_boundary": {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 127.2, "status": "FAIL"},
  "publish_boundary": {"run_timestamp": "2026-04-15T09:30:00+00:00", "age_hours": 0.5, "status": "PASS"},
  "pipeline_lag_hours": 126.7
}
```

**Giải thích:** `freshness_check=FAIL` là **hành vi đúng và có chủ đích** với sample CSV — dữ liệu nguồn được export ngày 10/04, vượt SLA 24h so với ngày chạy lab (15/04). Tuy nhiên `publish_boundary=PASS` xác nhận pipeline đã chạy và embed thành công gần đây. SLA áp cho **độ tươi của dữ liệu nguồn** (ingest), không áp cho thời điểm pipeline. Chi tiết đầy đủ trong `docs/runbook.md`.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

_________________

---

## 6. Rủi ro còn lại & việc chưa làm

- …
