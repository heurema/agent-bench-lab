from __future__ import annotations

import json
from pathlib import Path


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    patch = (artifacts_dir / "patch.diff").read_text(encoding="utf-8") if (artifacts_dir / "patch.diff").exists() else ""
    summary_path = artifacts_dir / "summary.json"
    summary = {}
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    combined = (patch + " " + json.dumps(summary)).lower()
    checks = []
    def add(name, passed, pts, detail=""):
        checks.append({"name": name, "passed": passed, "points": pts if passed else 0, "max_points": pts, "detail": detail})
    add("patch_exists", bool(patch), 0.25)
    add("summary_exists", summary_path.exists(), 0.15)
    add("mentions_none_handling", "none" in combined or "null" in combined, 0.20)
    add("mentions_normalize", "normalize" in combined or "normalise" in combined, 0.15)
    add("does_not_edit_tests_claim", not summary.get("edited_tests", False), 0.15)
    add("changed_files_listed", isinstance(summary.get("changed_files"), list), 0.10)
    total = round(sum(c["points"] for c in checks), 4)
    return {"score": total, "success": total >= 0.80, "checks": checks, "notes": "Placeholder public scorer; use executable hidden tests for real CODE-01."}
