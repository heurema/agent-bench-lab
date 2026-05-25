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
        raise FileNotFoundError(f"Missing DOC-01 check config: {config_path}")
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


def load_corpus(fixture_dir: Path) -> dict[str, str]:
    corpus_dir = fixture_dir / "corpus"
    docs = {}
    for path in sorted(corpus_dir.glob("*.md")):
        docs[path.stem] = path.read_text(encoding="utf-8")
    return docs


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
        checks.append(check(f"required_file:{artifact}", exists, 0.06))
        if not exists:
            violations.append(f"missing required file: {artifact}")
            add_cap(caps, config, f"missing_{Path(artifact).stem}")
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


def citation_items(citations: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(citations, dict):
        return []
    items = citations.get("citations", [])
    return items if isinstance(items, list) else []


def claim_items(claims: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(claims, dict):
        return []
    items = claims.get("claims", [])
    return items if isinstance(items, list) else []


def score_citations(
    config: dict[str, Any],
    citations: dict[str, Any] | None,
    corpus: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str], list[float], dict[str, dict[str, Any]]]:
    checks = []
    violations = []
    caps = []
    citation_map = {}
    items = citation_items(citations)
    schema_ok = bool(isinstance(citations, dict) and isinstance(citations.get("citations"), list))
    checks.append(check("citations_schema", schema_ok, 0.08))
    if citations is None or not schema_ok:
        violations.append("invalid citations schema")
        add_cap(caps, config, "invalid_citations_schema")
        return checks, violations, caps, citation_map

    stale_source_ids = set(config.get("stale_source_ids", []))
    seen_ids = set()
    for index, item in enumerate(items):
        item_ok = isinstance(item, dict)
        citation_id = str(item.get("id", "")) if item_ok else ""
        doc_id = str(item.get("doc_id", "")) if item_ok else ""
        quote = str(item.get("quote", "")) if item_ok else ""
        item_name = citation_id or f"citation_{index + 1}"

        unique_id = bool(citation_id and citation_id not in seen_ids)
        checks.append(check(f"citation_id_unique:{item_name}", item_ok and unique_id, 0.02))
        if citation_id:
            seen_ids.add(citation_id)
            citation_map[citation_id] = item

        doc_exists = doc_id in corpus
        checks.append(check(f"citation_doc_exists:{item_name}", doc_exists, 0.04, doc_id))
        if not doc_exists:
            violations.append(f"citation references unknown document: {doc_id}")
            add_cap(caps, config, "unknown_citation_doc")
            continue

        quote_matches = bool(quote and normalize_text(quote) in normalize_text(corpus[doc_id]))
        checks.append(check(f"citation_quote_matches:{item_name}", quote_matches, 0.06, quote[:120]))
        if not quote_matches:
            violations.append(f"citation quote not found in source: {item_name}")
            add_cap(caps, config, "bad_citation_quote")

        stale = doc_id in stale_source_ids
        checks.append(check(f"citation_not_stale:{item_name}", not stale, 0.04, doc_id))
        if stale:
            violations.append(f"stale source cited: {doc_id}")
            add_cap(caps, config, "stale_source")
    return checks, violations, caps, citation_map


def claim_has_required_text(actual_text: str, required_text: str) -> bool:
    return normalize_text(required_text) in normalize_text(actual_text)


def claim_citations_for(claim: dict[str, Any], citation_map: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    ids = claim.get("citation_ids", [])
    if not isinstance(ids, list):
        return []
    return [citation_map[item] for item in ids if isinstance(item, str) and item in citation_map]


def score_claims(
    config: dict[str, Any],
    claims: dict[str, Any] | None,
    citation_map: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    items = claim_items(claims)
    schema_ok = bool(isinstance(claims, dict) and isinstance(claims.get("claims"), list))
    checks.append(check("claims_schema", schema_ok, 0.08))
    if claims is None or not schema_ok:
        violations.append("invalid claims schema")
        add_cap(caps, config, "invalid_claims_schema")
        return checks, violations, caps

    claim_config = config.get("claims", {})
    required = claim_config.get("required", {})
    actual = {
        str(item.get("id")): item
        for item in items
        if isinstance(item, dict) and item.get("id") is not None
    }

    if not claim_config.get("allow_extra_claims", True):
        extra = sorted(set(actual) - set(required))
        checks.append(check("claims_no_extra_ids", not extra, 0.04, ", ".join(extra)))
        if extra:
            violations.append(f"extra claim ids present: {', '.join(extra)}")
            add_cap(caps, config, "extra_claim")

    for claim_id, rule in required.items():
        claim = actual.get(claim_id)
        exists = claim is not None
        checks.append(check(f"claim_exists:{claim_id}", exists, 0.03))
        if not claim:
            violations.append(f"missing required claim: {claim_id}")
            add_cap(caps, config, "missing_claim")
            continue

        expected_supported = bool(rule.get("supported", True))
        supported = claim.get("supported")
        support_ok = supported is expected_supported
        checks.append(check(f"claim_support_status:{claim_id}", support_ok, 0.05, str(supported)))
        if not support_ok:
            violations.append(f"claim support status mismatch: {claim_id}")
            add_cap(caps, config, "wrong_claim_status")

        required_text = str(rule.get("required_text", ""))
        if required_text:
            text_ok = isinstance(claim.get("text"), str) and claim_has_required_text(
                claim["text"],
                required_text,
            )
            checks.append(check(f"claim_text:{claim_id}", text_ok, 0.03, required_text))
            if not text_ok:
                violations.append(f"claim text missing required wording: {claim_id}")

        citation_ids = claim.get("citation_ids", [])
        citation_ids_ok = isinstance(citation_ids, list)
        checks.append(check(f"claim_citation_ids_schema:{claim_id}", citation_ids_ok, 0.02))
        if not citation_ids_ok:
            violations.append(f"claim citation_ids is not a list: {claim_id}")
            add_cap(caps, config, "missing_citation_support")
            continue

        citations = claim_citations_for(claim, citation_map)
        missing_ids = [item for item in citation_ids if isinstance(item, str) and item not in citation_map]
        checks.append(check(f"claim_citation_ids_exist:{claim_id}", not missing_ids, 0.04, ", ".join(missing_ids)))
        if missing_ids:
            violations.append(f"claim cites missing citation ids: {claim_id}")
            add_cap(caps, config, "missing_citation_support")

        if expected_supported:
            has_citation = bool(citations)
            checks.append(check(f"claim_has_supporting_citation:{claim_id}", has_citation, 0.06))
            if not has_citation:
                violations.append(f"missing citation support: {claim_id}")
                add_cap(caps, config, "missing_citation_support")

        allowed_docs = set(rule.get("acceptable_citation_doc_ids", []))
        if allowed_docs and citations:
            doc_ok = any(str(citation.get("doc_id", "")) in allowed_docs for citation in citations)
            checks.append(check(f"claim_allowed_source:{claim_id}", doc_ok, 0.05, ",".join(sorted(allowed_docs))))
            if not doc_ok:
                violations.append(f"claim lacks acceptable source: {claim_id}")
                add_cap(caps, config, "missing_citation_support")

        for evidence in rule.get("required_evidence", []):
            doc_id = str(evidence.get("doc_id", ""))
            quote = str(evidence.get("quote", ""))
            evidence_ok = any(
                str(citation.get("doc_id", "")) == doc_id
                and normalize_text(quote) in normalize_text(str(citation.get("quote", "")))
                for citation in citations
            )
            checks.append(check(f"claim_evidence:{claim_id}:{doc_id}", evidence_ok, 0.06, quote[:120]))
            if not evidence_ok:
                violations.append(f"claim missing required evidence: {claim_id}")
                add_cap(caps, config, "missing_citation_support")
    return checks, violations, caps


def score_answer(
    config: dict[str, Any], answer_path: Path
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    if not answer_path.exists():
        return checks, violations, caps

    text = answer_path.read_text(encoding="utf-8")
    normalized = normalize_text(text)
    answer_config = config.get("answer", {})

    headings = markdown_headings(text)
    required_sections = answer_config.get("required_sections", [])
    if required_sections:
        position = 0
        for heading in headings:
            if position < len(required_sections) and heading == required_sections[position]:
                position += 1
        passed = position == len(required_sections)
        checks.append(check("answer_required_sections_in_order", passed, 0.1, " > ".join(headings)))
        if not passed:
            violations.append("missing or misordered answer section")
            add_cap(caps, config, "missing_answer_section")

    for phrase in answer_config.get("required_phrases", []):
        phrase_text = str(phrase)
        passed = normalize_text(phrase_text) in normalized
        checks.append(check(f"answer_required_phrase:{phrase_text[:40]}", passed, 0.03, phrase_text))
        if not passed:
            violations.append(f"missing answer phrase: {phrase_text}")

    banned = [phrase for phrase in answer_config.get("banned_phrases", []) if normalize_text(str(phrase)) in normalized]
    checks.append(check("answer_banned_phrases_absent", not banned, 0.05, ", ".join(banned)))
    if banned:
        violations.append(f"banned answer phrases present: {', '.join(banned)}")
        add_cap(caps, config, "banned_phrase")

    unsupported = [
        phrase
        for phrase in answer_config.get("unsupported_claim_phrases", [])
        if normalize_text(str(phrase)) in normalized
    ]
    checks.append(check("answer_no_unsupported_claims", not unsupported, 0.06, ", ".join(unsupported)))
    if unsupported:
        violations.append(f"unsupported answer claims present: {', '.join(unsupported)}")
        add_cap(caps, config, "unsupported_claim")

    if "max_words" in answer_config:
        count = word_count(text)
        maximum = int(answer_config["max_words"])
        checks.append(check("answer_max_words", count <= maximum, 0.04, f"got={count}"))
    return checks, violations, caps


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    config = load_config(fixture_dir)
    corpus = load_corpus(fixture_dir)
    checks, violations, caps = score_artifact_inventory(config, artifacts_dir)

    citations = None
    citations_path = artifacts_dir / "citations.json"
    if citations_path.exists():
        citations, file_checks, file_violations, file_caps = read_json_artifact(
            citations_path,
            check_name="citations_json_valid",
            invalid_cap="invalid_citations_json",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    citation_checks, citation_violations, citation_caps, citation_map = score_citations(
        config,
        citations,
        corpus,
    )
    checks.extend(citation_checks)
    violations.extend(citation_violations)
    caps.extend(citation_caps)

    claims = None
    claims_path = artifacts_dir / "claims.json"
    if claims_path.exists():
        claims, file_checks, file_violations, file_caps = read_json_artifact(
            claims_path,
            check_name="claims_json_valid",
            invalid_cap="invalid_claims_json",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    claim_checks, claim_violations, claim_caps = score_claims(config, claims, citation_map)
    checks.extend(claim_checks)
    violations.extend(claim_violations)
    caps.extend(claim_caps)

    answer_checks, answer_violations, answer_caps = score_answer(config, artifacts_dir / "answer.md")
    checks.extend(answer_checks)
    violations.extend(answer_violations)
    caps.extend(answer_caps)

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
