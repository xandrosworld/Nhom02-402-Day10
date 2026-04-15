# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Đức Hoàng Phúc  
**Vai trò:** Embed / Evaluation / Grading — Retrieval Owner  
**Ngày nộp:** 2026-04-15  

---

## 1. Tôi phụ trách phần nào?

File / module:
- eval_retrieval.py
- grading_run.py
- docs/quality_report.md

Tôi chịu trách nhiệm đánh giá retrieval sau pipeline ETL, kiểm tra hit_correct và hits_forbidden, đồng thời xây dựng grading JSONL.

Kết nối:
- Nhận dữ liệu từ ETL pipeline
- Dựa vào expectation suite
- Output dùng cho report

Bằng chứng:

=== EVAL SUMMARY ===

{'total': 4, 'hit_correct_rate': 1.0, 'hits_forbidden_rate': 0.0}

=== GRADING SUMMARY ===

{'total': 3, 'pass_rate': 1.0}

---

## 2. Một quyết định kỹ thuật

Tôi sử dụng hai metric: hit_correct và hits_forbidden thay vì chỉ accuracy. Điều này giúp phát hiện trường hợp context chứa dữ liệu sai dù answer đúng. Đây là yếu tố quan trọng trong RAG system.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Trong quá trình chạy `grading_run.py`, tôi gặp lỗi kết nối với embedding provider VoyageAI:

```bash
voyageai.error.APIConnectionError: Remote end closed connection without response
```

Lỗi xảy ra khi Chroma gọi embedding API trong quá trình query. Tôi xác định nguyên nhân là do phụ thuộc vào external API (VoyageAI), dẫn đến mất kết nối hoặc rate limit.

Để xử lý, tôi thêm một fallback vào quá trình gọi API.
Sau đó chạy lại pipeline:

```python
python etl_pipeline.py run
python grading_run.py
```
Kết quả ổn định hoàn toàn, xử lí được những trường hợp gặp lỗi. Điều này giúp hệ thống reproducible hơn.

---

## 4. Bằng chứng trước / sau (80–120 từ)

**run_id:** inject-bad vs clean

**Trước (inject-bad):**

Top docs: ['...14 ngày...', '...7 ngày...']
contains_expected = True
hits_forbidden = True


**Sau (clean pipeline):**

Top docs: ['...7 ngày...']
contains_expected = True
hits_forbidden = False


**Tổng hợp:**

| Scenario | hit_correct | hits_forbidden |
|----------|------------|----------------|
| Inject bad | 1.0 | 0.25 |
| Clean pipeline | 1.0 | 0.0 |

Điều này chứng minh rằng cleaning pipeline giúp loại bỏ dữ liệu stale, giảm nhiễu trong retrieval.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm thời gian, tôi sẽ triển khai một dashboard đơn giản để visualize các metric như `hit_correct` và `hits_forbidden` theo từng run_id. Điều này giúp theo dõi xu hướng chất lượng retrieval theo thời gian và phát hiện regression nhanh hơn khi pipeline thay đổi.
