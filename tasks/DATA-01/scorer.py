from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PASS_THRESHOLD = 0.9


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
        raise FileNotFoundError(f"Missing DATA-01 check config: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def markdown_headings(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.startswith("#")]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def add_cap(caps: list[float], config: dict[str, Any], cap_name: str) -> None:
    cap = config.get("score_caps", {}).get(cap_name)
    if isinstance(cap, (int, float)):
        caps.append(float(cap))


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def format_path(path: tuple[str, ...]) -> str:
    return ".".join(path) if path else "<root>"


def compare_value(
    actual: Any,
    expected: Any,
    *,
    tolerance: float = 0.0,
    normalize_strings: bool = False,
    path: tuple[str, ...] = (),
) -> tuple[bool, str]:
    if is_number(expected):
        if not is_number(actual):
            return False, f"{format_path(path)} expected number {expected!r} got {actual!r}"
        delta = abs(float(actual) - float(expected))
        if delta <= tolerance:
            return True, ""
        return False, f"{format_path(path)} expected {expected!r} got {actual!r}"

    if isinstance(expected, str):
        if not isinstance(actual, str):
            return False, f"{format_path(path)} expected string {expected!r} got {actual!r}"
        left = normalize_text(actual) if normalize_strings else actual
        right = normalize_text(expected) if normalize_strings else expected
        if left == right:
            return True, ""
        return False, f"{format_path(path)} expected {expected!r} got {actual!r}"

    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False, f"{format_path(path)} expected list got {actual!r}"
        if len(actual) != len(expected):
            return False, f"{format_path(path)} expected {len(expected)} items got {len(actual)}"
        for index, expected_item in enumerate(expected):
            passed, detail = compare_value(
                actual[index],
                expected_item,
                tolerance=tolerance,
                normalize_strings=normalize_strings,
                path=(*path, str(index)),
            )
            if not passed:
                return False, detail
        return True, ""

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False, f"{format_path(path)} expected object got {actual!r}"
        expected_keys = set(expected)
        actual_keys = set(actual)
        if expected_keys != actual_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            return False, f"{format_path(path)} missing={missing} extra={extra}"
        for key in sorted(expected):
            passed, detail = compare_value(
                actual[key],
                expected[key],
                tolerance=tolerance,
                normalize_strings=normalize_strings,
                path=(*path, key),
            )
            if not passed:
                return False, detail
        return True, ""

    if actual == expected:
        return True, ""
    return False, f"{format_path(path)} expected {expected!r} got {actual!r}"


def read_json_artifact(
    path: Path,
    *,
    check_name: str,
    invalid_cap: str,
    config: dict[str, Any],
) -> tuple[Any, list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        checks.append(check(check_name, False, 0.08, str(exc)))
        violations.append(f"invalid JSON: {path.name}")
        add_cap(caps, config, invalid_cap)
        return None, checks, violations, caps
    checks.append(check(check_name, isinstance(data, dict), 0.08))
    if not isinstance(data, dict):
        violations.append(f"JSON root is not an object: {path.name}")
        add_cap(caps, config, invalid_cap)
        return None, checks, violations, caps
    return data, checks, violations, caps


def score_artifact_inventory(
    config: dict[str, Any], artifacts_dir: Path
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    required = set(config.get("required_artifacts", []))
    allowed = required | set(config.get("allowed_extra_files", []))
    existing = {
        path.relative_to(artifacts_dir).as_posix()
        for path in artifacts_dir.rglob("*")
        if path.is_file()
    }

    for artifact in sorted(required):
        exists = artifact in existing
        checks.append(check(f"required_file:{artifact}", exists, 0.08))
        if not exists:
            violations.append(f"missing required file: {artifact}")
            add_cap(caps, config, f"missing_{Path(artifact).stem}")
            add_cap(caps, config, "missing_required_file")

    if not config.get("allow_extra_files", False):
        extra = sorted(existing - allowed)
        checks.append(check("no_extra_files", not extra, 0.06, ", ".join(extra)))
        if extra:
            violations.append(f"extra files present: {', '.join(extra)}")
            add_cap(caps, config, "extra_file")
    return checks, violations, caps


def score_metrics(
    config: dict[str, Any], metrics: dict[str, Any] | None
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    if metrics is None:
        return checks, violations, caps

    metric_config = config.get("metrics", {})
    required = metric_config.get("required", {})
    if not metric_config.get("allow_extra_keys", True):
        extra_metrics = sorted(set(metrics) - set(required))
        checks.append(check("metrics_no_extra_keys", not extra_metrics, 0.05, ", ".join(extra_metrics)))
        if extra_metrics:
            violations.append(f"extra metric keys present: {', '.join(extra_metrics)}")
            add_cap(caps, config, "extra_metric")

    forbidden = sorted(set(metric_config.get("forbidden_keys", [])) & set(metrics))
    checks.append(check("metrics_no_forbidden_keys", not forbidden, 0.05, ", ".join(forbidden)))
    if forbidden:
        violations.append(f"forbidden metric keys present: {', '.join(forbidden)}")
        add_cap(caps, config, "forbidden_metric")

    for key, rule in required.items():
        exists = key in metrics
        checks.append(check(f"metric_exists:{key}", exists, 0.03))
        if not exists:
            violations.append(f"missing required metric: {key}")
            add_cap(caps, config, "missing_metric")
            continue
        expected = rule.get("expected")
        tolerance = float(rule.get("tolerance", 0.0))
        normalize_strings = bool(rule.get("normalize_strings", False))
        passed, detail = compare_value(
            metrics[key],
            expected,
            tolerance=tolerance,
            normalize_strings=normalize_strings,
            path=(key,),
        )
        checks.append(check(f"metric_value:{key}", passed, 0.08, detail))
        if not passed:
            violations.append(f"metric mismatch: {key}")
            add_cap(caps, config, "wrong_metric")
    return checks, violations, caps


def score_report(
    config: dict[str, Any], report_path: Path
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    if not report_path.exists():
        return checks, violations, caps

    text = report_path.read_text(encoding="utf-8")
    normalized = normalize_text(text)
    report_config = config.get("report", {})

    headings = markdown_headings(text)
    required_sections = report_config.get("required_sections", [])
    if required_sections:
        position = 0
        for heading in headings:
            if position < len(required_sections) and heading == required_sections[position]:
                position += 1
        passed = position == len(required_sections)
        checks.append(check("report_required_sections_in_order", passed, 0.1, " > ".join(headings)))
        if not passed:
            violations.append("missing or misordered report section")
            add_cap(caps, config, "missing_report_section")

    for item in report_config.get("required_references", []):
        text_value = str(item.get("text", ""))
        passed = normalize_text(text_value) in normalized
        checks.append(check(f"report_reference:{item.get('metric', text_value)}", passed, 0.04, text_value))
        if not passed:
            violations.append(f"missing report reference: {item.get('metric', text_value)}")

    banned = [phrase for phrase in report_config.get("banned_phrases", []) if normalize_text(phrase) in normalized]
    checks.append(check("report_banned_phrases_absent", not banned, 0.05, ", ".join(banned)))
    if banned:
        violations.append(f"banned report phrases present: {', '.join(banned)}")
        add_cap(caps, config, "banned_phrase")

    unsupported = [
        phrase
        for phrase in report_config.get("unsupported_metric_phrases", [])
        if normalize_text(phrase) in normalized
    ]
    checks.append(check("report_no_unsupported_metrics", not unsupported, 0.05, ", ".join(unsupported)))
    if unsupported:
        violations.append(f"unsupported report metrics present: {', '.join(unsupported)}")
        add_cap(caps, config, "unsupported_metric")

    if "max_words" in report_config:
        count = word_count(text)
        maximum = int(report_config["max_words"])
        checks.append(check("report_max_words", count <= maximum, 0.04, f"got={count}"))
    return checks, violations, caps


def score_chart_spec(
    config: dict[str, Any], chart_spec: dict[str, Any] | None
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    if chart_spec is None:
        return checks, violations, caps

    chart_config = config.get("chart_spec", {})
    expected = chart_config.get("expected", {})
    tolerance = float(chart_config.get("tolerance", 0.0))
    checks_to_run = {
        "title": ("chart_title", 0.05),
        "x_axis": ("chart_x_axis", 0.04),
        "y_axis": ("chart_y_axis", 0.04),
        "series": ("chart_series", 0.12),
    }
    for key, (check_name, points) in checks_to_run.items():
        if key not in expected:
            continue
        passed, detail = compare_value(
            chart_spec.get(key),
            expected[key],
            tolerance=tolerance,
            normalize_strings=False,
            path=(key,),
        )
        checks.append(check(check_name, passed, points, detail))
        if not passed:
            violations.append(f"chart spec mismatch: {key}")
            if key == "series":
                add_cap(caps, config, "missing_chart_series")
            else:
                add_cap(caps, config, "wrong_chart_spec")
    return checks, violations, caps


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    config = load_config(fixture_dir)
    checks, violations, caps = score_artifact_inventory(config, artifacts_dir)

    metrics = None
    metrics_path = artifacts_dir / "metrics.json"
    if metrics_path.exists():
        metrics, file_checks, file_violations, file_caps = read_json_artifact(
            metrics_path,
            check_name="metrics_json_valid",
            invalid_cap="invalid_metrics_json",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    metric_checks, metric_violations, metric_caps = score_metrics(config, metrics)
    checks.extend(metric_checks)
    violations.extend(metric_violations)
    caps.extend(metric_caps)

    report_checks, report_violations, report_caps = score_report(config, artifacts_dir / "report.md")
    checks.extend(report_checks)
    violations.extend(report_violations)
    caps.extend(report_caps)

    chart_spec = None
    chart_path = artifacts_dir / "chart_spec.json"
    if chart_path.exists():
        chart_spec, chart_checks, chart_violations, chart_caps = read_json_artifact(
            chart_path,
            check_name="chart_spec_json_valid",
            invalid_cap="invalid_chart_json",
            config=config,
        )
        checks.extend(chart_checks)
        violations.extend(chart_violations)
        caps.extend(chart_caps)
    chart_score_checks, chart_score_violations, chart_score_caps = score_chart_spec(config, chart_spec)
    checks.extend(chart_score_checks)
    violations.extend(chart_score_violations)
    caps.extend(chart_score_caps)

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
