# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Nhom02-402-Day10  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Mai Tấn Thành (2A202600127) | `etl_pipeline.py`, `.env.example`, `requirements.txt`, `providers.py`, merge + final run | 26ai.thanhmt@vinuni.edu.vn |
| Đặng Tùng Anh (2A202600026) | `transform/cleaning_rules.py` | 26ai.anhdt2@vinuni.edu.vn |
| Hồ Nhất Khoa (2A202600066) | `quality/expectations.py`, `monitoring/freshness_check.py` | 26ai.khoahn@vinuni.edu.vn |
| Nguyễn Đức Hoàng Phúc (2A202600150) | `eval_retrieval.py`, `grading_run.py`, `docs/quality_report.md` | 26ai.phucndh@vinuni.edu.vn |
| Phạm Lê Hoàng Nam (2A202600416) | `contracts/data_contract.yaml`, `docs/*.md`, `reports/group_report.md` | 26ai.namplh@vinuni.edu.vn |

**Ngày nộp:** 15/04/2026  
**Repo:** xandrosworld/Nhom02-402-Day10  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

Nhóm triển khai pipeline ETL theo chuỗi: ingest dữ liệu raw CSV, làm sạch và cách ly dữ liệu lỗi, chạy expectation gate, embed vào ChromaDB, ghi manifest và kiểm tra freshness. Nguồn raw hiện tại là `data/raw/policy_export_dirty.csv`; mọi lần chạy đều sinh `run_id` và ghi vào log/manifest để truy vết. Luồng chạy chính sử dụng `etl_pipeline.py run`: gọi `clean_rows()` để tách `cleaned`/`quarantine`, sau đó `run_expectations()` quyết định dừng (`PIPELINE_HALT`) hay cho phép embed. Ở bước embed, collection được upsert theo `chunk_id` và prune id cũ để giữ tính idempotent. Cuối pipeline, hệ thống ghi `manifest_<run_id>.json` rồi kiểm freshness theo SLA. Hai run gần nhất đang có artifact là `ci-smoke` và `ci-smoke2`, đều cho `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`. Kết quả này cho thấy pipeline ổn định trên cùng bộ dữ liệu đầu vào.

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

`python etl_pipeline.py run`

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

| Rule / Expectation mới                                                                                                | Trước (số liệu)                                                                    | Sau / khi inject (số liệu)                                                                                              | Chứng cứ                                                                                                                      |
| --------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **E7 `corpus_completeness`** (severity: warn) — kiểm tra tất cả 4 `ALLOWED_DOC_IDS` phải có ít nhất 1 chunk sau clean | Standard run `run_id=standard-v1`: `missing_doc_ids=[]` → **PASS**                 | Custom inject (xoá toàn bộ sla_p1_2026 khỏi CSV): `missing_doc_ids=['sla_p1_2026']` → **WARN fires**                    | Log: `expectation[corpus_completeness] OK (warn) :: missing_doc_ids=[]`; unit test inject xác nhận `passed=False`             |
| **E8 `chunk_id_unique_non_empty`** (severity: halt) — `chunk_id` là primary key ChromaDB, phải không rỗng và duy nhất | Standard run `run_id=standard-v1`: `empty_chunk_ids=0, duplicate_ids=0` → **PASS** | Inject duplicate chunk_id (mock `_stable_chunk_id` trả cùng ID): `duplicate_ids=1` → **HALT fires**, `should_halt=True` | Log: `expectation[chunk_id_unique_non_empty] OK (halt) :: empty_chunk_ids=0, duplicate_ids=0`; unit test inject xác nhận halt |

**Rule chính (baseline + mở rộng):**

