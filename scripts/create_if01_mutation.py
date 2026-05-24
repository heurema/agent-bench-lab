from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "if01_mutations" / "case_mutation_001"


SPEC = """# IF-01 Generated Public-Style Mutation

Create `artifact.md`.

Requirements:

1. The Markdown headings must appear in this exact order:
   - `# Mutation Brief`
   - `## Acceptance`
   - `## Scope`
   - `## Out of Scope`
2. Mention `Harbor Relay`.
3. Mention `paired comparison`.
4. Mention `private holdout`.
5. Use 30 to 70 words total.
6. Use at most 10 lines.
7. Do not include `## Internal Notes`.
8. Do not include the phrase `benchmark answer`.
9. Do not create any other files.
"""


CHECK_CONFIG = {
    "case_id": "case_mutation_001",
    "description": (
        "Generated public-style IF-01 mutation with changed entity name, reordered sections, "
        "and changed numeric limits."
    ),
    "allow_extra_files": False,
    "forbidden_files": ["notes.md", "scratch.txt"],
    "score_caps": {
        "missing_required_file": 0.0,
        "banned_phrase": 0.0,
        "forbidden_section": 0.6,
        "forbidden_file": 0.6,
        "extra_file": 0.75,
    },
    "required_files": [
        {
            "path": "artifact.md",
            "format": "markdown",
            "markdown": {
                "first_line": "# Mutation Brief",
                "heading_order": [
                    "# Mutation Brief",
                    "## Acceptance",
                    "## Scope",
                    "## Out of Scope",
                ],
                "required_phrases": [
                    "Harbor Relay",
                    "paired comparison",
                    "private holdout",
                ],
                "banned_phrases": ["benchmark answer"],
                "forbidden_headings": [
                    "## Internal Notes",
                    "## Hidden Answers",
                ],
                "min_words": 30,
                "max_words": 70,
                "max_lines": 10,
            },
        }
    ],
}


def create_mutation(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "spec.md").write_text(SPEC, encoding="utf-8")
    (output_dir / "check_config.json").write_text(
        json.dumps(CHECK_CONFIG, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a safe public-style IF-01 mutation case")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output_dir = create_mutation(args.out)
    print(f"IF-01 mutation case created at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
