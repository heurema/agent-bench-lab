from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from agent_bench_lab.compare import compare_score_dirs, render_markdown_report
from agent_bench_lab.scoring import score_task

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


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def sup01_config(case_id: str) -> dict:
    path = root_dir() / "fixtures" / "public" / "SUP-01" / case_id / "check_config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sample_triage(config: dict) -> dict:
    return {
        "triage": [
            {"email_id": email_id, **rule}
            for email_id, rule in config["triage"]["required"].items()
        ]
    }


def sample_drafts(config: dict) -> dict:
    drafts = []
    for email_id, rule in config["drafts"]["required"].items():
        drafts.append(
            {
                "email_id": email_id,
                "draft_subject": f"Re: {email_id}",
                "draft_body": "\n".join(rule["required_phrases"]),
                "policy_citations": rule["required_policy_citations"],
                "tone": rule["tone"],
            }
        )
    return {"drafts": drafts}


def sample_escalations(config: dict) -> dict:
    return {
        "escalations": [
            {
                "email_id": email_id,
                "escalation_team": rule["escalation_team"],
                "escalation_reason": rule["escalation_reason"],
                "required_context": rule["required_context"],
            }
            for email_id, rule in config["escalations"]["required"].items()
        ]
    }


def sample_decision_log(config: dict, *, include_all_sections: bool = True, extra_line: str = "") -> str:
    sections = config["decision_log"]["required_sections"]
    if not include_all_sections:
        sections = sections[:-1]
    lines = [
        sections[0],
        "",
        sections[1],
        "- Processed the support inbox.",
        "",
        sections[2],
        *[f"- {phrase}." for phrase in config["decision_log"]["required_phrases"]],
    ]
    for section in sections[3:]:
        lines.extend(["", section, "- Listed unresolved items for human review."])
    if extra_line:
        lines.extend(["", extra_line])
    return "\n".join(lines) + "\n"


