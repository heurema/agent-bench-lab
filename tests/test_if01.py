import importlib.util
import json
from pathlib import Path

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


def write_case_001_valid(artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "artifact.md").write_text(
        "# Public Launch Note\n"
        "- This project uses versioned tasks.\n"
        "- This project uses repeatable scoring.\n"
        "- This project starts from public templates.\n",
        encoding="utf-8",
    )


def write_case_002_valid(artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "artifact.json").write_text(
        json.dumps(
            {
                "project": "Agent Bench Lab",
                "artifact_type": "evaluation_contract",
                "publishable": True,
                "checks": ["validation", "scoring", "compare-runs"],
            }
        ),
        encoding="utf-8",
    )


def write_case_003_valid(artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "artifact.md").write_text(
        "# Contract Brief\n"
        "## Scope\n"
        "Northstar Review checks strict instruction following with public examples and private holdout separation.\n"
        "## Acceptance\n"
        "The artifact mentions mutation cases, keeps the requested order, and stays inside the word limit.\n"
        "## Out of Scope\n"
        "No live services, no extra files, and no private data are required.\n",
        encoding="utf-8",
    )


def test_if01_valid_public_cases_pass(tmp_path):
    root = root_dir()
    cases = {
        "case_001": write_case_001_valid,
        "case_002": write_case_002_valid,
        "case_003": write_case_003_valid,
    }
    for case_id, writer in cases.items():
        artifact_dir = tmp_path / case_id
        writer(artifact_dir)
        result = score_task(root, "IF-01", case_id, artifact_dir)
        assert result["success"], case_id
        assert result["score"] >= result["pass_threshold"], case_id
        assert REQUIRED_SCORE_FIELDS.issubset(result), case_id


def test_if01_missing_required_file_fails(tmp_path):
    artifact_dir = tmp_path / "empty"
    artifact_dir.mkdir()

    result = score_task(root_dir(), "IF-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert any("missing required file" in item for item in result["policy_violations"])


def test_if01_invalid_json_fails(tmp_path):
    artifact_dir = tmp_path / "invalid-json"
    artifact_dir.mkdir()
    (artifact_dir / "artifact.json").write_text("{not valid json", encoding="utf-8")

    result = score_task(root_dir(), "IF-01", "case_002", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert "invalid JSON" in result["policy_violations"]


def test_if01_forbidden_section_caps_score(tmp_path):
    artifact_dir = tmp_path / "forbidden-section"
    write_case_003_valid(artifact_dir)
    with (artifact_dir / "artifact.md").open("a", encoding="utf-8") as handle:
        handle.write("## Internal Notes\nThis section is forbidden.\n")

    result = score_task(root_dir(), "IF-01", "case_003", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.6
    assert any("forbidden headings" in item for item in result["policy_violations"])


def test_if01_banned_phrase_zeroes_score(tmp_path):
    artifact_dir = tmp_path / "banned-phrase"
    write_case_001_valid(artifact_dir)
    with (artifact_dir / "artifact.md").open("a", encoding="utf-8") as handle:
        handle.write("benchmark answer\n")

    result = score_task(root_dir(), "IF-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] == 0.0
    assert any("banned phrases" in item for item in result["policy_violations"])


def test_if01_extra_file_detection_caps_score(tmp_path):
    artifact_dir = tmp_path / "extra-file"
    write_case_001_valid(artifact_dir)
    (artifact_dir / "unexpected.txt").write_text("extra output\n", encoding="utf-8")

    result = score_task(root_dir(), "IF-01", "case_001", artifact_dir)

    assert not result["success"]
    assert result["score"] <= 0.75
    assert any("extra files" in item for item in result["policy_violations"])


def test_if01_mutation_script_creates_valid_case_structure(tmp_path):
    script_path = root_dir() / "scripts" / "create_if01_mutation.py"
    spec = importlib.util.spec_from_file_location("create_if01_mutation", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    output_dir = module.create_mutation(tmp_path / "mutation")

    assert (output_dir / "spec.md").exists()
    config = json.loads((output_dir / "check_config.json").read_text(encoding="utf-8"))
    assert config["case_id"] == "case_mutation_001"
    assert config["required_files"][0]["path"] == "artifact.md"
