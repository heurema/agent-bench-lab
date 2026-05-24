import json
from pathlib import Path

from agent_bench_lab.compare import compare_score_dirs


def write_score(root: Path, run_name: str, task_id: str, score: float, success: bool) -> None:
    output = root / run_name / f"{task_id}_case_001" / "score.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "case_id": "case_001",
                "score": score,
                "success": success,
                "policy_violations": [],
            }
        ),
        encoding="utf-8",
    )


def test_compare_detects_improvement_and_regression(tmp_path):
    write_score(tmp_path, "baseline", "IF-01", 0.70, False)
    write_score(tmp_path, "candidate", "IF-01", 0.90, True)
    write_score(tmp_path, "baseline", "DATA-01", 1.00, True)
    write_score(tmp_path, "candidate", "DATA-01", 0.75, False)

    result = compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate")

    assert result["total_tasks_compared"] == 2
    assert [row["task_id"] for row in result["improvements"]] == ["IF-01"]
    assert [row["task_id"] for row in result["regressions"]] == ["DATA-01"]


def test_compare_handles_missing_scores(tmp_path):
    write_score(tmp_path, "baseline", "IF-01", 1.00, True)

    result = compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate")

    assert result["total_tasks_compared"] == 0
    assert result["missing_scores"][0]["task_id"] == "IF-01"
    assert result["missing_scores"][0]["status"] == "missing_candidate"
