# Quality Report — Lab Day 10

**run_id:** `2026-04-15T10-16Z`  
**inject run:** `inject-bad`  
**date:** `2026-04-15`

## 1. Run summary

Clean run:

- `raw_records=10`
- `cleaned_records=5`
- `quarantine_records=5`
- collection: `day10_kb`
- embedding: `voyage-multilingual-2`

Inject run:

- `raw_records=10`
- `cleaned_records=5`
- `quarantine_records=5`
- flags: `--no-refund-fix --skip-validate`

## 2. Expectation results

The final clean run passed all active expectations:

- `min_one_row`
- `no_empty_doc_id`
- `refund_no_stale_14d_window`
- `chunk_min_length_8`
- `effective_date_iso_yyyy_mm_dd`
- `hr_leave_no_stale_10d_annual`
- `corpus_completeness`
- `chunk_id_unique_non_empty`

Measured impact from the new rules:

- the stale HR 2025 row was quarantined
- the legacy catalog row was quarantined
- duplicate refund content was quarantined
- malformed and missing-date rows were blocked before publish

## 3. Retrieval and grading evidence

Files:

- `artifacts/eval/before_after_eval.csv`
- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/grading_run.jsonl`

Final clean eval:

- `4/4` queries had `contains_expected=yes`
- `0/4` queries had `hits_forbidden=yes`
- `q_leave_version` kept `top1_doc_expected=yes`

Grading with the lecturer's updated question set:

- `gq_d10_01`: pass
- `gq_d10_02`: pass with `resolution = 4 giờ`
- `gq_d10_03`: pass with `top1_doc_matches=true`

## 4. Before / after interpretation

For the final code state, retrieval stays stable between the clean run and the later `inject-bad` run:

- `q_refund_window` still returns the correct `7 ngày làm việc`
- `hits_forbidden=no` in both eval CSV files
- overall retrieval summary remains `hit_correct_rate=1.0` and `hits_forbidden_rate=0.0`

Reason:

The stricter cleaning rules now quarantine the stale refund row before publish because it is recognized as a bad export / system-note record. That means `--no-refund-fix --skip-validate` is no longer enough to let that stale refund chunk survive into Chroma.

This changes where the protection happens:

- before: corruption could survive longer and be seen in retrieval
- now: corruption is blocked earlier at cleaning / quarantine

## 5. Freshness and observability

Freshness result from the clean run:

- SLA: `24h`
- `ingest_boundary`: `FAIL`
- `publish_boundary`: `PASS`
- `pipeline_lag_hours`: about `122.278`

This is expected on the provided sample because `latest_exported_at=2026-04-10T08:00:00` is older than the configured SLA. The monitor still adds value because it separates upstream stale data from successful publish timing.

## 6. Conclusion

The final Day 10 pipeline is stable and observable:

- only cleaned data is published to `day10_kb`
- bad rows are quarantined before embed
- grading passes all three required questions on the updated question set
- freshness monitoring reports both ingest and publish boundaries

In the final version of the project, the strongest measurable impact is visible in quarantine behavior, expectation results, and stable retrieval quality after publish.