- Baseline clean: allowlist `doc_id`, chuẩn hóa `effective_date`, quarantine bản HR cũ, lọc text rỗng, dedupe, và fix refund 14→7.
- Rule mở rộng từ module transform: cắt tiền tố nhiễu (`FAQ bổ sung`, `Lưu ý`), chặn bản ghi có ghi chú lỗi migration/deprecated, và dùng `HR_CUTOFF_DATE` từ môi trường (không hard-code).
- Expectation hiện tại gồm E1–E8, trong đó các expectation mức `halt` gồm: `min_one_row`, `no_empty_doc_id`, `refund_no_stale_14d_window`, `effective_date_iso_yyyy_mm_dd`, `hr_leave_no_stale_10d_annual`, `chunk_id_unique_non_empty`; mức `warn` gồm `chunk_min_length_8`, `corpus_completeness`.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Khi inject dữ liệu làm trùng `chunk_id`, expectation `chunk_id_unique_non_empty` chuyển sang FAIL mức `halt`; pipeline sẽ dừng nếu không bật `--skip-validate`. Hướng xử lý là kiểm tra logic sinh ID ổn định tại `cleaning_rules.py`, loại nguyên nhân tạo ID trùng, sau đó chạy lại `python etl_pipeline.py run` để xác nhận `duplicate_ids=0`.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Nhóm dùng kịch bản inject theo đúng yêu cầu Sprint 3: `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`. Cách chạy này cố ý giữ lại dữ liệu stale (ví dụ cửa sổ hoàn tiền 14 ngày) và bỏ chặn expectation `halt` để mô phỏng tình huống dữ liệu xấu vẫn đi vào vector store. Kịch bản đối chiếu là chạy pipeline chuẩn (`python etl_pipeline.py run --run-id clean-good`) rồi thực hiện đánh giá retrieval.

**Kết quả định lượng (từ CSV / bảng):**

Tại thời điểm cập nhật báo cáo, thư mục `artifacts/eval` trên nhánh `main` chưa có file CSV/JSONL final (`before_after_eval.csv`, `grading_run.jsonl`). Vì vậy, nhóm ghi nhận trạng thái “chờ final run owner” để hoàn tất bằng chứng định lượng cho phần before/after retrieval. Dữ liệu nền hiện có trong manifest (`ci-smoke`, `ci-smoke2`) vẫn ổn định, tạo điều kiện để chạy tiếp vòng inject/eval ngay khi owner final run chốt artifact. Kế hoạch bổ sung bằng chứng là: (1) chạy inject-bad, (2) chạy clean-good, (3) xuất `artifacts/eval/before_after_eval.csv` và `artifacts/eval/grading_run.jsonl`, (4) đính kèm 2 dòng so sánh `contains_expected` và `hits_forbidden` cho câu `q_refund_window`/`q_leave_version`.

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

**Kết quả trên sample CSV (`run_id=ci-smoke2`):**

```
freshness_check=FAIL {
  "sla_hours": 24.0,
  "ingest_boundary": {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 122.092, "status": "FAIL"},
  "publish_boundary": {"run_timestamp": "2026-04-14T19:54:31.156431+00:00", "age_hours": 14.184, "status": "PASS"},
  "pipeline_lag_hours": 107.909,
  "reason": "freshness_sla_exceeded"
}
```

**Giải thích:** `FAIL` đến từ ingest boundary vì dữ liệu nguồn đã cũ hơn SLA 24 giờ. Đồng thời, publish boundary vẫn `PASS`, chứng tỏ pipeline chạy gần đây và publish thành công. Cách đọc này giúp tách bạch lỗi “dữ liệu nguồn stale” với lỗi “pipeline không chạy”. Chi tiết hướng xử lý đã ghi tại `docs/runbook.md`.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

Day 10 là lớp kiểm soát chất lượng dữ liệu trước khi retrieval/agent hoạt động. Nếu bỏ qua clean + expectation gate, agent Day 09 có thể truy hồi nhầm version policy dù prompt đúng. Vì vậy, collection `day10_kb` được dùng như đầu vào đã qua chuẩn hóa và quan sát được (log, manifest, quarantine) để giảm rủi ro trả lời sai ngữ cảnh.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa có artifact eval/grading final trong `artifacts/eval`; cần owner final run bổ sung trước khi nộp.
- Chưa có bộ test tự động hoàn chỉnh cho toàn bộ flow inject/eval trên nhánh hiện tại.
- Dữ liệu sample đang stale theo SLA 24h; cần xác định rõ policy xử lý freshness cho môi trường demo và môi trường thực.
- Cần khóa checklist “doc khớp src” trước merge để tránh lệch tài liệu khi module kỹ thuật thay đổi nhanh.
