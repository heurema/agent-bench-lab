from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_lifecycle_check_passes():
    result = run_script("scripts/check_lifecycle.py")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Lifecycle check passed" in result.stdout


def test_hardening_gate_check_passes():
    result = run_script("scripts/check_hardening_gates.py")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Hardening gate check passed" in result.stdout


def test_mutation_smoke_writes_to_supplied_output_root(tmp_path):
    result = run_script("scripts/run_mutation_smoke.py", "--out-root", str(tmp_path))

    assert result.returncode == 0, result.stdout + result.stderr
    for task_id in ("IF-01", "DATA-01", "DOC-01", "SUP-01", "API-01"):
        assert (tmp_path / task_id / "case_mutation_001" / "check_config.json").exists()


def test_lifecycle_marks_no_task_verified():
    data = json.loads((ROOT / "configs" / "task_lifecycle.json").read_text(encoding="utf-8"))

    assert all(not entry["verified"] for entry in data["tasks"].values())
    assert all(entry["status"] != "verified" for entry in data["tasks"].values())


def test_hardening_gates_cover_decision_grade_tasks_only():
    lifecycle = json.loads((ROOT / "configs" / "task_lifecycle.json").read_text(encoding="utf-8"))
    gates = json.loads((ROOT / "configs" / "hardening_gates.json").read_text(encoding="utf-8"))
    decision_grade = {
        task_id
        for task_id, entry in lifecycle["tasks"].items()
        if entry["status"] in {"decision-grade", "verified"}
    }

    assert set(gates["tasks"]) == decision_grade
