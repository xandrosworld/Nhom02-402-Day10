# Kien truc pipeline - Lab Day 10

Nhom: Nhom02-402-Day10  
Cap nhat: 2026-04-15

---

## 1. So do luong

```text
data/raw/policy_export_dirty.csv
  -> load_raw_csv()
  -> clean_rows()
      -> allowlist doc_id + parse date + HR cutoff tu env
      -> quarantine neu co ghi chu loi migration/ban nhap/deprecated
      -> chuan hoa tien to FAQ/Luu y + fix refund 14->7 (neu bat)
      -> artifacts/cleaned/cleaned_<run_id>.csv
      -> artifacts/quarantine/quarantine_<run_id>.csv
  -> run_expectations()
      -> E1..E8 (halt/warn), halt neu expectation severity=halt fail
  -> cmd_embed_internal()
      -> upsert vector theo chunk_id
      -> prune id cu khong con trong cleaned
  -> artifacts/manifests/manifest_<run_id>.json
  -> check_manifest_freshness()
      -> ingest_boundary (latest_exported_at)
      -> publish_boundary (run_timestamp)
```

Trong luồng trên, `run_id` được ghi vào log, manifest và metadata embed để truy vết lineage của từng lần chạy.

---

## 2. Ranh gioi trach nhiem

| Thanh phan    | Input                              | Output                           | Owner nhom            |
| ------------- | ---------------------------------- | -------------------------------- | --------------------- |
| Ingest        | `data/raw/policy_export_dirty.csv` | `raw_records`, run log           | Mai Tan Thanh         |
| Transform     | Raw rows                           | cleaned/quarantine rows + reason | Dang Tung Anh         |
| Quality       | cleaned rows                       | expectation result + halt flag   | Ho Nhat Khoa          |
| Embed         | cleaned CSV                        | Chroma collection `day10_kb`     | Mai Tan Thanh         |
| Monitor       | manifest                           | freshness PASS/WARN/FAIL         | Ho Nhat Khoa          |
| Eval/Grading  | Chroma collection + question sets  | eval CSV / grading JSONL         | Nguyen Duc Hoang Phuc |
| Contract/Docs | source map + policy metadata       | docs và report nộp bài           | Pham Le Hoang Nam     |

---

## 3. Idempotency va rerun

Pipeline embed sử dụng hai cơ chế:

- `upsert(ids=chunk_id)` để tránh duplicate vector khi rerun cùng input.
- `delete(ids=prev_ids - current_ids)` để loại stale vectors không còn trong cleaned snapshot mới.

Manifest hiện có (`ci-smoke`, `ci-smoke2`) cho thấy record count ổn định (`raw=10`, `cleaned=6`, `quarantine=4`), phù hợp với kỳ vọng rerun có tính chất xác định.

---

## 4. Lien he Day 09

Day 10 quản lý chất lượng dữ liệu trước khi retrieval hoạt động. Nếu policy stale (ví dụ vẫn còn "14 ngày làm việc"), hệ retrieval sẽ trả top-k có ngữ cảnh sai dù câu trả lời top-1 có thể có vẻ đúng. Vì vậy Day 10 là lớp bảo vệ data layer cho Day 08/09.

---

## 5. Rui ro da biet

- Nếu bỏ qua validate (`--skip-validate`), dữ liệu lỗi vẫn có thể được embed cho mục đích demo inject.
- Freshness theo `latest_exported_at` có thể FAIL với dữ liệu mẫu cũ; cần diễn giải rõ trong runbook.
- Chưa có test tự động trong nhánh `main`; cần bổ sung pytest unit + integration trước final merge.
- Rule `corpus_completeness` ở mức `warn`; nếu thiếu hẳn một doc_id thì pipeline vẫn chạy nhưng chất lượng retrieval có thể giảm.
