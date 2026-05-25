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


def api01_config(case_id: str) -> dict:
    path = root_dir() / "fixtures" / "public" / "API-01" / case_id / "check_config.json"
    return json.loads(path.read_text(encoding="utf-8"))


def api01_catalog(case_id: str) -> dict:
    path = root_dir() / "fixtures" / "public" / "API-01" / case_id / "api_catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))


def sample_tool_calls(config: dict, catalog: dict) -> dict:
    tools = {
        tool["tool_id"]: tool
        for tool in catalog.get("tools", [])
        if isinstance(tool, dict) and "tool_id" in tool
    }
    calls = []
    for expected in config["expected_calls"]:
        tool_id = expected["tool_id"]
        tool = tools[tool_id]
        params = dict(expected.get("params", {}))
        for param in tool.get("required_params", []):
            if param in params:
                continue
            if param == "body":
                params[param] = "Public smoke audit note."
            elif param == "summary":
                params[param] = "Public smoke follow-up task."
            elif param == "reason":
                params[param] = "Policy requires escalation."
            else:
                params[param] = f"sample_{param}"
        calls.append(
            {
                "step": expected["step"],
                "tool_id": tool_id,
                "params": params,
                "reason": f"Use {tool_id} according to policy.",
            }
        )
    return {"calls": calls}


def sample_result(config: dict) -> dict:
    return {
        "status": config["expected_status"],
        "summary": "Completed the synthetic local API workflow.",
        "final_state_expectation": config["expected_state"],
        "affected_entities": config["required_affected_entities"],
        "policy_notes": ["Used only the provided synthetic API catalog."],
    }


def sample_decision_log(config: dict, *, include_all_sections: bool = True) -> str:
    sections = config["decision_log"]["required_sections"]
    if not include_all_sections:
        sections = sections[:-1]
    lines = [
        sections[0],
        "",
        sections[1],
        "- Planned the synthetic local API workflow.",
        "",
        sections[2],
        *[f"- {phrase}." for phrase in config["decision_log"]["required_phrases"]],
    ]
    for section in sections[3:]:
        lines.extend(["", section, "- Applied policy constraints and avoided forbidden tools."])
    return "\n".join(lines) + "\n"


def write_valid_artifacts(artifact_dir: Path, case_id: str) -> None:
    config = api01_config(case_id)
    catalog = api01_catalog(case_id)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "tool_calls.json").write_text(
        json.dumps(sample_tool_calls(config, catalog), indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "result.json").write_text(
        json.dumps(sample_result(config), indent=2) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "decision_log.md").write_text(sample_decision_log(config), encoding="utf-8")


def load_tool_calls(artifact_dir: Path) -> dict:
    return json.loads((artifact_dir / "tool_calls.json").read_text(encoding="utf-8"))


def save_tool_calls(artifact_dir: Path, tool_calls: dict) -> None:
    (artifact_dir / "tool_calls.json").write_text(json.dumps(tool_calls), encoding="utf-8")


def test_api01_valid_public_cases_pass(tmp_path):
    for case_id in ("case_001", "case_002", "case_003"):
        artifact_dir = tmp_path / case_id
        write_valid_artifacts(artifact_dir, case_id)

        result = score_task(root_dir(), "API-01", case_id, artifact_dir)

        assert result["success"], case_id
        assert result["score"] >= result["pass_threshold"], case_id
        assert REQUIRED_SCORE_FIELDS.issubset(result), case_id


def test_api01_missing_tool_calls_fails(tmp_path):
    artifact_dir = tmp_path / "missing-tool-calls"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "tool_calls.json").unlink()

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert "missing required file: tool_calls.json" in result["policy_violations"]


def test_api01_invalid_json_fails(tmp_path):
    artifact_dir = tmp_path / "invalid-json"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "tool_calls.json").write_text("{not valid json", encoding="utf-8")

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.4
    assert "invalid JSON: tool_calls.json" in result["policy_violations"]


def test_api01_invented_tool_id_fails(tmp_path):
    artifact_dir = tmp_path / "invented-tool"
    write_valid_artifacts(artifact_dir, "case_001")
    tool_calls = load_tool_calls(artifact_dir)
    tool_calls["calls"][1]["tool_id"] = "accounts.magic"
    save_tool_calls(artifact_dir, tool_calls)

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.4
    assert "invented tool id: accounts.magic" in result["policy_violations"]


def test_api01_forbidden_endpoint_usage_caps_score(tmp_path):
    artifact_dir = tmp_path / "forbidden-tool"
    write_valid_artifacts(artifact_dir, "case_001")
    tool_calls = load_tool_calls(artifact_dir)
    tool_calls["calls"][1]["tool_id"] = "accounts.debug_export_flip"
    save_tool_calls(artifact_dir, tool_calls)

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.2
    assert "forbidden tool used: accounts.debug_export_flip" in result["policy_violations"]


