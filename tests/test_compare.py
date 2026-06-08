import json
from pathlib import Path

from agent_bench_lab.cli import main as cli_main
from agent_bench_lab.compare import compare_score_dirs
from agent_bench_lab.compare import render_markdown_report


def write_score(
    root: Path,
    run_name: str,
    task_id: str,
    score: float | None,
    success: bool,
    run_validity: dict | None = None,
) -> None:
    output = root / run_name / f"{task_id}_case_001" / "score.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "task_id": task_id,
        "case_id": "case_001",
        "score": score,
        "success": success,
        "policy_violations": [],
    }
    if run_validity is not None:
        record["run_validity"] = run_validity
    output.write_text(json.dumps(record), encoding="utf-8")


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


def test_compare_excludes_invalid_runs_from_score_averages(tmp_path):
    write_score(tmp_path, "baseline", "IF-01", 0.80, True)
    write_score(
        tmp_path,
        "candidate",
        "IF-01",
        None,
        False,
        {
            "valid": False,
            "category": "provider_error",
            "diagnostic_code": "provider_routing_failure",
            "reason": "model endpoint returned 404 repeatedly",
        },
    )
    write_score(tmp_path, "baseline", "DATA-01", 0.50, False)
    write_score(tmp_path, "candidate", "DATA-01", 0.70, True)

    result = compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate")
    report = render_markdown_report(result)

    assert result["total_tasks_compared"] == 1
    assert result["baseline_average_score"] == 0.50
    assert result["candidate_average_score"] == 0.70
    assert [row["task_id"] for row in result["improvements"]] == ["DATA-01"]
    assert result["invalid_runs"] == [
        {
            "side": "candidate",
            "task_id": "IF-01",
            "case_id": "case_001",
            "category": "provider_error",
            "diagnostic_code": "provider_routing_failure",
            "reason": "model endpoint returned 404 repeatedly",
        }
    ]
    assert "## Run Validity" in report
    assert "candidate IF-01/case_001: provider_error/provider_routing_failure" in report


def test_cli_compare_only_fails_on_invalid_when_flag_is_set(tmp_path):
    write_score(tmp_path, "baseline", "IF-01", 0.80, True)
    write_score(
        tmp_path,
        "candidate",
        "IF-01",
        None,
        False,
        {"valid": False, "category": "provider_error", "reason": "provider failed"},
    )
    report_path = tmp_path / "report.md"

    default_exit = cli_main(
        [
            "compare",
            "--baseline",
            str(tmp_path / "baseline"),
            "--candidate",
            str(tmp_path / "candidate"),
            "--out",
            str(report_path),
        ]
    )
    strict_exit = cli_main(
        [
            "compare",
            "--baseline",
            str(tmp_path / "baseline"),
            "--candidate",
            str(tmp_path / "candidate"),
            "--out",
            str(report_path),
            "--fail-on-invalid",
        ]
    )

    assert default_exit == 0
    assert strict_exit == 1
    assert "## Run Validity" in report_path.read_text(encoding="utf-8")
