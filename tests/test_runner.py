from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_bench_lab.cli import main as cli_main
from agent_bench_lab.runner import (
    TRACE_SNIPPET_CHARS,
    build_run_id,
    create_task_packet,
    run_agent_task,
)


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> dict:
    return load_json(root_dir() / "schemas" / name)


def load_trace_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def assert_valid(schema_name: str, data: dict) -> None:
    validator = Draft202012Validator(load_schema(schema_name))
    errors = sorted(validator.iter_errors(data), key=lambda item: tuple(item.absolute_path))
    assert errors == []


def assert_no_scorer_only_packet_files(packet_dir: Path) -> None:
    packet_files = [path.relative_to(packet_dir).as_posix() for path in packet_dir.rglob("*") if path.is_file()]
    assert "fixture/check_config.json" not in packet_files
    assert not any("answer_key" in path.lower() for path in packet_files)
    assert not any("hidden_label" in path.lower() for path in packet_files)
    assert not any("scorer_config" in path.lower() for path in packet_files)
    assert not any("expected" in path.lower() for path in packet_files)


def assert_runner_contract_outputs(out_dir: Path) -> None:
    assert_valid("run.schema.json", load_json(out_dir / "run.json"))
    assert_valid("score.schema.json", load_json(out_dir / "score.json"))
    for event in load_trace_events(out_dir / "trace.jsonl"):
        assert_valid("trace_event.schema.json", event)


def test_golden_runner_contract_fixtures_match_schemas():
    golden_dir = root_dir() / "tests" / "golden" / "runner"

    assert_valid("run.schema.json", load_json(golden_dir / "run.json"))
    assert_valid("score.schema.json", load_json(golden_dir / "score.json"))
    for event in load_trace_events(golden_dir / "trace.jsonl"):
        assert_valid("trace_event.schema.json", event)


def test_build_run_id_is_unique_for_fast_repeated_runs():
    run_ids = [build_run_id("unspecified", "IF-01", "case_001") for _ in range(20)]

    assert len(set(run_ids)) == len(run_ids)


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
    assert_no_scorer_only_packet_files(packet_dir)


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
    assert_runner_contract_outputs(out_dir)


def test_if01_task_packet_includes_only_expected_safe_fixture_files(tmp_path):
    out_dir = tmp_path / "if01_packet"
    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} scripts/mock_agent_write_artifacts.py",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
    )
    packet_dir = Path(run_record["paths"]["task_packet"])
    artifacts_dir = Path(run_record["paths"]["artifacts"])

    assert (packet_dir / "prompt.md").exists()
    assert (packet_dir / "task.json").exists()
    assert (packet_dir / "task_prompt.md").exists()
    assert (packet_dir / "fixture" / "spec.md").exists()
    assert (artifacts_dir / "artifact.md").exists()
    assert artifacts_dir != packet_dir
    assert not str(artifacts_dir).startswith(str(packet_dir))
    assert_no_scorer_only_packet_files(packet_dir)
    assert json.loads((out_dir / "score.json").read_text(encoding="utf-8"))["success"]


def test_data01_task_packet_includes_safe_data_without_scorer_config(tmp_path):
    out_dir = tmp_path / "data01_packet"
    run_record = run_agent_task(
        root=root_dir(),
        task_id="DATA-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} scripts/mock_agent_write_artifacts.py",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=60,
    )
    packet_dir = Path(run_record["paths"]["task_packet"])
    artifacts_dir = Path(run_record["paths"]["artifacts"])

    assert (packet_dir / "fixture" / "spec.md").exists()
    assert (packet_dir / "fixture" / "data" / "events.csv").exists()
    assert (packet_dir / "fixture" / "data" / "customers.csv").exists()
    assert (packet_dir / "fixture" / "data" / "analytics.db").exists()
    assert not (packet_dir / "fixture" / "check_config.json").exists()
    assert (artifacts_dir / "metrics.json").exists()
    assert not (packet_dir / "metrics.json").exists()
    assert artifacts_dir != packet_dir
    assert_no_scorer_only_packet_files(packet_dir)
    assert json.loads((out_dir / "score.json").read_text(encoding="utf-8"))["success"]


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
    assert_runner_contract_outputs(out_dir)


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


