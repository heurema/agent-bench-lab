from __future__ import annotations

import re
import subprocess
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

SKIP_CONTENT_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "private",
    "runs",
    "traces",
    "artifacts",
    "build",
    "dist",
}
SKIP_WALK_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist"}
SKIP_WALK_PREFIXES = {
    "runs/",
    "traces/",
    "artifacts/",
    "examples/artifacts/",
    "reports/generated/",
}
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".csv", ".html", ".env", ".toml", ".yaml", ".yml", ".gitignore", ""}

DENIED_PATH_PREFIXES = {
    "runs/",
    "traces/",
    "private/",
    "fixtures/private/",
    "examples/artifacts/",
    "artifacts/",
    "reports/generated/",
}
DENIED_PATH_PARTS = {"runs", "traces", "private", "artifacts"}
DENIED_PATH_TERMS = {
    ".env",
    ".env.",
    "secret",
    "token",
    "key",
    "answer_key",
    "hidden_label",
    "customer_private",
}


def should_skip_content(path: Path) -> bool:
    return any(part in SKIP_CONTENT_DIRS for part in path.parts)


def _relative_path(path: Path) -> str:
    return path.as_posix().removeprefix("./")


def denylisted_path_reason(path: str) -> str | None:
    normalized = _relative_path(Path(path)).lower()
    parts = normalized.split("/")
    for prefix in DENIED_PATH_PREFIXES:
        if normalized.startswith(prefix):
            return f"denied path prefix {prefix}"
    for part in parts:
        if part in DENIED_PATH_PARTS:
            return f"denied path component {part}"
        if part == ".env" or part.startswith(".env."):
            return "denied env file path"
    for term in DENIED_PATH_TERMS:
        if term in normalized:
            return f"denied path term {term}"
    return None


def git_tracked_paths(root: Path) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def walk_source_paths(root: Path) -> list[str]:
    paths = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        rel_name = rel.as_posix()
        if any(part in SKIP_WALK_DIRS for part in rel.parts):
            continue
        if any(rel_name.startswith(prefix) for prefix in SKIP_WALK_PREFIXES):
            continue
        if path.is_file():
            paths.append(rel_name)
    return sorted(paths)


def scan_paths(root: Path, paths: list[str]) -> list[str]:
    findings = []
    for rel_path in sorted(paths):
        reason = denylisted_path_reason(rel_path)
        if reason:
            findings.append(f"{rel_path}: {reason}")
        path = root / rel_path
        if not path.is_file() or should_skip_content(path):
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


def scan(root: Path) -> list[str]:
    tracked_paths = git_tracked_paths(root)
    paths = tracked_paths if tracked_paths is not None else walk_source_paths(root)
    return scan_paths(root, paths)


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    findings = scan(root)
    if findings:
        print("Potential public-release issues:")
        for item in findings:
            print(f"- {item}")
        raise SystemExit(1)
    print("No obvious public-release issues found.")
