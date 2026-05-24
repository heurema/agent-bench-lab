from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_AGENT_CONFIG_ID = "unspecified"
DEFAULT_AGENT_CONFIG_HASH = "unspecified"
DEFAULT_PASS_THRESHOLD = 0.8


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_hash(data: Any) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def load_agent_config(path: Path | None) -> tuple[str, str]:
    if path is None:
        return DEFAULT_AGENT_CONFIG_ID, DEFAULT_AGENT_CONFIG_HASH
    if not path.exists():
        raise FileNotFoundError(f"Missing agent config: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return path.stem, file_sha256(path)
    agent_config_id = data.get("agent_config_id") or data.get("id") or path.stem
    return str(agent_config_id), stable_json_hash(data)


def artifact_hashes(artifacts_dir: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(artifacts_dir.rglob("*")):
        if path.is_file():
            hashes[path.relative_to(artifacts_dir).as_posix()] = file_sha256(path)
    return hashes


def checks_to_components(checks: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(checks, list):
        return {}
    components = {}
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            continue
        name = str(check.get("name") or f"check_{index + 1}")
        components[name] = {
            "passed": bool(check.get("passed", False)),
            "points": check.get("points"),
            "max_points": check.get("max_points"),
            "detail": check.get("detail", ""),
        }
    return components


def normalize_policy_violations(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, int):
        if value <= 0:
            return []
        return [f"policy violation count: {value}"]
    if isinstance(value, str):
        return [value] if value else []
    return [str(value)]


def load_task_version(task_dir: Path) -> str:
    task_file = task_dir / "task.json"
    if not task_file.exists():
        return "unknown"
    task = json.loads(task_file.read_text(encoding="utf-8"))
    return str(task.get("version", "unknown"))


def scorer_version(task_dir: Path) -> str:
    scorer_path = task_dir / "scorer.py"
    if not scorer_path.exists():
        return "missing"
    return f"sha256:{file_sha256(scorer_path)[:12]}"


def build_score_record(
    *,
    raw_result: dict[str, Any],
    task_dir: Path,
    artifacts_dir: Path,
    task_id: str,
    case_id: str,
    agent_config_path: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    agent_config_id, agent_config_hash = load_agent_config(agent_config_path)
    resolved_run_id = run_id or f"{agent_config_id}_{task_id}_{case_id}"
    components = raw_result.get("components")
    if not isinstance(components, dict):
        components = checks_to_components(raw_result.get("checks"))
    errors = raw_result.get("errors", [])
    if isinstance(errors, str):
        errors = [errors]
    if not isinstance(errors, list):
        errors = [str(errors)]

    record = {
        "run_id": resolved_run_id,
        "task_id": task_id,
        "case_id": case_id,
        "task_version": load_task_version(task_dir),
        "scorer_version": scorer_version(task_dir),
        "agent_config_id": agent_config_id,
        "agent_config_hash": agent_config_hash,
        "success": bool(raw_result.get("success", False)),
        "score": float(raw_result.get("score", 0.0)),
        "pass_threshold": float(raw_result.get("pass_threshold", DEFAULT_PASS_THRESHOLD)),
        "components": components,
        "policy_violations": normalize_policy_violations(raw_result.get("policy_violations")),
        "errors": [str(error) for error in errors],
        "artifact_hashes": artifact_hashes(artifacts_dir),
        "metadata": {
            "latency_seconds": raw_result.get("latency_seconds"),
            "cost_usd": raw_result.get("cost_usd"),
            "tool_calls": raw_result.get("tool_calls"),
            "model_calls": raw_result.get("model_calls"),
            "notes": raw_result.get("notes"),
        },
    }
    if "checks" in raw_result:
        record["checks"] = raw_result["checks"]
    return record
