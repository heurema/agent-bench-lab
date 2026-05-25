from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

VALID_EXPLOIT_STATUSES = {"implemented", "planned", "not_applicable"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def decision_grade_tasks(root: Path) -> set[str]:
    lifecycle = load_json(root / "configs" / "task_lifecycle.json")
    return {
        task_id
        for task_id, entry in lifecycle.get("tasks", {}).items()
        if entry.get("status") in {"decision-grade", "verified"}
    }


def tracked_files(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def check_hardening_gates(root: Path) -> list[str]:
    config = load_json(root / "configs" / "hardening_gates.json")
    entries = config.get("tasks", {})
    errors: list[str] = []

    if not isinstance(entries, dict):
        return ["configs/hardening_gates.json: tasks must be an object"]

    expected_tasks = decision_grade_tasks(root)
    configured_tasks = set(entries)

    for missing in sorted(expected_tasks - configured_tasks):
        errors.append(f"{missing}: missing hardening gate entry")
    for extra in sorted(configured_tasks - expected_tasks):
        errors.append(f"{extra}: hardening gate entry is only expected for decision-grade tasks")

    tracked = tracked_files(root)
    generated_tracked = sorted(path for path in tracked if path.startswith("artifacts/"))
    if generated_tracked:
        errors.append(f"generated mutation output is tracked: {', '.join(generated_tracked)}")

    for task_id, entry in sorted(entries.items()):
        if entry.get("task_id") != task_id:
            errors.append(f"{task_id}: task_id must match config key")

        mutation_required = entry.get("mutation_smoke_required") is True
        mutation_script = entry.get("mutation_script")
        if mutation_required:
            if not isinstance(mutation_script, str) or not (root / mutation_script).exists():
                errors.append(f"{task_id}: required mutation script does not exist")
            expected_files = entry.get("expected_output_files")
            if not isinstance(expected_files, list) or not expected_files:
                errors.append(f"{task_id}: mutation smoke requires expected_output_files")

        mutation_output = entry.get("mutation_output")
        if not isinstance(mutation_output, str) or not mutation_output.startswith("artifacts/"):
            errors.append(f"{task_id}: mutation_output must be under artifacts/")
        elif mutation_output in tracked:
            errors.append(f"{task_id}: mutation_output path is tracked")

        exploit_status = entry.get("exploit_smoke_status")
        if exploit_status not in VALID_EXPLOIT_STATUSES:
            errors.append(f"{task_id}: invalid exploit_smoke_status {exploit_status!r}")
        if exploit_status in {"planned", "not_applicable"}:
            reason = entry.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{task_id}: {exploit_status} exploit status requires a reason")

        if entry.get("public_safe") is not True:
            errors.append(f"{task_id}: public_safe must be true")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate hardening gate declarations.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    errors = check_hardening_gates(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Hardening gate check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
