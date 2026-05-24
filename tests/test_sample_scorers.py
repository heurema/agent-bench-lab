from pathlib import Path

import pytest

from agent_bench_lab.scoring import load_scorer, score_task


def test_sample_if01_score(tmp_path):
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "artifact.md").write_text("# Public Launch Note\n- This uses versioned tasks.\n- This uses repeatable scoring.\n- This uses public templates.\n", encoding="utf-8")
    result = score_task(root, "IF-01", "case_001", artifact_dir)
    assert result["success"]


def test_sample_data01_score(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    metrics = {
        "paid_order_count": 4,
        "total_paid_revenue_usd": 720.5,
        "top_region_by_paid_revenue": "NA",
        "active_customer_count": 4,
    }
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (artifact_dir / "report.md").write_text("4 720.5 NA 4", encoding="utf-8")
    result = score_task(root, "DATA-01", "case_001", artifact_dir)
    assert result["success"]


def test_scorer_interface_is_enforced(tmp_path):
    task_dir = tmp_path / "BAD-01"
    task_dir.mkdir()
    (task_dir / "scorer.py").write_text("def score(task_dir):\n    return {}\n", encoding="utf-8")

    with pytest.raises(TypeError, match="score signature"):
        load_scorer(task_dir)
