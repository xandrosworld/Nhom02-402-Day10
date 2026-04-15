# Quality report — Lab Day 10 (nhóm)

**run_id:** 2026-04-15T09-12Z (clean) / inject-bad (corruption test)  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (inject-bad) | Sau (clean pipeline) | Ghi chú |
|--------|-------------------|----------------------|---------|
| raw_records | 10 | 10 | Dữ liệu đầu vào giữ nguyên |
| cleaned_records | 6 | 6 | Sau cleaning rules |
| quarantine_records | 4 | 4 | Các record lỗi bị loại |
| Expectation halt? | FAIL (skip-validate) | PASS | Inject cố tình bypass validation |

---

## 2. Before / after retrieval (bắt buộc)

> File kết quả:
- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/before_after_eval.csv`

---

### Câu hỏi then chốt: refund window (`q_refund_window`)

**Trước (inject-bad):**

- Top docs:
  - "14 ngày làm việc" ❌ (stale)
  - "7 ngày làm việc" ✅ (correct)
- contains_expected = True  
- hits_forbidden = True  

👉 Context chứa cả thông tin đúng và sai (rất nguy hiểm)

---

**Sau (clean pipeline):**

- Top docs:
  - chỉ còn "7 ngày làm việc" ✅
- contains_expected = True  
- hits_forbidden = False  

👉 Context sạch hoàn toàn, không còn stale data

---

### Merit: HR policy version (`q_leave_version`)

**Trước (inject-bad):**

- Top doc: `hr_leave_policy`
- contains_expected = True  
- hits_forbidden = False  
- top1_doc_expected = đúng

👉 Tuy chưa bị ảnh hưởng trực tiếp, nhưng context có dấu hiệu nhiễu từ policy khác

---

**Sau (clean pipeline):**

- Top doc: `hr_leave_policy`
- contains_expected = True  
- hits_forbidden = False  
- top1_doc_expected = đúng

👉 Retrieval ổn định và chính xác

---

### Tổng kết retrieval

| Scenario | hit_correct | hits_forbidden |
|----------|------------|----------------|
| Inject bad | 1.0 | 0.25 |
| Clean pipeline | 1.0 | 0.0 |

👉 Mặc dù accuracy không đổi, nhưng chất lượng context cải thiện rõ rệt

---

## 3. Freshness & monitor

Kết quả:

```json
freshness_check = FAIL
{
  "latest_exported_at": "2026-04-10T08:00:00",
  "age_hours": ~121,
  "sla_hours": 24,
  "reason": "freshness_sla_exceeded"
}
```

Giải thích:

- SLA được chọn: 24 giờ
- Dữ liệu đã cũ ~121 giờ → vượt SLA

=> FAIL là đúng behavior, giúp phát hiện data outdated trước khi ảnh hưởng downstream

---

## 4. Corruption inject (Sprint 3)
**Cách inject:**

Sử dụng:

```python
python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
```

**Loại corruption:**

- Stale policy: refund window = 14 ngày (thay vì 7)
- Bypass validation để dữ liệu lỗi vẫn được embed

**Cách phát hiện:**
1. Expectation suite:

```bash
refund_no_stale_14d_window → FAIL
```

2. Retrieval evaluation:
- hits_forbidden tăng từ 0.0 → 0.25
- xuất hiện chunk chứa "14 ngày"

**Insight quan trọng:**

- Model vẫn trả lời đúng (hit_correct = 1.0)
- Nhưng context bị nhiễu (hits_forbidden > 0)

👉 Đây là failure mode nguy hiểm trong RAG system

---

## 5. Hạn chế & việc chưa làm

- Chưa tự động visualize before/after (chart)
- Chưa có threshold alert cho hits_forbidden
- Chưa implement retry / fallback cho embedding provider (VoyageAI)
- Chưa kiểm soát contamination giữa các topic (cross-policy noise)
- Chưa có lineage tracking chi tiết theo chunk level