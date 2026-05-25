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


def doc01_config(case_id: str) -> dict:
    path = root_dir() / "fixtures" / "public" / "DOC-01" / case_id / "check_config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sample_answer(config: dict, *, include_all_sections: bool = True, extra_line: str = "") -> str:
    sections = config["answer"]["required_sections"]
    if not include_all_sections:
        sections = sections[:-1]
    lines = [
        sections[0],
        "",
        sections[1],
        *[f"- {phrase}." for phrase in config["answer"]["required_phrases"]],
    ]
    for section in sections[2:]:
        lines.extend(["", section, "- Grounded in the provided corpus."])
    if extra_line:
        lines.extend(["", extra_line])
    return "\n".join(lines) + "\n"


def sample_citations_and_claims(config: dict) -> tuple[dict, dict]:
    citations = []
    claims = []
    for claim_id, rule in config["claims"]["required"].items():
        citation_ids = []
        for index, evidence in enumerate(rule.get("required_evidence", []), start=1):
            citation_id = f"c_{claim_id}_{index}"
            citation_ids.append(citation_id)
            citations.append(
                {
                    "id": citation_id,
                    "doc_id": evidence["doc_id"],
                    "quote": evidence["quote"],
                }
            )
        claims.append(
            {
                "id": claim_id,
                "text": rule["required_text"],
                "supported": bool(rule["supported"]),
                "citation_ids": citation_ids,
            }
        )
    return {"citations": citations}, {"claims": claims}


