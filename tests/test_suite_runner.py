from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from agent_bench_lab.cli import main as cli_main
from agent_bench_lab.compare import compare_score_dirs
from agent_bench_lab.suite_runner import build_suite_run_id, load_suite_config, run_agent_suite


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def write_suite(path: Path, task_ids: list[str]) -> Path:
    path.write_text(
        json.dumps(
            {
                "suite_id": "test-suite-v0",
                "version": "0.0.0",
                "description": "Temporary suite for runner tests.",
                "tasks": task_ids,
                "recommended_cases": ["case_001"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_scorer_only_packet_files(packet_dir: Path) -> None:
    packet_files = [path.relative_to(packet_dir).as_posix() for path in packet_dir.rglob("*") if path.is_file()]
    assert "fixture/check_config.json" not in packet_files
    assert not any("answer_key" in path.lower() for path in packet_files)
    assert not any("hidden_label" in path.lower() for path in packet_files)
    assert not any("scorer_config" in path.lower() for path in packet_files)
    assert not any("expected" in path.lower() for path in packet_files)


def write_conditional_agent(path: Path) -> Path:
    path.write_text(
        """
from pathlib import Path
import os
import sys

task_id = os.environ["AGENT_BENCH_TASK_ID"]
artifacts = Path(os.environ["AGENT_BENCH_ARTIFACTS_DIR"])
artifacts.mkdir(parents=True, exist_ok=True)

if task_id == "IF-01":
    (artifacts / "artifact.md").write_text(
        "# Public Launch Note\\n"
        "- versioned tasks\\n"
        "- repeatable scoring\\n"
        "- public templates\\n",
        encoding="utf-8",
    )
    raise SystemExit(0)

print("intentional failure for suite-runner test", file=sys.stderr)
raise SystemExit(3)
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def test_load_suite_config_by_name_and_path():
    root = root_dir()

    by_name = load_suite_config(root, "tools-local")
    by_path = load_suite_config(root, root / "configs" / "suites" / "tools-local.json")

    assert by_name["suite_id"] == "tools-local-v0"
    assert by_path["suite_id"] == "tools-local-v0"
    assert by_name["tasks"] == ["API-01"]


def test_build_suite_run_id_is_unique_for_fast_repeated_runs():
    suite_run_ids = [build_suite_run_id("unspecified", "core-v0") for _ in range(20)]

    assert len(set(suite_run_ids)) == len(suite_run_ids)


def test_run_agent_suite_creates_suite_run_and_task_outputs(tmp_path):
    suite_path = write_suite(tmp_path / "suite.json", ["IF-01", "DATA-01"])
    out_dir = tmp_path / "suite_run"

    suite_record = run_agent_suite(
        root=root_dir(),
        suite=suite_path,
        agent_cmd=f"{sys.executable} scripts/mock_agent_write_artifacts.py",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
    )

    assert suite_record["status"] == "passed"
    assert suite_record["total_tasks"] == 2
    assert suite_record["completed_tasks"] == 2
    assert suite_record["failed_tasks"] == 0
    assert suite_record["success_count"] == 2
    assert suite_record["average_score"] == 1.0
    assert (out_dir / "suite_run.json").exists()
    for task_id in ("IF-01", "DATA-01"):
        run_dir = out_dir / f"{task_id}_case_001"
        assert (run_dir / "run.json").exists()
        assert (run_dir / "trace.jsonl").exists()
        assert (run_dir / "score.json").exists()


def test_run_agent_suite_reuses_task_packet_visibility_boundary(tmp_path):
    suite_path = write_suite(tmp_path / "suite.json", ["DATA-01"])
    out_dir = tmp_path / "suite_run"

    suite_record = run_agent_suite(
        root=root_dir(),
        suite=suite_path,
        agent_cmd=f"{sys.executable} scripts/mock_agent_write_artifacts.py",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
    )
    task_run = suite_record["task_runs"][0]
    packet_dir = Path(task_run["path"]) / "task_packet"
    artifacts_dir = Path(task_run["path"]) / "artifacts"

    assert (packet_dir / "fixture" / "spec.md").exists()
    assert (packet_dir / "fixture" / "data" / "events.csv").exists()
    assert not (packet_dir / "fixture" / "check_config.json").exists()
    assert (artifacts_dir / "metrics.json").exists()
    assert artifacts_dir != packet_dir
    assert_no_scorer_only_packet_files(packet_dir)


def test_run_agent_suite_continues_after_task_failure_by_default(tmp_path):
    suite_path = write_suite(tmp_path / "suite.json", ["IF-01", "DATA-01"])
    agent_path = write_conditional_agent(tmp_path / "conditional_agent.py")
    out_dir = tmp_path / "suite_run"

    suite_record = run_agent_suite(
        root=root_dir(),
        suite=suite_path,
        agent_cmd=f"{sys.executable} {agent_path}",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
    )

    assert suite_record["status"] == "partial"
    assert suite_record["total_tasks"] == 2
    assert suite_record["completed_tasks"] == 2
    assert suite_record["success_count"] == 1
    assert suite_record["failed_tasks"] == 1
    assert [run["task_id"] for run in suite_record["task_runs"]] == ["IF-01", "DATA-01"]
    assert (out_dir / "DATA-01_case_001" / "score.json").exists()


def test_run_agent_suite_fail_fast_stops_after_first_failure(tmp_path):
    suite_path = write_suite(tmp_path / "suite.json", ["DATA-01", "IF-01"])
    agent_path = write_conditional_agent(tmp_path / "conditional_agent.py")
    out_dir = tmp_path / "suite_run"

    suite_record = run_agent_suite(
        root=root_dir(),
        suite=suite_path,
        agent_cmd=f"{sys.executable} {agent_path}",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
        fail_fast=True,
    )

    assert suite_record["status"] == "failed"
    assert suite_record["total_tasks"] == 2
    assert suite_record["completed_tasks"] == 1
    assert suite_record["failed_tasks"] == 1
    assert suite_record["stopped_early"] is True
    assert [run["task_id"] for run in suite_record["task_runs"]] == ["DATA-01"]
    assert not (out_dir / "IF-01_case_001").exists()


def test_cli_run_suite_works_and_compare_can_consume_scores(tmp_path, capsys):
    suite_path = write_suite(tmp_path / "suite.json", ["IF-01", "DATA-01"])
    out_dir = tmp_path / "suite_run"

    exit_code = cli_main(
        [
            "--root",
            str(root_dir()),
            "run-suite",
            "--suite",
            str(suite_path),
            "--agent-cmd",
            f"{sys.executable} scripts/mock_agent_write_artifacts.py",
            "--out",
            str(out_dir),
            "--timeout",
            "60",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    comparison = compare_score_dirs(out_dir, out_dir)

    assert exit_code == 0
    assert output["status"] == "passed"
    assert output["success_count"] == 2
    assert (out_dir / "suite_run.json").exists()
    assert comparison["total_tasks_compared"] == 2


def test_generated_run_paths_are_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "runs/manual/mock-core/suite_run.json"],
        cwd=root_dir(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
