from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from secrets import token_hex
from typing import Any

from .redaction import redact_text
from .registry import load_task, repo_root_from
from .run_records import load_agent_config, load_task_version
from .run_validity import build_invalid_score_record, load_run_validity
from .scoring import score_task, write_score

RUN_STATUSES = {"passed", "failed", "timeout", "error", "invalid", "environment_error"}
TRACE_SNIPPET_CHARS = 2000
AGENT_VISIBLE_TASK_FILES = ("prompt.md", "task.json")
SCORER_ONLY_FILENAMES = {
    "check_config.json",
}
SCORER_ONLY_PATTERNS = (
    "answer_key",
    "hidden_label",
    "private",
    "canary",
    "scorer_config",
    "expected",
    "rubric_private",
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def command_hash(agent_cmd: str) -> str:
    return sha256(agent_cmd.encode("utf-8")).hexdigest()


def safe_slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value)


def unique_run_token() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}_{token_hex(4)}"


def safe_snippet(text: str | None, limit: int = TRACE_SNIPPET_CHARS) -> str:
    if not text:
        return ""
    return redact_text(text[:limit])


def is_agent_visible_path(path: Path) -> bool:
    if path.name.lower() in SCORER_ONLY_FILENAMES:
        return False
    lowered = path.as_posix().lower()
    return not any(pattern in lowered for pattern in SCORER_ONLY_PATTERNS)


def copy_public_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_trace_event(
    trace_path: Path,
    *,
    run_id: str,
    event_type: str,
    actor: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "ts": utc_now(),
        "run_id": run_id,
        "event_type": event_type,
        "actor": actor,
        "metadata": metadata or {},
    }
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def create_task_packet(
    *,
    root: Path,
    task_id: str,
    case_id: str,
    task_dir: Path,
    fixture_dir: Path,
    packet_dir: Path,
) -> dict[str, Any]:
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True)

    included: list[str] = []
    excluded_count = 0

    for filename in AGENT_VISIBLE_TASK_FILES:
        source = task_dir / filename
        if not source.exists():
            continue
        destination = packet_dir / filename
        copy_public_file(source, destination)
        included.append(destination.relative_to(packet_dir).as_posix())

    for source in sorted(fixture_dir.rglob("*")):
        if not source.is_file() or source.is_symlink():
            continue
        rel_fixture_path = source.relative_to(fixture_dir)
        if not is_agent_visible_path(rel_fixture_path):
            excluded_count += 1
            continue
        destination = packet_dir / "fixture" / rel_fixture_path
        copy_public_file(source, destination)
        included.append(destination.relative_to(packet_dir).as_posix())

    prompt_source = task_dir / "prompt.md"
    spec_source = fixture_dir / "spec.md"
    prompt_parts = []
    if prompt_source.exists():
        prompt_parts.append(prompt_source.read_text(encoding="utf-8"))
    if spec_source.exists() and is_agent_visible_path(Path("spec.md")):
        prompt_parts.extend(["", "## Case Spec", "", spec_source.read_text(encoding="utf-8")])
    task_prompt = "\n".join(prompt_parts).strip() + "\n"
    (packet_dir / "task_prompt.md").write_text(task_prompt, encoding="utf-8")
    included.append("task_prompt.md")

    readme = (
        "# Agent Bench Task Packet\n\n"
        "This directory contains only agent-visible task instructions and public fixture inputs.\n"
        "Write final artifacts to the path in `AGENT_BENCH_ARTIFACTS_DIR`.\n\n"
        "Scorer-only files such as `check_config.json`, hidden labels, answer keys, private scorer "
        "configs, canaries, and expected values are intentionally excluded.\n"
    )
    (packet_dir / "README.md").write_text(readme, encoding="utf-8")
    included.append("README.md")

    manifest = {
        "task_id": task_id,
        "case_id": case_id,
        "source_fixture": (fixture_dir.relative_to(root)).as_posix(),
        "included_files": sorted(set(included)),
        "excluded_file_count": excluded_count,
        "excluded_reason": "scorer_or_private_visibility_boundary",
        "visibility": "agent",
        "scorer_only_files_excluded": True,
    }
    write_json(packet_dir / "manifest.json", manifest)
    return manifest


