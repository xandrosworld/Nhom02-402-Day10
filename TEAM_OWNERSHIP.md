# Team Ownership - Day 10

Nguyen tac:
- Moi nguoi chi sua file trong ownership cua minh.
- Khong doi interface ham co san neu chua thong qua Mai Tan Thanh.
- Khong commit `.env`.
- Khong commit artifact tam thoi tu may ca nhan. Artifact final do Mai Tan Thanh chay va commit mot lan.

Branches:
- `feat/pipeline-thanh`
- `feat/transform-tunganh`
- `feat/quality-khoa`
- `feat/eval-phuc`
- `feat/docs-nam`

Ownership:
- Mai Tan Thanh
  - `etl_pipeline.py`
  - `.env.example`
  - `requirements.txt`
  - `providers.py`
  - merge, final run, final artifacts

- Dang Tung Anh
  - `transform/cleaning_rules.py`

- Ho Nhat Khoa
  - `quality/expectations.py`
  - `monitoring/freshness_check.py`

- Nguyen Duc Hoang Phuc
  - `eval_retrieval.py`
  - `grading_run.py`
  - `docs/quality_report.md`

- Pham Le Hoang Nam
  - `contracts/data_contract.yaml`
  - `docs/pipeline_architecture.md`
  - `docs/data_contract.md`
  - `docs/runbook.md`
  - `reports/group_report.md`

Final run owner:
- Chi Mai Tan Thanh duoc commit:
  - `artifacts/cleaned/*`
  - `artifacts/manifests/*`
  - `artifacts/quarantine/*`
  - `artifacts/eval/*`
  - `artifacts/logs/*`
