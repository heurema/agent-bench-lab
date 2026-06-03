from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .redaction import redact_text
from .run_records import (
    DEFAULT_PASS_THRESHOLD,
    artifact_hashes,
    load_agent_config,
    load_task_version,
)

VALIDITY_CATEGORIES = {"provider_error", "environment_error", "harness_error"}
REASON_CHARS = 1000
ENVIRONMENT_REF_CHARS = 300


def valid_run_validity() -> dict[str, Any]:
    return {"valid": True}


def _safe_text(value: Any, limit: int) -> str:
    text = "" if value is None else str(value)
    return redact_text(text[:limit])


def invalid_run_validity(
    *,
    category: str,
    reason: str,
    environment_ref: str | None = None,
) -> dict[str, Any]:
    normalized_category = category if category in VALIDITY_CATEGORIES else "harness_error"
    result: dict[str, Any] = {
        "valid": False,
        "category": normalized_category,
        "reason": _safe_text(reason, REASON_CHARS) or "run invalidated by diagnostics",
    }
    if environment_ref:
        result["environment_ref"] = _safe_text(environment_ref, ENVIRONMENT_REF_CHARS)
    return result


def load_run_validity(diagnostics_path: Path) -> dict[str, Any]:
    if not diagnostics_path.exists():
        return valid_run_validity()
    try:
        data = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return invalid_run_validity(
            category="harness_error",
            reason="invalid diagnostics JSON",
        )
    if not isinstance(data, dict):
        return invalid_run_validity(
            category="harness_error",
            reason="diagnostics JSON must be an object",
        )
    if data.get("valid") is not False:
        return valid_run_validity()
    category = str(data.get("category") or "harness_error")
    reason = str(data.get("reason") or f"{category} reported by wrapper")
    environment_ref = data.get("environment_ref")
    return invalid_run_validity(
        category=category,
        reason=reason,
        environment_ref=str(environment_ref) if environment_ref is not None else None,
    )


def build_invalid_score_record(
    *,
    task_dir: Path,
    artifacts_dir: Path,
    task_id: str,
    case_id: str,
    agent_config_path: Path | None,
    run_id: str,
    run_validity: dict[str, Any],
) -> dict[str, Any]:
    agent_config_id, agent_config_hash = load_agent_config(agent_config_path)
    reason = str(run_validity.get("reason") or "run invalidated")
    return {
        "run_id": run_id,
        "task_id": task_id,
        "case_id": case_id,
        "task_version": load_task_version(task_dir),
        "scorer_version": "skipped:run_invalid",
        "agent_config_id": agent_config_id,
        "agent_config_hash": agent_config_hash,
        "success": False,
        "score": None,
        "pass_threshold": DEFAULT_PASS_THRESHOLD,
        "components": {},
        "policy_violations": [],
        "errors": [reason],
        "artifact_hashes": artifact_hashes(artifacts_dir),
        "metadata": {
            "latency_seconds": None,
            "cost_usd": None,
            "tool_calls": None,
            "model_calls": None,
            "notes": None,
        },
        "run_validity": run_validity,
    }
