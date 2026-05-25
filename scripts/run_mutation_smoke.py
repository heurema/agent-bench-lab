from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def selected_entries(root: Path, task_id: str | None) -> list[tuple[str, dict]]:
    config = load_json(root / "configs" / "hardening_gates.json")
    entries = config.get("tasks", {})
    selected = []
    for current_task_id, entry in sorted(entries.items()):
        if task_id and current_task_id != task_id:
            continue
        if entry.get("mutation_smoke_required") is True:
            selected.append((current_task_id, entry))
    return selected


def output_dir(root: Path, out_root: Path | None, task_id: str, entry: dict) -> Path:
    if out_root is not None:
        return out_root / task_id / "case_mutation_001"
    return root / entry["mutation_output"]


def run_mutation(root: Path, task_id: str, entry: dict, out_root: Path | None) -> None:
    script = root / entry["mutation_script"]
    output = output_dir(root, out_root, task_id, entry)
    if output.exists():
        shutil.rmtree(output)

    subprocess.run(
        [sys.executable, str(script), "--out", str(output)],
        cwd=root,
        check=True,
    )

    if not output.exists():
        raise RuntimeError(f"{task_id}: mutation output was not created: {output}")
    for rel_path in entry.get("expected_output_files", []):
        expected = output / rel_path
        if not expected.exists():
            raise RuntimeError(f"{task_id}: expected mutation output missing: {expected}")

    print(f"{task_id}: mutation smoke output ok at {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public mutation smoke generators.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--task", help="Run one task family only.")
    parser.add_argument(
        "--out-root",
        type=Path,
        help="Override output root. Defaults to each task mutation_output config.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    out_root = args.out_root.resolve() if args.out_root else None
    entries = selected_entries(root, args.task)
    if not entries:
        print("No mutation smoke entries selected.")
        return 1

    for task_id, entry in entries:
        run_mutation(root, task_id, entry, out_root)

    print("Mutation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
