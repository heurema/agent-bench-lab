from pathlib import Path

import pytest

from agent_bench_lab.run_records import load_agent_config
from agent_bench_lab.scoring import load_scorer, score_task

REQUIRED_SCORE_FIELDS = {
    "run_id",
    "task_id",
    "case_id",
    "task_version",
    "scorer_version",
    "agent_config_id",
    "agent_config_hash",
    "success",
    "score",
    "pass_threshold",
    "components",
    "policy_violations",
    "errors",
    "artifact_hashes",
    "metadata",
}


def test_sample_if01_score(tmp_path):
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "artifact.md").write_text("# Public Launch Note\n- This uses versioned tasks.\n- This uses repeatable scoring.\n- This uses public templates.\n", encoding="utf-8")
    result = score_task(root, "IF-01", "case_001", artifact_dir)
    assert result["success"]
    assert REQUIRED_SCORE_FIELDS.issubset(result)


def test_sample_data01_score(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    metrics = {
        "qualified_event_count": 4,
        "unique_customer_count": 4,
        "total_revenue_usd": 820.5,
        "top_region_by_revenue": "NA",
        "revenue_by_region": {
            "EU": 340.0,
            "NA": 480.5,
        },
        "top_category_by_revenue": "subscription",
    }
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (artifact_dir / "report.md").write_text(
        "# DATA-01 Case 001 Memo\n"
        "## Summary\n"
        "- Qualified events: 4\n"
        "- Total revenue: 820.50\n"
        "- Top region: NA\n"
        "- Top category: subscription\n"
        "## Method\n"
        "- Applied the public fixture rules.\n"
        "## Caveats\n"
        "- Public smoke fixture only.\n",
        encoding="utf-8",
    )
    (artifact_dir / "chart_spec.json").write_text(
        json.dumps(
            {
                "title": "Case 001 Revenue by Region",
                "x_axis": "region",
                "y_axis": "revenue_usd",
                "series": [
                    {
                        "name": "revenue_usd",
                        "points": [
                            {"label": "NA", "value": 480.5},
                            {"label": "EU", "value": 340.0},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = score_task(root, "DATA-01", "case_001", artifact_dir)
    assert result["success"]


def test_sample_doc01_score(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "answer.md").write_text(
        "# DOC-01 Case 001 Answer\n"
        "## Answer\n"
        "- email support.\n"
        "- two business days.\n"
        "- CSV.\n"
        "- within 14 days.\n"
        "- no paid data export.\n"
        "## Evidence\n"
        "- See citation artifacts.\n"
        "## Limits\n"
        "- Public smoke fixture only.\n",
        encoding="utf-8",
    )
    (artifact_dir / "citations.json").write_text(
        json.dumps(
            {
                "citations": [
                    {
                        "id": "c_support_target_1",
                        "doc_id": "product_policy",
                        "quote": "Northstar Basic includes email support with a target response within two business days.",
                    },
                    {
                        "id": "c_export_format_1",
                        "doc_id": "product_policy",
                        "quote": "Workspace admins can export account activity as CSV.",
                    },
                    {
                        "id": "c_refund_condition_1",
                        "doc_id": "product_policy",
                        "quote": "Refund requests within 14 days may be approved when no paid data export has been used.",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "claims.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "id": "support_target",
                        "text": "email support with a target response within two business days",
                        "supported": True,
                        "citation_ids": ["c_support_target_1"],
                    },
                    {
                        "id": "export_format",
                        "text": "export account activity as CSV",
                        "supported": True,
                        "citation_ids": ["c_export_format_1"],
                    },
                    {
                        "id": "refund_condition",
                        "text": "within 14 days may be approved when no paid data export has been used",
                        "supported": True,
                        "citation_ids": ["c_refund_condition_1"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    result = score_task(root, "DOC-01", "case_001", artifact_dir)
    assert result["success"]


def test_sample_sup01_score(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "triage.json").write_text(
        json.dumps(
            {
                "triage": [
                    {
                        "email_id": "email_001",
                        "category": "billing",
                        "priority": "normal",
                        "requires_reply": True,
                        "requires_escalation": False,
                        "reason_code": "duplicate_charge_review",
                    },
                    {
                        "email_id": "email_002",
                        "category": "informational",
                        "priority": "low",
                        "requires_reply": False,
                        "requires_escalation": False,
                        "reason_code": "informational_no_action",
                    },
                    {
                        "email_id": "email_003",
                        "category": "how_to",
                        "priority": "normal",
                        "requires_reply": True,
                        "requires_escalation": False,
                        "reason_code": "export_instructions",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "drafts.json").write_text(
        json.dumps(
            {
                "drafts": [
                    {
                        "email_id": "email_001",
                        "draft_subject": "Re: duplicate charge",
                        "draft_body": "The billing team will review within two business days.",
                        "policy_citations": ["BILLING-REVIEW"],
                        "tone": "calm",
                    },
                    {
                        "email_id": "email_003",
                        "draft_subject": "Re: CSV export",
                        "draft_body": "Use the CSV activity export from account settings.",
                        "policy_citations": ["EXPORT-HELP"],
                        "tone": "helpful",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "escalations.json").write_text(
        json.dumps({"escalations": []}),
        encoding="utf-8",
    )
    (artifact_dir / "decision_log.md").write_text(
        "# SUP-01 Case 001 Decision Log\n"
        "## Summary\n"
        "- Processed email_001, email_002, and email_003.\n"
        "## Policy Decisions\n"
        "- email_001 billing review; email_002 no reply; email_003 export help.\n"
        "- no escalation required.\n"
        "## Human Review\n"
        "- None.\n",
        encoding="utf-8",
    )
    result = score_task(root, "SUP-01", "case_001", artifact_dir)
    assert result["success"]


def test_sample_api01_score(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "tool_calls.json").write_text(
        json.dumps(
            {
                "calls": [
                    {
                        "step": 1,
                        "tool_id": "accounts.get",
                        "params": {"account_id": "acct_api_001"},
                        "reason": "Need current account state before mutation.",
                    },
                    {
                        "step": 2,
                        "tool_id": "accounts.set_export_access",
                        "params": {
                            "account_id": "acct_api_001",
                            "field": "export_enabled",
                            "value": True,
                        },
                        "reason": "Enable export access through the allowed write tool.",
                    },
                    {
                        "step": 3,
                        "tool_id": "notes.create",
                        "params": {
                            "note_id": "note_api_001",
                            "account_id": "acct_api_001",
                            "body": "Public smoke audit note.",
                        },
                        "reason": "Create the required audit note.",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "result.json").write_text(
        json.dumps(
            {
                "status": "completed",
                "summary": "Enabled export access and created an audit note.",
                "final_state_expectation": [
                    {
                        "path": ["accounts", "acct_api_001", "export_enabled"],
                        "value": True,
                    },
                    {
                        "path": ["notes", "note_api_001", "account_id"],
                        "value": "acct_api_001",
                    },
                ],
                "affected_entities": ["account:acct_api_001", "note:note_api_001"],
                "policy_notes": ["Used only non-admin tools."],
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "decision_log.md").write_text(
        "# API-01 Case 001 Decision Log\n"
        "## Summary\n"
        "- Planned the local API workflow.\n"
        "## Selected Tools\n"
        "- accounts.get; accounts.set_export_access; notes.create.\n"
        "## Policy Constraints\n"
        "- Applied read before write.\n"
        "## Avoided Tools\n"
        "- Avoided accounts.debug_export_flip.\n",
        encoding="utf-8",
    )
    result = score_task(root, "API-01", "case_001", artifact_dir)
    assert result["success"]


def test_scorer_interface_is_enforced(tmp_path):
    task_dir = tmp_path / "BAD-01"
    task_dir.mkdir()
    (task_dir / "scorer.py").write_text("def score(task_dir):\n    return {}\n", encoding="utf-8")

    with pytest.raises(TypeError, match="score signature"):
        load_scorer(task_dir)


def test_agent_config_hash_is_stable():
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs" / "agents" / "baseline.json"

    first_id, first_hash = load_agent_config(config_path)
    second_id, second_hash = load_agent_config(config_path)

    assert first_id == "baseline"
    assert first_hash == second_hash
