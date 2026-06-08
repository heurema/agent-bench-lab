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
DIAGNOSTIC_CODE_RULES = {
    "provider_routing_failure": {
        "category": "provider_error",
        "invalidates_quality": True,
    },
    "cost_accounting_drift": {
        "category": "provider_error",
        "invalidates_quality": False,
    },
    "final_submit_not_executed": {
        "category": "harness_error",
        "invalidates_quality": True,
    },
    "verifier_infrastructure_failure": {
        "category": "environment_error",
        "invalidates_quality": True,
    },
}
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
    diagnostic_code: str | None = None,
) -> dict[str, Any]:
    normalized_code = diagnostic_code if diagnostic_code in DIAGNOSTIC_CODE_RULES else None
    normalized_category = _category_for(category, normalized_code)
    result: dict[str, Any] = {
        "valid": False,
        "category": normalized_category,
        "reason": _safe_text(reason, REASON_CHARS) or "run invalidated by diagnostics",
    }
    if normalized_code:
        result["diagnostic_code"] = normalized_code
    if environment_ref:
        result["environment_ref"] = _safe_text(environment_ref, ENVIRONMENT_REF_CHARS)
    return result


def _category_for(category: str | None, diagnostic_code: str | None) -> str:
    if category in VALIDITY_CATEGORIES:
        return str(category)
    if diagnostic_code:
        return str(DIAGNOSTIC_CODE_RULES[diagnostic_code]["category"])
    return "harness_error"


def _diagnostic_code(data: dict[str, Any]) -> str | None:
    value = data.get("diagnostic_code")
    if not isinstance(value, str):
        return None
    return value if value in DIAGNOSTIC_CODE_RULES else None


def _diagnostic_invalidates_quality(diagnostic_code: str | None) -> bool:
    if not diagnostic_code:
        return False
    return bool(DIAGNOSTIC_CODE_RULES[diagnostic_code]["invalidates_quality"])


def diagnostic_run_validity(
    *,
    category: str | None,
    diagnostic_code: str,
    reason: str,
    environment_ref: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "valid": True,
        "category": _category_for(category, diagnostic_code),
        "diagnostic_code": diagnostic_code,
        "reason": _safe_text(reason, REASON_CHARS) or f"{diagnostic_code} reported by wrapper",
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
    diagnostic_code = _diagnostic_code(data)
    invalidates_quality = data.get("valid") is False or _diagnostic_invalidates_quality(
        diagnostic_code
    )
    if not invalidates_quality and not diagnostic_code:
        return valid_run_validity()
    category = str(data.get("category") or "")
    reason = str(
        data.get("reason")
        or (
            f"{diagnostic_code} reported by wrapper"
            if diagnostic_code
            else f"{_category_for(category, None)} reported by wrapper"
        )
    )
    environment_ref = data.get("environment_ref")
    normalized_environment_ref = str(environment_ref) if environment_ref is not None else None
    if invalidates_quality:
        return invalid_run_validity(
            category=category,
            reason=reason,
            environment_ref=normalized_environment_ref,
            diagnostic_code=diagnostic_code,
        )
    return diagnostic_run_validity(
        category=category,
        diagnostic_code=str(diagnostic_code),
        reason=reason,
        environment_ref=normalized_environment_ref,
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
