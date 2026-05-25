from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_STATUSES = {"experimental", "decision-grade", "verified", "deprecated"}
DECISION_READY_STATUSES = {"decision-grade", "verified"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def task_dirs(root: Path) -> set[str]:
    return {
        path.name
        for path in (root / "tasks").iterdir()
        if path.is_dir() and (path / "task.json").exists()
    }


def suite_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((root / "configs" / "suites").glob("*.json")):
        data = load_json(path)
        suite_id = data.get("suite_id")
        if isinstance(suite_id, str):
            ids.add(suite_id)
    return ids


def require_text(entry: dict, field: str, errors: list[str]) -> None:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{entry.get('task_id')}: missing non-empty {field}")


def require_list(entry: dict, field: str, errors: list[str]) -> None:
    value = entry.get(field)
    if not isinstance(value, list) or not value:
        errors.append(f"{entry.get('task_id')}: missing non-empty {field}")


def check_decision_grade(root: Path, task_id: str, entry: dict, errors: list[str]) -> None:
    task_dir = root / "tasks" / task_id
    for filename in ("task.json", "prompt.md", "scorer.py"):
        if not (task_dir / filename).exists():
            errors.append(f"{task_id}: missing tasks/{task_id}/{filename}")

    fixture_dir = root / "fixtures" / "public" / task_id
    if not fixture_dir.exists():
        errors.append(f"{task_id}: missing public fixture directory")

    docs_reference = entry.get("docs_reference")
    if not isinstance(docs_reference, str) or not (root / docs_reference).exists():
        errors.append(f"{task_id}: docs_reference does not exist")

    require_text(entry, "private_holdout_strategy", errors)
    require_text(entry, "mutation_strategy", errors)
    require_text(entry, "primary_oracle", errors)
    require_list(entry, "scorer_contracts", errors)

    if entry.get("public_cases") is not True:
        errors.append(f"{task_id}: decision-grade task must declare public_cases true")
    if entry.get("has_redacted_feedback") is not True:
        errors.append(f"{task_id}: decision-grade task must declare redacted feedback")
    if not entry.get("exploit_smoke_status"):
        errors.append(f"{task_id}: missing exploit_smoke_status")


def check_lifecycle(root: Path) -> list[str]:
    config_path = root / "configs" / "task_lifecycle.json"
    config = load_json(config_path)
    entries = config.get("tasks", {})
    errors: list[str] = []

    if not isinstance(entries, dict):
        return ["configs/task_lifecycle.json: tasks must be an object"]

    actual_tasks = task_dirs(root)
    configured_tasks = set(entries)
    valid_suite_ids = suite_ids(root)

    for missing in sorted(actual_tasks - configured_tasks):
        errors.append(f"{missing}: missing lifecycle entry")
    for extra in sorted(configured_tasks - actual_tasks):
        errors.append(f"{extra}: lifecycle entry has no matching task directory")

    for task_id, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            errors.append(f"{task_id}: lifecycle entry must be an object")
            continue
        if entry.get("task_id") != task_id:
            errors.append(f"{task_id}: task_id must match config key")

        status = entry.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{task_id}: invalid status {status!r}")
            continue

        require_text(entry, "introduced_in", errors)
        require_text(entry, "current_version", errors)
        require_text(entry, "primary_oracle", errors)
        require_list(entry, "suite_ids", errors)

        for suite_id in entry.get("suite_ids", []):
            if suite_id not in valid_suite_ids:
                errors.append(f"{task_id}: unknown suite_id {suite_id}")

        if status in DECISION_READY_STATUSES:
            check_decision_grade(root, task_id, entry, errors)

        verified = entry.get("verified")
        if status == "verified" and verified is not True:
            errors.append(f"{task_id}: verified status requires verified=true")
        if status != "verified" and verified is True:
            errors.append(f"{task_id}: verified=true is only allowed for verified tasks")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate task-family lifecycle metadata.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    errors = check_lifecycle(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Lifecycle check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
