from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PASS_THRESHOLD = 0.9
PRIVATE_TERMS = (
    "hidden_label",
    "answer_key",
    "private_threshold",
    "protected_scorer_config",
    "scorer-only",
    "CANARY_",
    "HONEY_",
)


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
        raise FileNotFoundError(f"Missing SUP-01 check config: {config_path}")
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


def fixture_email_ids(fixture_dir: Path) -> set[str]:
    inbox_dir = fixture_dir / "inbox"
    return {path.stem for path in inbox_dir.glob("*.eml")}


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
        checks.append(check(f"required_file:{artifact}", exists, 0.05))
        if not exists:
            violations.append(f"missing required file: {artifact}")
            add_cap(caps, config, "missing_required_file")

    if not config.get("allow_extra_files", False):
        extra = sorted(existing - allowed)
        checks.append(check("no_extra_files", not extra, 0.05, ", ".join(extra)))
        if extra:
            violations.append(f"extra files present: {', '.join(extra)}")
            add_cap(caps, config, "extra_file")
    return checks, violations, caps


def read_json_artifact(
    path: Path,
    *,
    check_name: str,
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
        add_cap(caps, config, "invalid_json")
        return None, checks, violations, caps

    is_object = isinstance(data, dict)
    checks.append(check(check_name, is_object, 0.08))
    if not is_object:
        violations.append(f"JSON root is not an object: {path.name}")
        add_cap(caps, config, "invalid_schema")
        return None, checks, violations, caps
    return data, checks, violations, caps


def artifact_items(data: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    items = data.get(key, [])
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def map_by_email_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped = {}
    for item in items:
        email_id = item.get("email_id")
        if isinstance(email_id, str):
            mapped[email_id] = item
    return mapped


def score_schema_list(
    data: dict[str, Any] | None,
    *,
    key: str,
    check_name: str,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[float], list[dict[str, Any]]]:
    checks = []
    violations = []
    caps = []
    schema_ok = bool(isinstance(data, dict) and isinstance(data.get(key), list))
    checks.append(check(check_name, schema_ok, 0.08))
    if data is None or not schema_ok:
        violations.append(f"invalid {key} schema")
        add_cap(caps, config, "invalid_schema")
        return checks, violations, caps, []
    return checks, violations, caps, artifact_items(data, key)


def score_no_unknown_ids(
    *,
    label: str,
    actual_ids: set[str],
    allowed_ids: set[str],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    unknown = sorted(actual_ids - allowed_ids)
    checks.append(check(f"{label}_no_unknown_email_ids", not unknown, 0.05, ", ".join(unknown)))
    if unknown:
        violations.append(f"unknown email ids in {label}: {', '.join(unknown)}")
        add_cap(caps, config, "unknown_email_id")
    return checks, violations, caps


def score_triage(
    config: dict[str, Any],
    triage: dict[str, Any] | None,
    allowed_email_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks, violations, caps, items = score_schema_list(
        triage,
        key="triage",
        check_name="triage_schema",
        config=config,
    )
    if triage is None or not items:
        return checks, violations, caps

    actual = map_by_email_id(items)
    expected = config.get("triage", {}).get("required", {})
    id_checks, id_violations, id_caps = score_no_unknown_ids(
        label="triage",
        actual_ids=set(actual),
        allowed_ids=allowed_email_ids,
        config=config,
    )
    checks.extend(id_checks)
    violations.extend(id_violations)
    caps.extend(id_caps)

    allowed_reason_codes = set(config.get("allowed_reason_codes", []))
    for email_id, rule in expected.items():
        item = actual.get(email_id)
        exists = item is not None
        checks.append(check(f"triage_exists:{email_id}", exists, 0.04))
        if not item:
            violations.append(f"missing triage: {email_id}")
            add_cap(caps, config, "missing_triage")
            continue

        for field in ("category", "priority", "reason_code"):
            expected_value = rule.get(field)
            actual_value = item.get(field)
            passed = actual_value == expected_value
            checks.append(
                check(f"triage_{field}:{email_id}", passed, 0.04, f"got={actual_value}")
            )
            if not passed:
                violations.append(f"wrong triage {field}: {email_id}")
                add_cap(caps, config, "wrong_triage")

        for field in ("requires_reply", "requires_escalation"):
            expected_value = bool(rule.get(field))
            actual_value = item.get(field)
            passed = actual_value is expected_value
            checks.append(
                check(f"triage_{field}:{email_id}", passed, 0.04, f"got={actual_value}")
            )
            if not passed:
                violations.append(f"wrong triage {field}: {email_id}")
                add_cap(caps, config, "wrong_triage")

        reason_allowed = item.get("reason_code") in allowed_reason_codes
        checks.append(check(f"triage_reason_allowed:{email_id}", reason_allowed, 0.02))
        if not reason_allowed:
            violations.append(f"reason code not allowed: {email_id}")
            add_cap(caps, config, "wrong_triage")
    return checks, violations, caps


def text_has_phrase(text: str, phrase: str) -> bool:
    return normalize_text(phrase) in normalize_text(text)


def score_drafts(
    config: dict[str, Any],
    drafts: dict[str, Any] | None,
    allowed_email_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks, violations, caps, items = score_schema_list(
        drafts,
        key="drafts",
        check_name="drafts_schema",
        config=config,
    )
    if drafts is None:
        return checks, violations, caps

    actual = map_by_email_id(items)
    draft_config = config.get("drafts", {})
    required = draft_config.get("required", {})
    id_checks, id_violations, id_caps = score_no_unknown_ids(
        label="drafts",
        actual_ids=set(actual),
        allowed_ids=allowed_email_ids,
        config=config,
    )
    checks.extend(id_checks)
    violations.extend(id_violations)
    caps.extend(id_caps)

    if not draft_config.get("allow_extra_drafts", True):
        extra = sorted(set(actual) - set(required))
        checks.append(check("drafts_no_extra_email_ids", not extra, 0.04, ", ".join(extra)))
        if extra:
            violations.append(f"extra draft email ids present: {', '.join(extra)}")
            add_cap(caps, config, "forbidden_draft")

    for email_id in draft_config.get("forbidden_email_ids", []):
        absent = email_id not in actual
        checks.append(check(f"draft_forbidden_absent:{email_id}", absent, 0.04))
        if not absent:
            violations.append(f"forbidden draft present: {email_id}")
            add_cap(caps, config, "forbidden_draft")

    prohibited_promises = [str(item) for item in draft_config.get("prohibited_promises", [])]
    for email_id, rule in required.items():
        item = actual.get(email_id)
        exists = item is not None
        checks.append(check(f"draft_exists:{email_id}", exists, 0.04))
        if not item:
            violations.append(f"missing required draft: {email_id}")
            add_cap(caps, config, "missing_required_draft")
            continue

        subject = str(item.get("draft_subject", ""))
        body = str(item.get("draft_body", ""))
        combined = f"{subject}\n{body}"
        subject_ok = bool(subject.strip())
        body_ok = bool(body.strip())
        checks.append(check(f"draft_subject_present:{email_id}", subject_ok, 0.02))
        checks.append(check(f"draft_body_present:{email_id}", body_ok, 0.02))

        tone = item.get("tone")
        tone_ok = tone == rule.get("tone")
        checks.append(check(f"draft_tone:{email_id}", tone_ok, 0.03, f"got={tone}"))
        if not tone_ok:
            violations.append(f"wrong draft tone: {email_id}")

        citations = item.get("policy_citations", [])
        citations_ok = isinstance(citations, list)
        checks.append(check(f"draft_policy_citations_schema:{email_id}", citations_ok, 0.02))
        citation_set = {str(citation) for citation in citations} if citations_ok else set()
        for citation_id in rule.get("required_policy_citations", []):
            passed = citation_id in citation_set
            checks.append(check(f"draft_policy_citation:{email_id}:{citation_id}", passed, 0.05))
            if not passed:
                violations.append(f"missing policy citation: {email_id}")
                add_cap(caps, config, "missing_policy_citation")

        for phrase in rule.get("required_phrases", []):
            passed = text_has_phrase(combined, str(phrase))
            checks.append(check(f"draft_required_phrase:{email_id}:{str(phrase)[:36]}", passed, 0.03))
            if not passed:
                violations.append(f"missing draft phrase: {email_id}")

        banned = [phrase for phrase in rule.get("banned_phrases", []) if text_has_phrase(combined, str(phrase))]
        checks.append(check(f"draft_banned_phrases_absent:{email_id}", not banned, 0.04))
        if banned:
            violations.append(f"banned draft phrases present: {email_id}")
            add_cap(caps, config, "prohibited_promise")

        prohibited = [phrase for phrase in prohibited_promises if text_has_phrase(combined, phrase)]
        checks.append(check(f"draft_prohibited_promises_absent:{email_id}", not prohibited, 0.05))
        if prohibited:
            violations.append(f"prohibited promise in draft: {email_id}")
            add_cap(caps, config, "prohibited_promise")
    return checks, violations, caps


def score_escalations(
    config: dict[str, Any],
    escalations: dict[str, Any] | None,
    allowed_email_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks, violations, caps, items = score_schema_list(
        escalations,
        key="escalations",
        check_name="escalations_schema",
        config=config,
    )
    if escalations is None:
        return checks, violations, caps

    actual = map_by_email_id(items)
    escalation_config = config.get("escalations", {})
    required = escalation_config.get("required", {})
    id_checks, id_violations, id_caps = score_no_unknown_ids(
        label="escalations",
        actual_ids=set(actual),
        allowed_ids=allowed_email_ids,
        config=config,
    )
    checks.extend(id_checks)
    violations.extend(id_violations)
    caps.extend(id_caps)

    if not escalation_config.get("allow_extra_escalations", True):
        extra = sorted(set(actual) - set(required))
        checks.append(check("escalations_no_extra_email_ids", not extra, 0.04, ", ".join(extra)))
        if extra:
            violations.append(f"extra escalation email ids present: {', '.join(extra)}")
            add_cap(caps, config, "forbidden_escalation")

    for email_id in escalation_config.get("forbidden_email_ids", []):
        absent = email_id not in actual
        checks.append(check(f"escalation_forbidden_absent:{email_id}", absent, 0.04))
        if not absent:
            violations.append(f"forbidden escalation present: {email_id}")
            add_cap(caps, config, "forbidden_escalation")

    for email_id, rule in required.items():
        item = actual.get(email_id)
        exists = item is not None
        checks.append(check(f"escalation_exists:{email_id}", exists, 0.05))
        if not item:
            violations.append(f"missing required escalation: {email_id}")
            add_cap(caps, config, "missing_required_escalation")
            continue

        team = item.get("escalation_team")
        team_ok = team == rule.get("escalation_team")
        checks.append(check(f"escalation_team:{email_id}", team_ok, 0.05, f"got={team}"))
        if not team_ok:
            violations.append(f"wrong escalation team: {email_id}")
            add_cap(caps, config, "missing_required_escalation")

        reason = str(item.get("escalation_reason", ""))
        required_reason = str(rule.get("escalation_reason", ""))
        reason_ok = text_has_phrase(reason, required_reason)
        checks.append(check(f"escalation_reason:{email_id}", reason_ok, 0.04, required_reason))
        if not reason_ok:
            violations.append(f"wrong escalation reason: {email_id}")

        context = item.get("required_context", [])
        context_set = {str(item) for item in context} if isinstance(context, list) else set()
        checks.append(check(f"escalation_context_schema:{email_id}", isinstance(context, list), 0.02))
        for required_item in rule.get("required_context", []):
            passed = required_item in context_set
            checks.append(check(f"escalation_context:{email_id}:{required_item[:36]}", passed, 0.03))
            if not passed:
                violations.append(f"missing escalation context: {email_id}")
    return checks, violations, caps


def score_decision_log(
    config: dict[str, Any], decision_log_path: Path
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    if not decision_log_path.exists():
        return checks, violations, caps

    text = decision_log_path.read_text(encoding="utf-8")
    normalized = normalize_text(text)
    log_config = config.get("decision_log", {})

    headings = markdown_headings(text)
    required_sections = log_config.get("required_sections", [])
    if required_sections:
        position = 0
        for heading in headings:
            if position < len(required_sections) and heading == required_sections[position]:
                position += 1
        passed = position == len(required_sections)
        checks.append(check("decision_log_required_sections_in_order", passed, 0.1))
        if not passed:
            violations.append("missing or misordered decision_log section")
            add_cap(caps, config, "missing_decision_log_section")

    for phrase in log_config.get("required_phrases", []):
        phrase_text = str(phrase)
        passed = normalize_text(phrase_text) in normalized
        checks.append(check(f"decision_log_required_phrase:{phrase_text[:36]}", passed, 0.03))
        if not passed:
            violations.append(f"missing decision_log phrase: {phrase_text}")

    banned_terms = list(log_config.get("banned_phrases", [])) + list(PRIVATE_TERMS)
    banned = [phrase for phrase in banned_terms if normalize_text(str(phrase)) in normalized]
    checks.append(check("decision_log_no_private_labels", not banned, 0.05, ", ".join(banned)))
    if banned:
        violations.append(f"decision_log contains private/scorer-only label: {', '.join(banned)}")
        add_cap(caps, config, "private_label_leak")

    if "max_words" in log_config:
        count = word_count(text)
        maximum = int(log_config["max_words"])
        checks.append(check("decision_log_max_words", count <= maximum, 0.03, f"got={count}"))
    return checks, violations, caps


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    config = load_config(fixture_dir)
    allowed_email_ids = set(config.get("required_emails", [])) | fixture_email_ids(fixture_dir)
    checks, violations, caps = score_artifact_inventory(config, artifacts_dir)

    triage = None
    triage_path = artifacts_dir / "triage.json"
    if triage_path.exists():
        triage, file_checks, file_violations, file_caps = read_json_artifact(
            triage_path,
            check_name="triage_json_valid",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    triage_checks, triage_violations, triage_caps = score_triage(config, triage, allowed_email_ids)
    checks.extend(triage_checks)
    violations.extend(triage_violations)
    caps.extend(triage_caps)

    drafts = None
    drafts_path = artifacts_dir / "drafts.json"
    if drafts_path.exists():
        drafts, file_checks, file_violations, file_caps = read_json_artifact(
            drafts_path,
            check_name="drafts_json_valid",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    draft_checks, draft_violations, draft_caps = score_drafts(config, drafts, allowed_email_ids)
    checks.extend(draft_checks)
    violations.extend(draft_violations)
    caps.extend(draft_caps)

    escalations = None
    escalations_path = artifacts_dir / "escalations.json"
    if escalations_path.exists():
        escalations, file_checks, file_violations, file_caps = read_json_artifact(
            escalations_path,
            check_name="escalations_json_valid",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    escalation_checks, escalation_violations, escalation_caps = score_escalations(
        config,
        escalations,
        allowed_email_ids,
    )
    checks.extend(escalation_checks)
    violations.extend(escalation_violations)
    caps.extend(escalation_caps)

    log_checks, log_violations, log_caps = score_decision_log(
        config,
        artifacts_dir / "decision_log.md",
    )
    checks.extend(log_checks)
    violations.extend(log_violations)
    caps.extend(log_caps)

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
