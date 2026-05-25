from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "Northstar": "Helio",
    "Basic": "Starter",
    "email support": "portal support",
    "two business days": "three business days",
    "CSV": "JSONL",
    "14 days": "10 days",
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

    distractor = output / "corpus" / "extra_distractor.md"
    distractor.write_text(
        "---\n"
        "doc_id: extra_distractor\n"
        "title: Helio Draft Partner Memo\n"
        "status: draft\n"
        "---\n\n"
        "A draft partner memo mentions a possible premium hotline.\n"
        "It is not approved policy for the mutated public-style case.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe public-style DOC-01 mutation case.")
    parser.add_argument(
        "--source",
        default=str(ROOT / "fixtures" / "public" / "DOC-01" / "case_001"),
        help="Source public DOC-01 case to mutate.",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "artifacts" / "mutations" / "DOC-01" / "case_mutation_001"),
        help="Ignored output directory for the mutation case.",
    )
    args = parser.parse_args()
    copy_mutated_case(Path(args.source).resolve(), Path(args.out).resolve())
    print(f"DOC-01 mutation case created at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
