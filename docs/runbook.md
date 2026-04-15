# Runbook - Lab Day 10 (incident toi gian)

---

## Symptom

1. Agent trả lời sai policy (ví dụ xuất hiện "14 ngày" thay vì "7 ngày").
2. Grading check có `hits_forbidden=true` hoặc `top1_doc_matches=false`.
3. Pipeline dừng với thông báo `PIPELINE_HALT`.
4. Freshness check trả về `FAIL` do vượt SLA.

---

## Detection

1. Log pipeline: `artifacts/logs/run_<run_id>.log`.
2. Manifest snapshot: `artifacts/manifests/manifest_<run_id>.json`.
3. Quarantine ratio: `quarantine_records/raw_records`.
4. Eval signal: `contains_expected`, `hits_forbidden`, `top1_doc_expected`.
5. Freshness signal: `PASS/WARN/FAIL` với `ingest_boundary`, `publish_boundary`, `pipeline_lag_hours` và `sla_hours`.

---

## Diagnosis

| Buoc | Viec lam                                         | Ket qua mong doi                                              |
| ---- | ------------------------------------------------ | ------------------------------------------------------------- |
| 1    | Kiểm tra manifest mới nhất và xác định `run_id`  | Xác nhận batch đang phục vụ retrieval                         |
| 2    | Kiểm tra `cleaned_records`, `quarantine_records` | Nhìn thấy biến động bất thường so với baseline                |
| 3    | Mở file quarantine và xem cột `reason`           | Tìm được lý do gây fail (unknown doc/date/duplicate/HR stale) |
| 4    | Đối chiếu expectation fail trong log             | Xác định fail thuộc `warn` hay `halt` (E1..E8)                |
| 5    | Chạy retrieval eval trên bộ câu hỏi mẫu          | Xác nhận tác động đối với câu hỏi refund/HR/SLA               |

Lệnh khuyến nghị:

```bash
python etl_pipeline.py run --run-id debug-<tag>
python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json
python eval_retrieval.py --out artifacts/eval/before_after_eval.csv
python instructor_quick_check.py --grading artifacts/eval/grading_run.jsonl
```

---

## Mitigation

1. Nếu expectation `halt` fail: sửa dữ liệu/rule, chạy lại pipeline không dùng `--skip-validate`.
2. Nếu retrieval có forbidden evidence: đảm bảo refund fix bật, và rerun để prune stale vectors.
3. Nếu freshness FAIL: đọc chi tiết boundary nào fail. Nếu fail ở ingest, cập nhật export mới; nếu fail ở publish, chạy lại pipeline để tạo manifest/run_timestamp mới.
4. Nếu grading không đạt gq_d10_03: ưu tiên sửa luồng HR versioning và top-1 ranking evidence.

---

## Prevention

1. Duy trì contract allowlist và cutoff versioning đồng bộ với cleaning rules.
2. Bổ sung pytest unit/integration cho transform, expectations, freshness.
3. Chạy quick check artifact trước merge final.
4. Quy định owner final run chốt artifact một lần để tránh sai lệch run_id.