def default_out_dir(root: Path, agent_config_id: str, task_id: str, case_id: str, run_id: str) -> Path:
    return root / "runs" / "manual" / safe_slug(agent_config_id) / f"{task_id}_{case_id}_{run_id}"


def build_run_id(agent_config_id: str, task_id: str, case_id: str) -> str:
    return safe_slug(f"{agent_config_id}_{task_id}_{case_id}_{unique_run_token()}")


def run_agent_task(
    task_id: str,
    case_id: str,
    agent_cmd: str,
    agent_config_path: Path | None,
    out_dir: Path | None = None,
    timeout_seconds: int = 600,
    root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root_from(root)
    task_dir = root / "tasks" / task_id
    fixture_dir = root / "fixtures" / "public" / task_id / case_id
    if not task_dir.is_dir():
        raise FileNotFoundError(f"Unknown task: {task_id}")
    if not fixture_dir.is_dir():
        raise FileNotFoundError(f"Missing public fixture for {task_id}/{case_id}: {fixture_dir}")

    task = load_task(task_dir)
    agent_config_id, agent_config_hash = load_agent_config(agent_config_path)
    run_id = build_run_id(agent_config_id, task_id, case_id)
    resolved_out_dir = out_dir.resolve() if out_dir else default_out_dir(
        root, agent_config_id, task_id, case_id, run_id
    )
    resolved_out_dir.mkdir(parents=True, exist_ok=True)

    task_packet_dir = resolved_out_dir / "task_packet"
    artifacts_dir = resolved_out_dir / "artifacts"
    score_path = resolved_out_dir / "score.json"
    run_path = resolved_out_dir / "run.json"
    trace_path = resolved_out_dir / "trace.jsonl"
    diagnostics_path = resolved_out_dir / "diagnostics.json"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    if trace_path.exists():
        trace_path.unlink()
    if diagnostics_path.exists():
        diagnostics_path.unlink()

    started_at = utc_now()
    append_trace_event(trace_path, run_id=run_id, event_type="run_started", actor="runner")
    manifest = create_task_packet(
        root=root,
        task_id=task_id,
        case_id=case_id,
        task_dir=task_dir,
        fixture_dir=fixture_dir,
        packet_dir=task_packet_dir,
    )
    append_trace_event(
        trace_path,
        run_id=run_id,
        event_type="task_packet_created",
        actor="runner",
        metadata={"included_files": len(manifest["included_files"])},
    )

    env = os.environ.copy()
    env.update(
        {
            "AGENT_BENCH_TASK_ID": task_id,
            "AGENT_BENCH_CASE_ID": case_id,
            "AGENT_BENCH_RUN_ID": run_id,
            "AGENT_BENCH_TASK_PACKET": str(task_packet_dir),
            "AGENT_BENCH_ARTIFACTS_DIR": str(artifacts_dir),
            "AGENT_BENCH_AGENT_CONFIG": str(agent_config_path or ""),
            "AGENT_BENCH_DIAGNOSTICS_FILE": str(diagnostics_path),
        }
    )

    returncode: int | None = None
    stdout_snippet = ""
    stderr_snippet = ""
    status = "failed"
    append_trace_event(
        trace_path,
        run_id=run_id,
        event_type="agent_command_started",
        actor="agent",
        metadata={"agent_cmd_hash": command_hash(agent_cmd)},
    )
    try:
        completed = subprocess.run(
            agent_cmd,
            shell=True,
            cwd=root,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = completed.returncode
        stdout_snippet = safe_snippet(completed.stdout)
        stderr_snippet = safe_snippet(completed.stderr)
        append_trace_event(
            trace_path,
            run_id=run_id,
            event_type="agent_command_completed",
            actor="agent",
            metadata={
                "returncode": returncode,
                "stdout_snippet": stdout_snippet,
                "stderr_snippet": stderr_snippet,
            },
        )
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        stdout = (
            exc.stdout.decode("utf-8", errors="replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout
        )
        stderr = (
            exc.stderr.decode("utf-8", errors="replace")
            if isinstance(exc.stderr, bytes)
            else exc.stderr
        )
        stdout_snippet = safe_snippet(stdout)
        stderr_snippet = safe_snippet(stderr)
        append_trace_event(
            trace_path,
            run_id=run_id,
            event_type="agent_command_timeout",
            actor="agent",
            metadata={
                "timeout_seconds": timeout_seconds,
                "stdout_snippet": stdout_snippet,
                "stderr_snippet": stderr_snippet,
            },
        )

    run_validity = load_run_validity(diagnostics_path)
    invalid_run = run_validity.get("valid") is False
    if invalid_run:
        append_trace_event(
            trace_path,
            run_id=run_id,
            event_type="run_invalidated",
            actor="runner",
            metadata={
                "category": run_validity.get("category"),
                "diagnostic_code": run_validity.get("diagnostic_code"),
                "reason": run_validity.get("reason"),
                "environment_ref": run_validity.get("environment_ref"),
            },
        )
        score = build_invalid_score_record(
            task_dir=task_dir,
            artifacts_dir=artifacts_dir,
            task_id=task_id,
            case_id=case_id,
            agent_config_path=agent_config_path,
            run_id=run_id,
            run_validity=run_validity,
        )
    else:
        append_trace_event(trace_path, run_id=run_id, event_type="scorer_started", actor="scorer")
        try:
            score = score_task(
                root=root,
                task_id=task_id,
                case_id=case_id,
                artifacts_dir=artifacts_dir,
                agent_config_path=agent_config_path,
                run_id=run_id,
            )
        except Exception as exc:  # noqa: BLE001 - runner must preserve local failure records.
            score = {
                "run_id": run_id,
                "task_id": task_id,
                "case_id": case_id,
                "task_version": load_task_version(task_dir),
                "scorer_version": "error",
                "agent_config_id": agent_config_id,
                "agent_config_hash": agent_config_hash,
                "success": False,
                "score": 0.0,
                "pass_threshold": 0.8,
                "components": {},
                "policy_violations": [],
                "errors": [redact_text(str(exc))],
                "artifact_hashes": {},
                "metadata": {
                    "latency_seconds": None,
                    "cost_usd": None,
                    "tool_calls": None,
                    "model_calls": None,
                    "notes": None,
                },
            }
        if run_validity.get("diagnostic_code"):
            score["run_validity"] = run_validity
    write_score(score, score_path)
    if not invalid_run:
        append_trace_event(
            trace_path,
            run_id=run_id,
            event_type="scorer_completed",
            actor="scorer",
            metadata={"score": score.get("score"), "success": score.get("success")},
        )

    if invalid_run:
        status = "environment_error"
    elif status != "timeout":
        status = "passed" if returncode == 0 and score.get("success") else "failed"
    completed_at = utc_now()
    run_record = {
        "run_id": run_id,
        "task_id": task_id,
        "case_id": case_id,
        "task_version": load_task_version(task_dir),
        "task_name": task.get("name"),
        "agent_config_id": agent_config_id,
        "agent_config_hash": agent_config_hash,
        "agent_cmd_hash": command_hash(agent_cmd),
        "started_at": started_at,
        "completed_at": completed_at,
        "status": status,
        "success": bool(score.get("success")) and status == "passed",
        "score": score.get("score"),
        "timeout_seconds": timeout_seconds,
        "paths": {
            "task_packet": str(task_packet_dir),
            "artifacts": str(artifacts_dir),
            "score": str(score_path),
            "trace": str(trace_path),
        },
        "command": {
            "returncode": returncode,
            "agent_cmd_redacted": redact_text(agent_cmd),
            "stdout_snippet": stdout_snippet,
            "stderr_snippet": stderr_snippet,
        },
    }
    if invalid_run:
        run_record["validity_category"] = run_validity.get("category")
    if run_validity.get("diagnostic_code"):
        run_record["validity_diagnostic_code"] = run_validity.get("diagnostic_code")
    write_json(run_path, run_record)
    append_trace_event(
        trace_path,
        run_id=run_id,
        event_type="run_completed",
        actor="runner",
        metadata={"status": status, "score": score.get("score"), "success": run_record["success"]},
    )
    return run_record
