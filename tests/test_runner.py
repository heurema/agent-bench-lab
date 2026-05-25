from __future__ import annotations

import json
import sys
from pathlib import Path

from agent_bench_lab.cli import main as cli_main
from agent_bench_lab.runner import create_task_packet, run_agent_task


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def test_task_packet_excludes_check_config(tmp_path):
    out_dir = tmp_path / "packet_run"
    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} -c \"pass\"",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=30,
    )
    packet_dir = Path(run_record["paths"]["task_packet"])

    assert (packet_dir / "fixture" / "spec.md").exists()
    assert not (packet_dir / "fixture" / "check_config.json").exists()
    assert "check_config.json" not in (packet_dir / "manifest.json").read_text(encoding="utf-8")


def test_task_packet_excludes_denylisted_scorer_only_files(tmp_path):
    task_dir = tmp_path / "tasks" / "T-01"
    fixture_dir = tmp_path / "fixtures" / "public" / "T-01" / "case_001"
    packet_dir = tmp_path / "packet"
    task_dir.mkdir(parents=True)
    fixture_dir.mkdir(parents=True)
    (task_dir / "prompt.md").write_text("Prompt", encoding="utf-8")
    (task_dir / "task.json").write_text("{}", encoding="utf-8")
    (fixture_dir / "spec.md").write_text("Spec", encoding="utf-8")
    (fixture_dir / "answer_key.json").write_text("{}", encoding="utf-8")
    (fixture_dir / "hidden_label.txt").write_text("label", encoding="utf-8")
    (fixture_dir / "data.csv").write_text("id,value\n1,2\n", encoding="utf-8")

    manifest = create_task_packet(
        root=tmp_path,
        task_id="T-01",
        case_id="case_001",
        task_dir=task_dir,
        fixture_dir=fixture_dir,
        packet_dir=packet_dir,
    )

    assert (packet_dir / "fixture" / "data.csv").exists()
    assert not (packet_dir / "fixture" / "answer_key.json").exists()
    assert not (packet_dir / "fixture" / "hidden_label.txt").exists()
    assert manifest["excluded_file_count"] == 2


def test_runner_writes_run_trace_and_score_with_mock_agent(tmp_path):
    out_dir = tmp_path / "run"
    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} scripts/mock_agent_write_artifacts.py",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
    )

    assert run_record["status"] == "passed"
    assert (out_dir / "run.json").exists()
    assert (out_dir / "trace.jsonl").exists()
    assert (out_dir / "score.json").exists()
    assert (out_dir / "artifacts" / "artifact.md").exists()
    score = json.loads((out_dir / "score.json").read_text(encoding="utf-8"))
    assert score["success"]


def test_runner_handles_agent_command_timeout(tmp_path):
    out_dir = tmp_path / "timeout"
    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} -c \"import time; time.sleep(2)\"",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=1,
    )

    assert run_record["status"] == "timeout"
    assert (out_dir / "run.json").exists()
    assert (out_dir / "score.json").exists()
    assert "agent_command_timeout" in (out_dir / "trace.jsonl").read_text(encoding="utf-8")


def test_runner_handles_missing_artifacts_gracefully(tmp_path):
    out_dir = tmp_path / "missing_artifacts"
    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} -c \"print('no artifacts')\"",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=30,
    )

    assert run_record["status"] == "failed"
    score = json.loads((out_dir / "score.json").read_text(encoding="utf-8"))
    assert not score["success"]
    assert score["score"] < score["pass_threshold"]


def test_runner_redacts_unsafe_stdout_and_stderr(tmp_path):
    out_dir = tmp_path / "redacted"
    command = (
        f"{sys.executable} -c \"import sys; "
        "print('correct answer was x expected=y CANARY_123'); "
        "print('api_key=secret', file=sys.stderr)\""
    )
    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=command,
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=30,
    )
    trace_text = (out_dir / "trace.jsonl").read_text(encoding="utf-8")
    run_text = json.dumps(run_record)

    assert "[REDACTED]" in trace_text
    assert "CANARY_123" not in trace_text
    assert "api_key" not in trace_text
    assert "CANARY_123" not in run_text
    assert "api_key" not in run_text


def test_cli_agent_bench_run_works_with_mock_agent(tmp_path, capsys):
    out_dir = tmp_path / "cli_run"
    exit_code = cli_main(
        [
            "--root",
            str(root_dir()),
            "run",
            "--task",
            "IF-01",
            "--case",
            "case_001",
            "--agent-cmd",
            f"{sys.executable} scripts/mock_agent_write_artifacts.py",
            "--out",
            str(out_dir),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "passed"
    assert output["success"] is True
    assert (out_dir / "run.json").exists()
