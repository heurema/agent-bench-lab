from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "AtlasOps": "CedarOps",
    "BeaconFlow": "SignalFlow",
    "ClearPort": "NorthPort",
    "acct_api_001": "acct_api_701",
    "acct_api_201": "acct_api_801",
    "ticket_api_201": "ticket_api_801",
    "task_api_201": "task_api_801",
    "note_api_001": "note_api_701",
    "2026-05-24": "2026-05-31",
}


def mutate_text(text: str) -> str:
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def mutate_json(value):
    if isinstance(value, str):
        return mutate_text(value)
    if isinstance(value, list):
        return [mutate_json(item) for item in value]
    if isinstance(value, dict):
        return {key: mutate_json(item) for key, item in value.items()}
    return value


def add_distractors(output: Path) -> None:
    catalog_path = output / "api_catalog.json"
    state_path = output / "api_state.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        tools = catalog.setdefault("tools", [])
        if isinstance(tools, list):
            tools.append(
                {
                    "tool_id": "reports.preview",
                    "category": "read",
                    "operation": "read",
                    "entity": "reports",
                    "id_param": "report_id",
                    "required_params": ["report_id"],
                }
            )
        catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        reports = state.setdefault("reports", {})
        if isinstance(reports, dict):
            reports["report_api_999"] = {
                "title": "Distractor public mutation report",
                "created_at": "2026-05-31T09:00:00Z",
            }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def copy_mutated_case(source: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        target = output / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            target.write_text(json.dumps(mutate_json(data), indent=2) + "\n", encoding="utf-8")
        else:
            target.write_text(mutate_text(path.read_text(encoding="utf-8")), encoding="utf-8")

    add_distractors(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe public-style API-01 mutation case.")
    parser.add_argument(
        "--source",
        default=str(ROOT / "fixtures" / "public" / "API-01" / "case_001"),
        help="Source public API-01 case to mutate.",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "artifacts" / "mutations" / "API-01" / "case_mutation_001"),
        help="Ignored output directory for the mutation case.",
    )
    args = parser.parse_args()
    copy_mutated_case(Path(args.source).resolve(), Path(args.out).resolve())
    print(f"API-01 mutation case created at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
