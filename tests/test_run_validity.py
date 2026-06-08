from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_bench_lab.run_validity import load_run_validity


def write_diagnostics(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("diagnostic_code", "expected_category"),
    [
        ("provider_routing_failure", "provider_error"),
        ("final_submit_not_executed", "harness_error"),
        ("verifier_infrastructure_failure", "environment_error"),
    ],
)
def test_load_run_validity_preserves_stable_invalid_diagnostic_codes(
    tmp_path, diagnostic_code, expected_category
):
    diagnostics_path = write_diagnostics(
        tmp_path / "diagnostics.json",
        {
            "valid": False,
            "diagnostic_code": diagnostic_code,
            "reason": "public-safe diagnostic reason",
        },
    )

    run_validity = load_run_validity(diagnostics_path)

    assert run_validity == {
        "valid": False,
        "category": expected_category,
        "diagnostic_code": diagnostic_code,
        "reason": "public-safe diagnostic reason",
    }


def test_load_run_validity_accepts_cost_accounting_drift_as_valid_annotation(tmp_path):
    diagnostics_path = write_diagnostics(
        tmp_path / "diagnostics.json",
        {
            "valid": True,
            "diagnostic_code": "cost_accounting_drift",
            "reason": "cache pricing is unavailable for cost comparison",
            "environment_ref": "provider-pricing-snapshot-v1",
        },
    )

    run_validity = load_run_validity(diagnostics_path)

    assert run_validity == {
        "valid": True,
        "category": "provider_error",
        "diagnostic_code": "cost_accounting_drift",
        "reason": "cache pricing is unavailable for cost comparison",
        "environment_ref": "provider-pricing-snapshot-v1",
    }
