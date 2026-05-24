from pathlib import Path

import pytest

from agent_bench_lab.run_records import load_agent_config
from agent_bench_lab.scoring import load_scorer, score_task

REQUIRED_SCORE_FIELDS = {
    "run_id",
    "task_id",
    "case_id",
    "task_version",
    "scorer_version",
    "agent_config_id",
    "agent_config_hash",
    "success",
    "score",
    "pass_threshold",
    "components",
    "policy_violations",
    "errors",
    "artifact_hashes",
    "metadata",
}


def test_sample_if01_score(tmp_path):
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "artifact.md").write_text("# Public Launch Note\n- This uses versioned tasks.\n- This uses repeatable scoring.\n- This uses public templates.\n", encoding="utf-8")
    result = score_task(root, "IF-01", "case_001", artifact_dir)
    assert result["success"]
    assert REQUIRED_SCORE_FIELDS.issubset(result)


def test_sample_data01_score(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    metrics = {
        "qualified_event_count": 4,
        "unique_customer_count": 4,
        "total_revenue_usd": 820.5,
        "top_region_by_revenue": "NA",
        "revenue_by_region": {
            "EU": 340.0,
            "NA": 480.5,
        },
        "top_category_by_revenue": "subscription",
    }
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (artifact_dir / "report.md").write_text(
        "# DATA-01 Case 001 Memo\n"
        "## Summary\n"
        "- Qualified events: 4\n"
        "- Total revenue: 820.50\n"
        "- Top region: NA\n"
        "- Top category: subscription\n"
        "## Method\n"
        "- Applied the public fixture rules.\n"
        "## Caveats\n"
        "- Public smoke fixture only.\n",
        encoding="utf-8",
    )
    (artifact_dir / "chart_spec.json").write_text(
        json.dumps(
            {
                "title": "Case 001 Revenue by Region",
                "x_axis": "region",
                "y_axis": "revenue_usd",
                "series": [
                    {
                        "name": "revenue_usd",
                        "points": [
                            {"label": "NA", "value": 480.5},
                            {"label": "EU", "value": 340.0},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = score_task(root, "DATA-01", "case_001", artifact_dir)
    assert result["success"]


def test_scorer_interface_is_enforced(tmp_path):
    task_dir = tmp_path / "BAD-01"
    task_dir.mkdir()
    (task_dir / "scorer.py").write_text("def score(task_dir):\n    return {}\n", encoding="utf-8")

    with pytest.raises(TypeError, match="score signature"):
        load_scorer(task_dir)


def test_agent_config_hash_is_stable():
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs" / "agents" / "baseline.json"

    first_id, first_hash = load_agent_config(config_path)
    second_id, second_hash = load_agent_config(config_path)

    assert first_id == "baseline"
    assert first_hash == second_hash
