from __future__ import annotations

import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]+"),
]

ALLOWLIST = {
    "sk-public-test-DO-NOT-LEAK",
}

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "private", "runs", "traces", "artifacts", "build", "dist"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".csv", ".html", ".env", ".toml", ".yaml", ".yml", ".gitignore", ""}


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def scan(root: Path) -> list[str]:
    findings = []
    for path in root.rglob("*"):
        if path.is_dir() or should_skip(path):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name != ".gitignore":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            for match in pattern.findall(text):
                value = match if isinstance(match, str) else "".join(match)
                if value in ALLOWLIST:
                    continue
                findings.append(f"{path}: possible secret pattern {pattern.pattern}")
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
            # Allow synthetic documentation examples only if explicitly marked later.
            findings.append(f"{path}: possible email address")
    return findings


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    findings = scan(root)
    if findings:
        print("Potential public-release issues:")
        for item in findings:
            print(f"- {item}")
        raise SystemExit(1)
    print("No obvious public-release issues found.")
