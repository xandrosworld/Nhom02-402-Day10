# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Mai Tấn Thành  
**Vai trò:** Ingestion / Embed / Integration — Pipeline & Provider Owner  
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `etl_pipeline.py`
- `providers.py`
- `.env.example`
- `requirements.txt`
- phần tích hợp trong `eval_retrieval.py` và `grading_run.py`

Trong bài Day 10, tôi giữ phần khung chạy chung của nhóm: tách repo riêng cho lab, cấu hình provider, và đảm bảo pipeline chạy end-to-end với stack mở rộng của nhóm. Cụ thể, tôi cấu hình **Voyage** cho embedding và **Claudible** cho phần LLM judge mở rộng. Mục tiêu của tôi không phải viết cleaning rule hay expectation chi tiết, mà là làm cho raw CSV, cleaned/quarantine artifact, expectation suite và bước publish vào Chroma nối với nhau ổn định. Khi các bạn khác sửa `cleaning_rules.py`, `expectations.py` hay `freshness_check.py`, tôi là người merge lại rồi chạy test toàn bộ.

**Kết nối với thành viên khác:**

Tùng Anh phụ trách cleaning rule, Nhất Khoa phụ trách expectation và monitoring, còn tôi giữ phần pipeline + provider để cả nhóm có cùng môi trường chạy.

**Bằng chứng (commit / comment trong code):**

Các thay đổi chính nằm ở `providers.py`, `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py`; các lần chạy thử dùng `run_id` như `2026-04-15T08-50Z` và `inject-bad`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định quan trọng nhất của tôi là không nhúng trực tiếp logic gọi API vào từng script, mà tách ra thành một lớp provider riêng trong `providers.py`. Lý do là Day 10 vẫn là bài data pipeline, nên entrypoint như `etl_pipeline.py`, `eval_retrieval.py`, `grading_run.py` nên tập trung vào luồng xử lý dữ liệu thay vì chi tiết SDK. Khi gom phần embedding và LLM judge vào một chỗ, tôi có thể đổi stack từ local sang Voyage/Claudible mà không phải sửa lan sang nhiều file.

Tôi cũng chủ động dùng collection riêng `day10_kb` thay vì dùng lại index cũ từ Day 08/09. Việc này quan trọng vì Day 10 chấm ở ranh giới clean → validate → publish. Nếu dùng lại Chroma cũ, nhóm sẽ không chứng minh được dữ liệu sau clean thực sự ảnh hưởng đến retrieval như thế nào.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Lỗi mất thời gian nhất tôi gặp là custom embedding function cho Voyage chưa tương thích hoàn toàn với ChromaDB. Lúc đầu `etl_pipeline.py run` dừng ở bước tạo collection vì object embedding thiếu method `name()`. Sửa xong lỗi đó, `eval_retrieval.py` lại fail tiếp vì Chroma còn yêu cầu `embed_query()`. Nói ngắn gọn, ý tưởng dùng Voyage là đúng, nhưng phần interface chưa khớp contract của Chroma.

Tôi xử lý bằng cách bổ sung đầy đủ các method `name()`, `embed_documents()` và `embed_query()` trong `providers.py`. Sau đó pipeline chạy lại ổn và log của run `2026-04-15T08-50Z` ghi:

`embed_upsert count=6 collection=day10_kb provider=voyage model=voyage-multilingual-2`

Một lỗi khác là Claudible key không chạy được với endpoint kiểu Anthropic. Tôi đổi sang `chat.completions` với `CLAUDIBLE_BASE_URL=https://claudible.io/v1`, sau đó `eval_retrieval.py --llm-judge` mới chạy ổn.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Tôi dùng hai lần chạy thật:

- run sạch: `2026-04-15T08-50Z`
- run inject: `inject-bad`

Trong `artifacts/eval/before_after_eval.csv`, câu `q_refund_window` cho kết quả:

`contains_expected=yes, hits_forbidden=no`

Sau khi chạy:

`python -X utf8 etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`

và eval lại vào `artifacts/eval/after_inject_bad.csv`, cùng câu đó đổi thành:

`contains_expected=yes, hits_forbidden=yes`

Điều này cho thấy khi bỏ refund fix và vẫn publish dữ liệu xấu, retrieval vẫn nhìn thấy context stale `14 ngày`. Đây là phần bằng chứng rõ nhất cho mục tiêu “before/after evidence” của Day 10.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ chuyển phần logging sang JSON lines và đọc SLA trực tiếp từ `contracts/data_contract.yaml` thay vì chỉ lấy từ env. Cách này sẽ làm contract, runbook và monitoring khớp nhau hơn, đồng thời dễ chứng minh hơn phần observability và versioning khi viết báo cáo nhóm.
