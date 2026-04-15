"""
Kiểm tra freshness từ manifest pipeline (SLA đơn giản theo giờ).

Sinh viên mở rộng: đọc watermark DB, so sánh với clock batch, v.v.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Cho phép "2026-04-10T08:00:00" không có timezone
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def check_manifest_freshness(
    manifest_path: Path,
    *,
    sla_hours: float = 24.0,
    now: datetime | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Trả về ("PASS" | "WARN" | "FAIL", detail dict).

    Đo freshness ở **2 ranh giới** (Distinction criterion):
      - Boundary 1 (ingest): `latest_exported_at` — dữ liệu nguồn cũ bao lâu?
      - Boundary 2 (publish): `run_timestamp` — pipeline chạy gần đây chưa?

    pipeline_lag_hours = publish_dt - ingest_dt (âm nếu export trước khi pipeline chạy).
    """
    now = now or datetime.now(timezone.utc)
    if not manifest_path.is_file():
        return "FAIL", {"reason": "manifest_missing", "path": str(manifest_path)}

    data: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Boundary 1: ingest — khi nào dữ liệu rời khỏi hệ thống nguồn?
    ingest_ts = data.get("latest_exported_at")
    ingest_dt = parse_iso(str(ingest_ts)) if ingest_ts else None

    # Boundary 2: publish — khi nào pipeline embed xong vào ChromaDB?
    publish_ts = data.get("run_timestamp")
    publish_dt = parse_iso(str(publish_ts)) if publish_ts else None

    detail: Dict[str, Any] = {"sla_hours": sla_hours}

    if ingest_dt:
        ingest_age = (now - ingest_dt).total_seconds() / 3600.0
        detail["ingest_boundary"] = {
            "latest_exported_at": ingest_ts,
            "age_hours": round(ingest_age, 3),
            "status": "PASS" if ingest_age <= sla_hours else "FAIL",
        }
    else:
        detail["ingest_boundary"] = {"status": "UNKNOWN", "reason": "no_exported_at"}

    if publish_dt:
        publish_age = (now - publish_dt).total_seconds() / 3600.0
        detail["publish_boundary"] = {
            "run_timestamp": publish_ts,
            "age_hours": round(publish_age, 3),
            "status": "PASS" if publish_age <= sla_hours else "FAIL",
        }
    else:
        detail["publish_boundary"] = {"status": "UNKNOWN", "reason": "no_run_timestamp"}

    # Pipeline lag: khoảng thời gian từ export đến publish
    if ingest_dt and publish_dt:
        lag = (publish_dt - ingest_dt).total_seconds() / 3600.0
        detail["pipeline_lag_hours"] = round(lag, 3)

    ingest_status = detail["ingest_boundary"].get("status", "UNKNOWN")
    publish_status = detail["publish_boundary"].get("status", "UNKNOWN")

    if ingest_status == "FAIL" or publish_status == "FAIL":
        return "FAIL", {**detail, "reason": "freshness_sla_exceeded"}
    if ingest_status == "UNKNOWN" or publish_status == "UNKNOWN":
        return "WARN", {**detail, "reason": "partial_timestamps_available"}
    return "PASS", detail