def test_runner_bounds_and_redacts_command_output_snippets(tmp_path):
    out_dir = tmp_path / "bounded_redaction"
    unsafe_terms = [
        "answer_key",
        "hidden_label",
        "CANARY_123",
        "expected=value",
        "token",
        "secret",
    ]
    unsafe_payload = " ".join(unsafe_terms)
    command = (
        f"{sys.executable} -c \"import sys; "
        f"print('safe-prefix-' + 'x' * {TRACE_SNIPPET_CHARS + 200} + '{unsafe_payload}'); "
        f"print('{unsafe_payload}', file=sys.stderr)\""
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
    events = load_trace_events(out_dir / "trace.jsonl")
    completed_event = next(event for event in events if event["event_type"] == "agent_command_completed")
    stdout_snippet = completed_event["metadata"]["stdout_snippet"]
    stderr_snippet = completed_event["metadata"]["stderr_snippet"]
    run_text = json.dumps(run_record)
    trace_text = (out_dir / "trace.jsonl").read_text(encoding="utf-8")

    assert len(stdout_snippet) <= TRACE_SNIPPET_CHARS
    assert stderr_snippet == "[REDACTED]"
    for term in unsafe_terms:
        assert term not in trace_text
        assert term not in run_text
    assert_runner_contract_outputs(out_dir)


def test_runner_invalidates_provider_diagnostics_and_skips_scorer(tmp_path):
    out_dir = tmp_path / "provider_invalid"
    agent_path = tmp_path / "provider_invalid_agent.py"
    agent_path.write_text(
        """
import json
import os
from pathlib import Path

Path(os.environ["AGENT_BENCH_DIAGNOSTICS_FILE"]).write_text(
    json.dumps(
        {
            "valid": False,
            "category": "provider_error",
            "reason": "model endpoint returned 404 repeatedly",
            "environment_ref": "provider-snapshot-v1",
        }
    ),
    encoding="utf-8",
)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} {agent_path}",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=30,
    )
    score = load_json(out_dir / "score.json")
    events = load_trace_events(out_dir / "trace.jsonl")
    event_types = [event["event_type"] for event in events]

    assert run_record["status"] == "environment_error"
    assert run_record["success"] is False
    assert run_record["validity_category"] == "provider_error"
    assert score["score"] is None
    assert score["success"] is False
    assert score["run_validity"] == {
        "valid": False,
        "category": "provider_error",
        "reason": "model endpoint returned 404 repeatedly",
        "environment_ref": "provider-snapshot-v1",
    }
    assert "run_invalidated" in event_types
    assert "scorer_started" not in event_types
    assert "scorer_completed" not in event_types
    assert_runner_contract_outputs(out_dir)


def test_runner_reads_invalid_diagnostics_even_when_command_exits_nonzero(tmp_path):
    out_dir = tmp_path / "harness_invalid"
    agent_path = tmp_path / "harness_invalid_agent.py"
    agent_path.write_text(
        """
import json
import os
from pathlib import Path

Path(os.environ["AGENT_BENCH_DIAGNOSTICS_FILE"]).write_text(
    json.dumps(
        {
            "valid": False,
            "category": "harness_error",
            "reason": "wrapper failed before handing task to agent",
        }
    ),
    encoding="utf-8",
)
raise SystemExit(7)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} {agent_path}",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=30,
    )
    score = load_json(out_dir / "score.json")

    assert run_record["status"] == "environment_error"
    assert run_record["command"]["returncode"] == 7
    assert run_record["validity_category"] == "harness_error"
    assert score["run_validity"]["category"] == "harness_error"
    assert_runner_contract_outputs(out_dir)


def test_runner_preserves_valid_cost_diagnostic_without_invalidating_score(tmp_path):
    out_dir = tmp_path / "cost_diagnostic"
    agent_path = tmp_path / "cost_diagnostic_agent.py"
    agent_path.write_text(
        """
import json
import os
from pathlib import Path

artifacts = Path(os.environ["AGENT_BENCH_ARTIFACTS_DIR"])
artifacts.mkdir(parents=True, exist_ok=True)
(artifacts / "artifact.md").write_text(
    "# Public Launch Note\\n"
    "- versioned tasks\\n"
    "- repeatable scoring\\n"
    "- public templates\\n",
    encoding="utf-8",
)
Path(os.environ["AGENT_BENCH_DIAGNOSTICS_FILE"]).write_text(
    json.dumps(
        {
            "valid": True,
            "diagnostic_code": "cost_accounting_drift",
            "reason": "cache pricing is unavailable for cost comparison",
            "environment_ref": "provider-pricing-snapshot-v1",
        }
    ),
    encoding="utf-8",
)
""".strip()
        + "\n",
        encoding="utf-8",
    )

    run_record = run_agent_task(
        root=root_dir(),
        task_id="IF-01",
        case_id="case_001",
        agent_cmd=f"{sys.executable} {agent_path}",
        agent_config_path=None,
        out_dir=out_dir,
        timeout_seconds=30,
    )
    score = load_json(out_dir / "score.json")

    assert run_record["status"] == "passed"
    assert run_record["success"] is True
    assert run_record["validity_diagnostic_code"] == "cost_accounting_drift"
    assert score["success"] is True
    assert score["score"] == 1.0
    assert score["run_validity"] == {
        "valid": True,
        "category": "provider_error",
        "diagnostic_code": "cost_accounting_drift",
        "reason": "cache pricing is unavailable for cost comparison",
        "environment_ref": "provider-pricing-snapshot-v1",
    }
    assert_runner_contract_outputs(out_dir)


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
