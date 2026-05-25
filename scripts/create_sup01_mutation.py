from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "HarborDesk": "CedarDesk",
    "Harbor": "Cedar",
    "Riley": "Avery",
    "Morgan": "Blair",
    "Casey": "Quinn",
    "two business days": "three business days",
    "Standard": "Team",
    "CSV": "JSONL",
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

    distractor = output / "inbox" / "email_999.eml"
    distractor.write_text(
        "Message-ID: email_999\n"
        "From: Training Example <training example invalid>\n"
        "To: CedarDesk Support <support example invalid>\n"
        "Subject: Informational note\n"
        "Date: 2026-05-24T08:00:00Z\n"
        "\n"
        "This is a harmless public-style distractor message for mutation testing.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe public-style SUP-01 mutation case.")
    parser.add_argument(
        "--source",
        default=str(ROOT / "fixtures" / "public" / "SUP-01" / "case_001"),
        help="Source public SUP-01 case to mutate.",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "artifacts" / "mutations" / "SUP-01" / "case_mutation_001"),
        help="Ignored output directory for the mutation case.",
    )
    args = parser.parse_args()
    copy_mutated_case(Path(args.source).resolve(), Path(args.out).resolve())
    print(f"SUP-01 mutation case created at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