def write_valid_artifacts(artifact_dir: Path, case_id: str) -> None:
    config = doc01_config(case_id)
    citations, claims = sample_citations_and_claims(config)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "answer.md").write_text(sample_answer(config), encoding="utf-8")
    (artifact_dir / "citations.json").write_text(
        json.dumps(citations, indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "claims.json").write_text(
        json.dumps(claims, indent=2) + "\n",
        encoding="utf-8",
    )


def test_doc01_valid_public_cases_pass(tmp_path):
    for case_id in ("case_001", "case_002", "case_003"):
        artifact_dir = tmp_path / case_id
        write_valid_artifacts(artifact_dir, case_id)

        result = score_task(root_dir(), "DOC-01", case_id, artifact_dir)

        assert result["success"], case_id
        assert result["score"] >= result["pass_threshold"], case_id
        assert REQUIRED_SCORE_FIELDS.issubset(result), case_id


def test_doc01_missing_answer_fails(tmp_path):
    artifact_dir = tmp_path / "missing-answer"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "answer.md").unlink()

    result = score_task(root_dir(), "DOC-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert "missing required file: answer.md" in result["policy_violations"]


def test_doc01_invalid_citations_json_fails(tmp_path):
    artifact_dir = tmp_path / "invalid-citations"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "citations.json").write_text("{not valid json", encoding="utf-8")

    result = score_task(root_dir(), "DOC-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.4
    assert "invalid JSON: citations.json" in result["policy_violations"]


def test_doc01_invalid_claims_json_fails(tmp_path):
    artifact_dir = tmp_path / "invalid-claims"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "claims.json").write_text("{not valid json", encoding="utf-8")

    result = score_task(root_dir(), "DOC-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.4
    assert "invalid JSON: claims.json" in result["policy_violations"]


def test_doc01_unsupported_claim_in_answer_is_detected(tmp_path):
    artifact_dir = tmp_path / "unsupported-answer"
    config = doc01_config("case_003")
    write_valid_artifacts(artifact_dir, "case_003")
    (artifact_dir / "answer.md").write_text(
        sample_answer(config, extra_line="Orion Sync is SOC 2 Type II certified."),
        encoding="utf-8",
    )

    result = score_task(root_dir(), "DOC-01", "case_003", artifact_dir)

    assert not result["success"]
    assert any("unsupported answer claims" in item for item in result["policy_violations"])


def test_doc01_missing_citation_is_penalized(tmp_path):
    artifact_dir = tmp_path / "missing-citation"
    write_valid_artifacts(artifact_dir, "case_001")
    claims = json.loads((artifact_dir / "claims.json").read_text(encoding="utf-8"))
    claims["claims"][0]["citation_ids"] = []
    (artifact_dir / "claims.json").write_text(json.dumps(claims), encoding="utf-8")

    result = score_task(root_dir(), "DOC-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.65
    assert "missing citation support: support_target" in result["policy_violations"]


def test_doc01_stale_citation_is_penalized(tmp_path):
    artifact_dir = tmp_path / "stale-citation"
    write_valid_artifacts(artifact_dir, "case_002")
    citations = json.loads((artifact_dir / "citations.json").read_text(encoding="utf-8"))
    citations["citations"][0]["doc_id"] = "legacy_policy"
    citations["citations"][0]["quote"] = "The stale archive says priority incidents are acknowledged within 24 hours."
    (artifact_dir / "citations.json").write_text(json.dumps(citations), encoding="utf-8")

    result = score_task(root_dir(), "DOC-01", "case_002", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.5
    assert "stale source cited: legacy_policy" in result["policy_violations"]


def test_doc01_cited_snippet_must_exist_in_source(tmp_path):
    artifact_dir = tmp_path / "bad-snippet"
    write_valid_artifacts(artifact_dir, "case_001")
    citations = json.loads((artifact_dir / "citations.json").read_text(encoding="utf-8"))
    citations["citations"][0]["quote"] = "This quote is not in the source document."
    (artifact_dir / "citations.json").write_text(json.dumps(citations), encoding="utf-8")

    result = score_task(root_dir(), "DOC-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.6
    assert any("citation quote not found" in item for item in result["policy_violations"])


def test_doc01_not_enough_evidence_branch_works(tmp_path):
    artifact_dir = tmp_path / "not-enough-evidence"
    write_valid_artifacts(artifact_dir, "case_003")

    result = score_task(root_dir(), "DOC-01", "case_003", artifact_dir)

    assert result["success"]
    claims = json.loads((artifact_dir / "claims.json").read_text(encoding="utf-8"))
    unsupported = {item["id"] for item in claims["claims"] if item["supported"] is False}
    assert {"hipaa_export_ready", "soc2_type2_certified"}.issubset(unsupported)


def test_doc01_extra_file_detection_works(tmp_path):
    artifact_dir = tmp_path / "extra"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "notes.txt").write_text("extra output\n", encoding="utf-8")

    result = score_task(root_dir(), "DOC-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.8
    assert any("extra files" in item for item in result["policy_violations"])


def test_doc01_mutation_script_creates_public_style_case(tmp_path):
    script_path = root_dir() / "scripts" / "create_doc01_mutation.py"
    spec = importlib.util.spec_from_file_location("create_doc01_mutation", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    output = tmp_path / "mutation"
    module.copy_mutated_case(root_dir() / "fixtures" / "public" / "DOC-01" / "case_001", output)

    assert (output / "spec.md").exists()
    assert (output / "check_config.json").exists()
    assert (output / "corpus" / "extra_distractor.md").exists()
    config = json.loads((output / "check_config.json").read_text(encoding="utf-8"))
    assert config["required_artifacts"] == ["answer.md", "citations.json", "claims.json"]


def test_doc01_compare_reports_still_redact_unsafe_diagnostics(tmp_path):
    baseline = tmp_path / "baseline" / "DOC-01_case_001" / "score.json"
    candidate = tmp_path / "candidate" / "DOC-01_case_001" / "score.json"
    baseline.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    baseline.write_text(
        json.dumps(
            {
                "task_id": "DOC-01",
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
                "task_id": "DOC-01",
                "case_id": "case_001",
                "score": 0.5,
                "success": False,
                "policy_violations": ["correct answer was hidden_label expected=DOC_PRIVATE"],
            }
        ),
        encoding="utf-8",
    )

    report = render_markdown_report(compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate"))

    assert "DOC_PRIVATE" not in report
    assert "hidden_label" not in report
    assert "[REDACTED]" in report
