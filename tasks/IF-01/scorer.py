from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PASS_THRESHOLD = 0.85


def check(name: str, passed: bool, points: float, detail: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "points": points if passed else 0.0,
        "max_points": points,
        "detail": detail,
    }


def load_config(fixture_dir: Path) -> dict[str, Any]:
    config_path = fixture_dir / "check_config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing IF-01 check config: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def markdown_headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.startswith("#")]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def is_ordered(values: list[str], expected: list[str]) -> bool:
    position = 0
    for item in values:
        if position < len(expected) and item == expected[position]:
            position += 1
    return position == len(expected)


def add_cap(caps: list[float], config: dict[str, Any], cap_name: str) -> None:
    cap = config.get("score_caps", {}).get(cap_name)
    if isinstance(cap, (int, float)):
        caps.append(float(cap))


def score_extra_files(config: dict[str, Any], artifacts_dir: Path) -> tuple[list[dict], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    required_files = {item["path"] for item in config.get("required_files", [])}
    forbidden_files = set(config.get("forbidden_files", []))
    existing_files = {
        path.relative_to(artifacts_dir).as_posix()
        for path in artifacts_dir.rglob("*")
        if path.is_file()
    }
    forbidden_present = sorted(existing_files & forbidden_files)
    checks.append(
        check(
            "forbidden_files_absent",
            not forbidden_present,
            0.08,
            ", ".join(forbidden_present),
        )
    )
    if forbidden_present:
        violations.append(f"forbidden files present: {', '.join(forbidden_present)}")
        add_cap(caps, config, "forbidden_file")

    if not config.get("allow_extra_files", False):
        allowed = required_files | forbidden_files
        extra_files = sorted(existing_files - allowed)
        checks.append(check("no_extra_files", not extra_files, 0.08, ", ".join(extra_files)))
        if extra_files:
            violations.append(f"extra files present: {', '.join(extra_files)}")
            add_cap(caps, config, "extra_file")
    return checks, violations, caps


def score_markdown_file(path: Path, file_config: dict[str, Any], root_config: dict[str, Any]) -> tuple[list[dict], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    normalized = normalize_text(text)
    rules = file_config.get("markdown", {})

    first_line = rules.get("first_line")
    if first_line is not None:
        checks.append(check("first_line_exact", bool(lines) and lines[0] == first_line, 0.08))

    required_phrases = rules.get("required_phrases", [])
    for phrase in required_phrases:
        checks.append(
            check(
                f"required_phrase:{phrase}",
                normalize_text(str(phrase)) in normalized,
                0.04,
            )
        )

    headings = markdown_headings(text)
    expected_order = rules.get("heading_order", [])
    if expected_order:
        checks.append(
            check(
                "heading_order",
                is_ordered(headings, expected_order),
                0.12,
                " > ".join(headings),
            )
        )

    forbidden_headings = set(rules.get("forbidden_headings", []))
    present_forbidden = sorted(item for item in headings if item in forbidden_headings)
    checks.append(check("forbidden_headings_absent", not present_forbidden, 0.08, ", ".join(present_forbidden)))
    if present_forbidden:
        violations.append(f"forbidden headings present: {', '.join(present_forbidden)}")
        add_cap(caps, root_config, "forbidden_section")

    banned_phrases = rules.get("banned_phrases", [])
    present_banned = [
        phrase for phrase in banned_phrases if normalize_text(str(phrase)) in normalized
    ]
    checks.append(check("banned_phrases_absent", not present_banned, 0.08, ", ".join(present_banned)))
    if present_banned:
        violations.append(f"banned phrases present: {', '.join(present_banned)}")
        add_cap(caps, root_config, "banned_phrase")

    if "exact_bullet_count" in rules:
        bullet_count = sum(1 for line in lines if line.startswith("- "))
        expected = int(rules["exact_bullet_count"])
        checks.append(check("exact_bullet_count", bullet_count == expected, 0.08, f"got={bullet_count}"))
    if "min_words" in rules:
        count = word_count(text)
        checks.append(check("min_words", count >= int(rules["min_words"]), 0.04, f"got={count}"))
    if "max_words" in rules:
        count = word_count(text)
        checks.append(check("max_words", count <= int(rules["max_words"]), 0.04, f"got={count}"))
    if "min_lines" in rules:
        checks.append(check("min_lines", len(lines) >= int(rules["min_lines"]), 0.03, f"got={len(lines)}"))
    if "max_lines" in rules:
        checks.append(check("max_lines", len(lines) <= int(rules["max_lines"]), 0.03, f"got={len(lines)}"))
    if "max_headings" in rules:
        checks.append(
            check("max_headings", len(headings) <= int(rules["max_headings"]), 0.04, f"got={len(headings)}")
        )
    return checks, violations, caps


def score_json_file(path: Path, file_config: dict[str, Any], root_config: dict[str, Any]) -> tuple[list[dict], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(check("json_valid", False, 0.18, str(exc)))
        violations.append("invalid JSON")
        add_cap(caps, root_config, "invalid_json")
        return checks, violations, caps

    checks.append(check("json_valid", isinstance(data, dict), 0.18))
    if not isinstance(data, dict):
        violations.append("JSON root is not an object")
        add_cap(caps, root_config, "invalid_json")
        return checks, violations, caps

    rules = file_config.get("json", {})
    for field, expected in rules.get("required_fields", {}).items():
        checks.append(
            check(
                f"required_field:{field}",
                data.get(field) == expected,
                0.06,
                f"expected={expected!r} got={data.get(field)!r}",
            )
        )
    forbidden_fields = sorted(set(rules.get("forbidden_fields", [])) & set(data.keys()))
    checks.append(check("forbidden_fields_absent", not forbidden_fields, 0.08, ", ".join(forbidden_fields)))
    if forbidden_fields:
        violations.append(f"forbidden fields present: {', '.join(forbidden_fields)}")
        add_cap(caps, root_config, "forbidden_field")

    for field, expected_items in rules.get("required_array_items", {}).items():
        actual = data.get(field)
        passed = isinstance(actual, list) and all(item in actual for item in expected_items)
        checks.append(check(f"required_array_items:{field}", passed, 0.08, f"got={actual!r}"))
    if "max_top_level_fields" in rules:
        maximum = int(rules["max_top_level_fields"])
        checks.append(check("max_top_level_fields", len(data) <= maximum, 0.04, f"got={len(data)}"))
    return checks, violations, caps


def score_required_files(config: dict[str, Any], artifacts_dir: Path) -> tuple[list[dict], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    for file_config in config.get("required_files", []):
        path = artifacts_dir / file_config["path"]
        exists = path.exists()
        checks.append(check(f"required_file:{file_config['path']}", exists, 0.12))
        if not exists:
            violations.append(f"missing required file: {file_config['path']}")
            add_cap(caps, config, "missing_required_file")
            continue
        file_format = file_config.get("format")
        if file_format == "markdown":
            file_checks, file_violations, file_caps = score_markdown_file(path, file_config, config)
        elif file_format == "json":
            file_checks, file_violations, file_caps = score_json_file(path, file_config, config)
        else:
            file_checks, file_violations, file_caps = [], [], []
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    return checks, violations, caps


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    config = load_config(fixture_dir)
    checks, violations, caps = score_extra_files(config, artifacts_dir)
    file_checks, file_violations, file_caps = score_required_files(config, artifacts_dir)
    checks.extend(file_checks)
    violations.extend(file_violations)
    caps.extend(file_caps)

    max_points = sum(float(item["max_points"]) for item in checks)
    earned_points = sum(float(item["points"]) for item in checks)
    score_value = earned_points / max_points if max_points else 0.0
    if caps:
        score_value = min(score_value, min(caps))
    score_value = round(score_value, 4)
    return {
        "score": score_value,
        "success": score_value >= PASS_THRESHOLD and not violations,
        "pass_threshold": PASS_THRESHOLD,
        "checks": checks,
        "policy_violations": violations,
        "notes": config.get("description"),
    }
