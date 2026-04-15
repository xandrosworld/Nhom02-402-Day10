# Data contract - Lab Day 10

Tài liệu này đồng bộ với [contracts/data_contract.yaml](../contracts/data_contract.yaml) và implementation trong [transform/cleaning_rules.py](../transform/cleaning_rules.py).

---

## 1. Nguon du lieu (source map)

| Nguon                                                         | Phuong thuc ingest                | Failure mode chinh                                       | Metric / alert                                                            |
| ------------------------------------------------------------- | --------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------- |
| `data/raw/policy_export_dirty.csv`                            | CSV snapshot qua `csv.DictReader` | duplicate chunk, empty fields, doc_id lạ, date không ISO, chứa ghi chú lỗi migration | `raw_records`, `cleaned_records`, `quarantine_records` trong log/manifest |
| `data/docs/policy_refund_v4.txt`                              | canonical policy source           | stale migration chunk "14 ngày" chèn vào raw             | expectation `refund_no_stale_14d_window` = halt                           |
| `data/docs/hr_leave_policy.txt`                               | canonical HR source               | xung đột version 10 ngày (cũ) vs 12 ngày (2026)          | quarantine reason `stale_hr_policy_effective_date` + expectation HR halt  |
| `data/docs/sla_p1_2026.txt` + `data/docs/it_helpdesk_faq.txt` | canonical IT sources              | mật độ chính xác retrieval khi index bị bẩn              | theo dõi qua eval retrieval/grading                                       |

---

## 2. Schema cleaned

| Cot | Kieu | Bat buoc | Ghi chu |
| --- | --- | --- | --- |
| `chunk_id` | string | Co | Sinh ổn định từ `doc_id + chunk_text + seq` để upsert idempotent |
| `doc_id` | string | Co | Phải nằm trong allowlist (`policy_refund_v4`, `sla_p1_2026`, `it_helpdesk_faq`, `hr_leave_policy`) |
| `chunk_text` | string | Co | Không được rỗng; expectation cảnh báo nếu < 8 ký tự |
| `effective_date` | date (`YYYY-MM-DD`) | Co | Cho phép input DMY và chuẩn hóa về ISO |
| `exported_at` | datetime ISO 8601 | Co | Dùng để tính freshness từ manifest |

---

## 3. Quy tac quarantine va luong xu ly

- Record lỗi không bị xóa im lặng mà được ghi vào `artifacts/quarantine/quarantine_<run_id>.csv` kèm `reason`.
- Các lý do baseline: `unknown_doc_id`, `missing_effective_date`, `invalid_effective_date_format`, `stale_hr_policy_effective_date`, `missing_chunk_text`, `duplicate_chunk_text`, `contains_system_error_note`.
- Record đã vào quarantine không được embed cho đến khi owner module sửa nguồn/logic và rerun pipeline.
- Phê duyệt merge lại dữ liệu thuộc owner transform + quality, final publish do owner pipeline chốt.

---

## 4. Phien ban va canonical

- Source of truth refund: `data/docs/policy_refund_v4.txt` (window hợp lệ: 7 ngày).
- Source of truth HR leave: `data/docs/hr_leave_policy.txt` (bản 2026; 12 ngày cho nhân sự < 3 năm).
- Contract versioning: ngưỡng HR cutoff lấy từ biến môi trường `HR_CUTOFF_DATE` (mặc định `2026-01-01`); dữ liệu HR cũ hơn mốc này bị quarantine.
- Nếu mở rộng doc mới, cần cập nhật đồng thời 3 nơi: contract allowlist, cleaning rules, và test/eval set.

---

## 5. Expectation gate (tham chiếu src)

Expectation hiện có trong mã nguồn gồm 8 rule:

- Halt: `min_one_row`, `no_empty_doc_id`, `refund_no_stale_14d_window`, `effective_date_iso_yyyy_mm_dd`, `hr_leave_no_stale_10d_annual`, `chunk_id_unique_non_empty`.
- Warn: `chunk_min_length_8`, `corpus_completeness`.

Pipeline chỉ dừng khi fail expectation mức `halt` (trừ khi chạy có chủ đích với `--skip-validate`).
