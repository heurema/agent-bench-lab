from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


def _expected(fixture_dir: Path) -> dict:
    rows = list(csv.DictReader((fixture_dir / "orders.csv").open(encoding="utf-8")))
    paid = [r for r in rows if r["status"] == "paid"]
    total = round(sum(float(r["amount_usd"]) for r in paid), 2)
    by_region = defaultdict(float)
    for r in paid:
        by_region[r["region"]] += float(r["amount_usd"])
    top_region = sorted(by_region.items(), key=lambda x: (-x[1], x[0]))[0][0]
    return {
        "paid_order_count": len(paid),
        "total_paid_revenue_usd": total,
        "top_region_by_paid_revenue": top_region,
        "active_customer_count": len({r["customer_id"] for r in paid}),
    }


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    expected = _expected(fixture_dir)
    metrics_path = artifacts_dir / "metrics.json"
    report_path = artifacts_dir / "report.md"
    checks = []
    metrics = {}
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception as exc:
            checks.append({"name": "metrics_json_parse", "passed": False, "points": 0, "max_points": 0.1, "detail": str(exc)})
    checks.append({"name": "metrics_json_exists", "passed": metrics_path.exists(), "points": 0.1 if metrics_path.exists() else 0, "max_points": 0.1})
    per_key = 0.15
    for key, value in expected.items():
        passed = metrics.get(key) == value
        checks.append({"name": f"metric_{key}", "passed": passed, "points": per_key if passed else 0, "max_points": per_key, "detail": f"expected={value!r} got={metrics.get(key)!r}"})
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    checks.append({"name": "report_exists", "passed": report_path.exists(), "points": 0.1 if report_path.exists() else 0, "max_points": 0.1})
    report_mentions = all(str(v) in report for v in expected.values())
    checks.append({"name": "report_mentions_metrics", "passed": report_mentions, "points": 0.2 if report_mentions else 0, "max_points": 0.2})
    total = round(sum(c["points"] for c in checks), 4)
    return {"score": min(total, 1.0), "success": total >= 0.85, "checks": checks, "expected_public": expected}