def test_api01_wrong_entity_id_fails(tmp_path):
    artifact_dir = tmp_path / "wrong-entity"
    write_valid_artifacts(artifact_dir, "case_001")
    tool_calls = load_tool_calls(artifact_dir)
    tool_calls["calls"][1]["params"]["account_id"] = "acct_api_wrong"
    save_tool_calls(artifact_dir, tool_calls)

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.5
    assert any("unknown entity id" in item for item in result["policy_violations"])


def test_api01_wrong_call_order_fails(tmp_path):
    artifact_dir = tmp_path / "wrong-order"
    write_valid_artifacts(artifact_dir, "case_001")
    tool_calls = load_tool_calls(artifact_dir)
    tool_calls["calls"][0], tool_calls["calls"][1] = tool_calls["calls"][1], tool_calls["calls"][0]
    tool_calls["calls"][0]["step"] = 1
    tool_calls["calls"][1]["step"] = 2
    save_tool_calls(artifact_dir, tool_calls)

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.6
    assert "wrong call order: accounts.get before accounts.set_export_access" in result[
        "policy_violations"
    ]


def test_api01_missing_required_read_before_write_fails(tmp_path):
    artifact_dir = tmp_path / "missing-read-before-write"
    write_valid_artifacts(artifact_dir, "case_001")
    tool_calls = load_tool_calls(artifact_dir)
    tool_calls["calls"] = [item for item in tool_calls["calls"] if item["tool_id"] != "accounts.get"]
    for index, call in enumerate(tool_calls["calls"], start=1):
        call["step"] = index
    save_tool_calls(artifact_dir, tool_calls)

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.55
    assert "missing read-before-write: accounts.get before accounts.set_export_access" in result[
        "policy_violations"
    ]


def test_api01_expected_final_state_diff_is_checked(tmp_path):
    artifact_dir = tmp_path / "state-diff"
    write_valid_artifacts(artifact_dir, "case_001")
    tool_calls = load_tool_calls(artifact_dir)
    tool_calls["calls"][1]["params"]["value"] = False
    save_tool_calls(artifact_dir, tool_calls)

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.55
    assert any("state diff mismatch" in item for item in result["policy_violations"])


def test_api01_blocked_escalated_case_works(tmp_path):
    artifact_dir = tmp_path / "blocked"
    write_valid_artifacts(artifact_dir, "case_003")

    result = score_task(root_dir(), "API-01", "case_003", artifact_dir)

    assert result["success"]
    assert result["score"] >= 0.9


def test_api01_result_status_mismatch_fails(tmp_path):
    artifact_dir = tmp_path / "status-mismatch"
    write_valid_artifacts(artifact_dir, "case_003")
    result_json = json.loads((artifact_dir / "result.json").read_text(encoding="utf-8"))
    result_json["status"] = "completed"
    (artifact_dir / "result.json").write_text(json.dumps(result_json), encoding="utf-8")

    result = score_task(root_dir(), "API-01", "case_003", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.4
    assert "result status mismatch: completed" in result["policy_violations"]


def test_api01_missing_decision_log_section_fails(tmp_path):
    artifact_dir = tmp_path / "missing-log-section"
    config = api01_config("case_001")
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "decision_log.md").write_text(
        sample_decision_log(config, include_all_sections=False),
        encoding="utf-8",
    )

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.75
    assert "missing or misordered decision_log section" in result["policy_violations"]


def test_api01_extra_file_detection_works(tmp_path):
    artifact_dir = tmp_path / "extra"
    write_valid_artifacts(artifact_dir, "case_001")
    (artifact_dir / "scratch.txt").write_text("extra output\n", encoding="utf-8")

    result = score_task(root_dir(), "API-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.8
    assert any("extra files" in item for item in result["policy_violations"])


def test_api01_mutation_script_creates_public_style_case(tmp_path):
    script_path = root_dir() / "scripts" / "create_api01_mutation.py"
    spec = importlib.util.spec_from_file_location("create_api01_mutation", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    output = tmp_path / "mutation"
    module.copy_mutated_case(root_dir() / "fixtures" / "public" / "API-01" / "case_001", output)

    assert (output / "spec.md").exists()
    assert (output / "check_config.json").exists()
    catalog = json.loads((output / "api_catalog.json").read_text(encoding="utf-8"))
    state = json.loads((output / "api_state.json").read_text(encoding="utf-8"))
    assert any(tool["tool_id"] == "reports.preview" for tool in catalog["tools"])
    assert "report_api_999" in state["reports"]


def test_api01_compare_reports_still_redact_unsafe_diagnostics(tmp_path):
    baseline = tmp_path / "baseline" / "API-01_case_001" / "score.json"
    candidate = tmp_path / "candidate" / "API-01_case_001" / "score.json"
    baseline.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    baseline.write_text(
        json.dumps(
            {
                "task_id": "API-01",
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
                "task_id": "API-01",
                "case_id": "case_001",
                "score": 0.5,
                "success": False,
                "policy_violations": ["correct answer was hidden_label expected=API_PRIVATE"],
            }
        ),
        encoding="utf-8",
    )

    report = render_markdown_report(compare_score_dirs(tmp_path / "baseline", tmp_path / "candidate"))

    assert "API_PRIVATE" not in report
    assert "hidden_label" not in report
    assert "[REDACTED]" in report
