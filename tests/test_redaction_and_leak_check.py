from __future__ import annotations

import importlib.util
from pathlib import Path

from agent_bench_lab.compare import compare_score_dirs, render_markdown_report, write_csv_report
from agent_bench_lab.redaction import REDACTED, is_public_safe_text, redact_obj, redact_text


def load_public_leak_check():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "public_leak_check.py"
    spec = importlib.util.spec_from_file_location("public_leak_check", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_redactor_removes_unsafe_strings():
    text = "correct answer was refund_escalation expected=refund_escalation CANARY_123"

    assert redact_text(text) == REDACTED
    assert redact_obj({"detail": text}) == {"detail": REDACTED}
    assert not is_public_safe_text(text)


def test_redactor_keeps_safe_feedback_readable():
    text = "numeric total is incorrect"

    assert redact_text(text) == text
    assert redact_obj({"detail": text}) == {"detail": text}
    assert is_public_safe_text(text)


def test_compare_reports_redact_unsafe_diagnostics(tmp_path):
    baseline_score = tmp_path / "baseline" / "IF-01_case_001" / "score.json"
    candidate_score = tmp_path / "candidate" / "IF-01_case_001" / "score.json"
    baseline_score.parent.mkdir(parents=True)
    candidate_score.parent.mkdir(parents=True)
    baseline_score.write_text(
        """
        {
          "task_id": "IF-01",
          "case_id": "case_001",
          "score": 0.8,
          "success": true,
          "policy_violations": []
        }
        """,
        encoding="utf-8",
    )
    candidate_score.write_text(
        """
        {
          "task_id": "IF-01",
          "case_id": "case_001",
          "score": 0.7,
          "success": false,
          "policy_violations": [
            "correct answer was refund_escalation expected=refund_escalation CANARY_123"
          ]
        }
        """,
        encoding="utf-8",
    )

    result = compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate")
    markdown = render_markdown_report(result)
    csv_path = tmp_path / "compare.csv"
    write_csv_report(result, csv_path)
    csv_text = csv_path.read_text(encoding="utf-8")

    assert REDACTED in markdown
    assert "refund_escalation" not in markdown
    assert "CANARY_123" not in markdown
    assert "expected=" not in markdown
    assert "refund_escalation" not in csv_text
    assert "CANARY_123" not in csv_text


def test_public_leak_check_fails_tracked_like_denied_path(tmp_path):
    public_leak_check = load_public_leak_check()

    findings = public_leak_check.scan_paths(
        tmp_path,
        ["fixtures/private/case_001/answer_key.json"],
    )

    assert findings
    assert "fixtures/private/case_001/answer_key.json" in findings[0]


def test_public_leak_check_fallback_ignores_generated_local_paths(tmp_path):
    public_leak_check = load_public_leak_check()
    for rel_path in [
        "runs/baseline/score.json",
        "examples/artifacts/IF-01/case_001/artifact.md",
        "reports/generated/compare.md",
    ]:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated local file", encoding="utf-8")

    assert public_leak_check.scan(tmp_path) == []


def test_public_leak_check_fallback_flags_private_source_tree(tmp_path):
    public_leak_check = load_public_leak_check()
    path = tmp_path / "fixtures" / "private" / "case_001" / "labels.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")

    findings = public_leak_check.scan(tmp_path)

    assert findings
    assert "fixtures/private/case_001/labels.json" in findings[0]


def test_public_leak_check_passes_current_repository_tree():
    public_leak_check = load_public_leak_check()
    root = Path(__file__).resolve().parents[1]

    assert public_leak_check.scan(root) == []