def write_valid_artifacts(artifact_dir: Path, case_id: str) -> None:
    config = sup01_config(case_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "triage.json").write_text(
        json.dumps(sample_triage(config), indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "drafts.json").write_text(
        json.dumps(sample_drafts(config), indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "escalations.json").write_text(
        json.dumps(sample_escalations(config), indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "decision_log.md").write_text(sample_decision_log(config), encoding="utf-8")


def test_sup01_valid_public_cases_pass(tmp_path):
    for case_id in ("case_001", "case_002", "case_003"):
        artifact_dir = tmp_path / case_id
        write_valid_artifacts(artifact_dir, case_id)

        result = score_task(root_dir(), "SUP-01", case_id, artifact_dir)

        assert result["success"], case_id
        assert result["score"] >= result["pass_threshold"], case_id
        assert REQUIRED_SCORE_FIELDS.issubset(result), case_id


def test_sup01_missing_triage_fails(tmp_path):
    artifact_dir = tmp_path / "missing-triage"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "triage.json").unlink()

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert "missing required file: triage.json" in result["policy_violations"]


def test_sup01_invalid_json_fails(tmp_path):
    artifact_dir = tmp_path / "invalid-json"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "triage.json").write_text("{not valid json", encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.4
    assert "invalid JSON: triage.json" in result["policy_violations"]


def test_sup01_unknown_email_id_is_detected(tmp_path):
    artifact_dir = tmp_path / "unknown-email"
    write_valid_artifacts(artifact_dir, "case_001")
    triage = json.loads((artifact_dir / "triage.json").read_text(encoding="utf-8"))
    triage["triage"].append(
        {
            "email_id": "email_999",
            "category": "billing",
            "priority": "normal",
            "requires_reply": True,
            "requires_escalation": False,
            "reason_code": "duplicate_charge_review",
        }
    )
    (artifact_dir / "triage.json").write_text(json.dumps(triage), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.5
    assert any("unknown email ids" in item for item in result["policy_violations"])


def test_sup01_wrong_category_or_priority_fails(tmp_path):
    artifact_dir = tmp_path / "wrong-triage"
    write_valid_artifacts(artifact_dir, "case_001")
    triage = json.loads((artifact_dir / "triage.json").read_text(encoding="utf-8"))
    triage["triage"][0]["category"] = "informational"
    triage["triage"][0]["priority"] = "low"
    (artifact_dir / "triage.json").write_text(json.dumps(triage), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.65
    assert "wrong triage category: email_001" in result["policy_violations"]
    assert "wrong triage priority: email_001" in result["policy_violations"]


def test_sup01_missing_required_reply_fails(tmp_path):
    artifact_dir = tmp_path / "missing-reply"
    write_valid_artifacts(artifact_dir, "case_001")
    drafts = json.loads((artifact_dir / "drafts.json").read_text(encoding="utf-8"))
    drafts["drafts"] = [item for item in drafts["drafts"] if item["email_id"] != "email_001"]
    (artifact_dir / "drafts.json").write_text(json.dumps(drafts), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.6
    assert "missing required draft: email_001" in result["policy_violations"]


def test_sup01_forbidden_reply_for_no_reply_email_fails(tmp_path):
    artifact_dir = tmp_path / "forbidden-reply"
    write_valid_artifacts(artifact_dir, "case_001")
    drafts = json.loads((artifact_dir / "drafts.json").read_text(encoding="utf-8"))
    drafts["drafts"].append(
        {
            "email_id": "email_002",
            "draft_subject": "Re: thanks",
            "draft_body": "No action needed.",
            "policy_citations": ["INFO-NO-REPLY"],
            "tone": "concise",
        }
    )
    (artifact_dir / "drafts.json").write_text(json.dumps(drafts), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.65
    assert "forbidden draft present: email_002" in result["policy_violations"]


def test_sup01_missing_required_escalation_fails(tmp_path):
    artifact_dir = tmp_path / "missing-escalation"
    write_valid_artifacts(artifact_dir, "case_002")
    escalations = json.loads((artifact_dir / "escalations.json").read_text(encoding="utf-8"))
    escalations["escalations"] = [
        item for item in escalations["escalations"] if item["email_id"] != "email_101"
    ]
    (artifact_dir / "escalations.json").write_text(json.dumps(escalations), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_002", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.35
    assert "missing required escalation: email_101" in result["policy_violations"]


def test_sup01_prohibited_promise_in_draft_is_detected(tmp_path):
    artifact_dir = tmp_path / "prohibited-promise"
    write_valid_artifacts(artifact_dir, "case_002")
    drafts = json.loads((artifact_dir / "drafts.json").read_text(encoding="utf-8"))
    drafts["drafts"][0]["draft_body"] += "\nThe credit approved amount is ready."
    (artifact_dir / "drafts.json").write_text(json.dumps(drafts), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_002", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.35
    assert "prohibited promise in draft: email_101" in result["policy_violations"]


def test_sup01_missing_policy_citation_is_penalized(tmp_path):
    artifact_dir = tmp_path / "missing-citation"
    write_valid_artifacts(artifact_dir, "case_001")
    drafts = json.loads((artifact_dir / "drafts.json").read_text(encoding="utf-8"))
    drafts["drafts"][1]["policy_citations"] = []
    (artifact_dir / "drafts.json").write_text(json.dumps(drafts), encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.65
    assert "missing policy citation: email_003" in result["policy_violations"]


def test_sup01_decision_log_required_sections_work(tmp_path):
    artifact_dir = tmp_path / "bad-log"
    config = sup01_config("case_003")
    write_valid_artifacts(artifact_dir, "case_003")
    (artifact_dir / "decision_log.md").write_text(
        sample_decision_log(config, include_all_sections=False),
        encoding="utf-8",
    )

    result = score_task(root_dir(), "SUP-01", "case_003", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.75
    assert "missing or misordered decision_log section" in result["policy_violations"]


def test_sup01_extra_file_detection_works(tmp_path):
    artifact_dir = tmp_path / "extra"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "notes.txt").write_text("extra output\n", encoding="utf-8")

    result = score_task(root_dir(), "SUP-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.8
    assert any("extra files" in item for item in result["policy_violations"])


def test_sup01_mutation_script_creates_public_style_case(tmp_path):
    script_path = root_dir() / "scripts" / "create_sup01_mutation.py"
    spec = importlib.util.spec_from_file_location("create_sup01_mutation", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    output = tmp_path / "mutation"
    module.copy_mutated_case(root_dir() / "fixtures" / "public" / "SUP-01" / "case_001", output)

    assert (output / "spec.md").exists()
    assert (output / "check_config.json").exists()
    assert (output / "inbox" / "email_999.eml").exists()
    config = json.loads((output / "check_config.json").read_text(encoding="utf-8"))
    assert config["required_artifacts"] == [
        "triage.json",
        "drafts.json",
        "escalations.json",
        "decision_log.md",
    ]


def test_sup01_compare_reports_still_redact_unsafe_diagnostics(tmp_path):
    baseline = tmp_path / "baseline" / "SUP-01_case_001" / "score.json"
    candidate = tmp_path / "candidate" / "SUP-01_case_001" / "score.json"
    baseline.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    baseline.write_text(
        json.dumps(
            {
                "task_id": "SUP-01",
                "case_id": "case_001",
                "score": 1.0,
                "success": True,
                "policy_violations": [],
            }
        ),
        encoding="utf-8",
    )
    candidate.write_text(
        json.dumps(
            {
                "task_id": "SUP-01",
                "case_id": "case_001",
                "score": 0.5,
                "success": False,
                "policy_violations": ["correct answer was hidden_label expected=SUP_PRIVATE"],
            }
        ),
        encoding="utf-8",
    )

    report = render_markdown_report(compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate"))

    assert "SUP_PRIVATE" not in report
    assert "hidden_label" not in report
    assert "[REDACTED]" in report
