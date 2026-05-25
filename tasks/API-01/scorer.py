from __future__ import annotations

import copy
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_config(fixture_dir: Path) -> dict[str, Any]:
    config_path = fixture_dir / "check_config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing API-01 check config: {config_path}")
    return load_json(config_path)


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
    checks.append(check(check_name, isinstance(data, dict), 0.08))
    if not isinstance(data, dict):
        violations.append(f"JSON root is not an object: {path.name}")
        add_cap(caps, config, "invalid_schema")
        return None, checks, violations, caps
    return data, checks, violations, caps


def tool_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tools = catalog.get("tools", [])
    if not isinstance(tools, list):
        return {}
    return {
        str(tool.get("tool_id")): tool
        for tool in tools
        if isinstance(tool, dict) and tool.get("tool_id") is not None
    }


def call_items(tool_calls: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(tool_calls, dict):
        return []
    calls = tool_calls.get("calls", [])
    return [call for call in calls if isinstance(call, dict)] if isinstance(calls, list) else []


def sorted_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(calls, key=lambda item: item.get("step", 0))


def first_index(calls: list[dict[str, Any]], tool_id: str) -> int | None:
    for index, call in enumerate(calls):
        if call.get("tool_id") == tool_id:
            return index
    return None


def get_path(data: dict[str, Any], path: list[Any]) -> Any:
    current: Any = data
    for item in path:
        if not isinstance(current, dict) or item not in current:
            return None
        current = current[item]
    return current


def set_path(data: dict[str, Any], path: list[Any], value: Any) -> None:
    current: Any = data
    for item in path[:-1]:
        if not isinstance(current, dict):
            return
        current = current.setdefault(item, {})
    if isinstance(current, dict) and path:
        current[path[-1]] = value


def call_params(call: dict[str, Any]) -> dict[str, Any]:
    params = call.get("params", {})
    return params if isinstance(params, dict) else {}


def score_call_schema(
    config: dict[str, Any],
    calls: list[dict[str, Any]],
    catalog_tools: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []

    steps = [call.get("step") for call in calls]
    steps_ok = steps == list(range(1, len(calls) + 1))
    checks.append(check("tool_call_steps_sequential", steps_ok, 0.04, str(steps)))
    if not steps_ok:
        violations.append("tool call steps are not sequential")
        add_cap(caps, config, "invalid_schema")

    if "max_call_count" in config:
        max_calls = int(config["max_call_count"])
        within_limit = len(calls) <= max_calls
        checks.append(check("tool_call_count_within_limit", within_limit, 0.04, str(len(calls))))
        if not within_limit:
            violations.append(f"tool call count exceeds limit: {len(calls)} > {max_calls}")
            add_cap(caps, config, "invalid_schema")

    used_tools = [str(call.get("tool_id", "")) for call in calls]
    for tool_id in config.get("required_tools", []):
        passed = tool_id in used_tools
        checks.append(check(f"required_tool:{tool_id}", passed, 0.04))
        if not passed:
            violations.append(f"missing required tool: {tool_id}")

    forbidden_tools = set(config.get("forbidden_tools", []))
    forbidden_categories = set(config.get("forbidden_tool_categories", []))
    for index, call in enumerate(calls, start=1):
        tool_id = str(call.get("tool_id", ""))
        params = call_params(call)
        reason = call.get("reason")
        schema_ok = isinstance(call.get("step"), int) and bool(tool_id) and isinstance(params, dict)
        checks.append(check(f"tool_call_schema:{index}", schema_ok, 0.03))
        if not schema_ok:
            violations.append(f"invalid tool call schema at step {index}")
            add_cap(caps, config, "invalid_schema")

        exists = tool_id in catalog_tools
        checks.append(check(f"tool_exists:{index}:{tool_id}", exists, 0.05))
        if not exists:
            violations.append(f"invented tool id: {tool_id}")
            add_cap(caps, config, "invented_tool")
            continue

        tool = catalog_tools[tool_id]
        forbidden = bool(tool.get("forbidden")) or tool_id in forbidden_tools
        forbidden = forbidden or str(tool.get("category")) in forbidden_categories
        checks.append(check(f"tool_not_forbidden:{index}:{tool_id}", not forbidden, 0.06))
        if forbidden:
            violations.append(f"forbidden tool used: {tool_id}")
            add_cap(caps, config, "forbidden_tool")

        for param in tool.get("required_params", []):
            present = param in params
            checks.append(check(f"tool_param_present:{tool_id}:{param}", present, 0.02))
            if not present:
                violations.append(f"missing parameter {param} for {tool_id}")
                add_cap(caps, config, "wrong_params")

        if tool.get("operation") == "update_field":
            field_param = str(tool.get("field_param", "field"))
            allowed_fields = set(tool.get("allowed_fields", []))
            field = params.get(field_param)
            if allowed_fields:
                allowed = field in allowed_fields
                checks.append(check(f"tool_field_allowed:{tool_id}", allowed, 0.03, str(field)))
                if not allowed:
                    violations.append(f"field not allowed for {tool_id}: {field}")
                    add_cap(caps, config, "wrong_params")

        checks.append(check(f"tool_reason_present:{index}", isinstance(reason, str) and bool(reason.strip()), 0.01))
    return checks, violations, caps


def score_expected_calls(
    config: dict[str, Any],
    calls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    calls_by_step = {call.get("step"): call for call in calls}
    for expected in config.get("expected_calls", []):
        step = expected.get("step")
        actual = calls_by_step.get(step)
        exists = actual is not None
        checks.append(check(f"expected_call_exists:{step}", exists, 0.03))
        if not actual:
            violations.append(f"missing expected call at step {step}")
            add_cap(caps, config, "wrong_call_order")
            continue
        tool_ok = actual.get("tool_id") == expected.get("tool_id")
        checks.append(check(f"expected_call_tool:{step}", tool_ok, 0.04, str(actual.get("tool_id"))))
        if not tool_ok:
            violations.append(f"wrong tool at step {step}")
            add_cap(caps, config, "wrong_call_order")

        actual_params = call_params(actual)
        for key, value in expected.get("params", {}).items():
            passed = actual_params.get(key) == value
            checks.append(check(f"expected_call_param:{step}:{key}", passed, 0.04, str(actual_params.get(key))))
            if not passed:
                violations.append(f"wrong parameter at step {step}: {key}")
                add_cap(caps, config, "wrong_params")
    return checks, violations, caps


def score_order_policy(
    config: dict[str, Any],
    calls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    ordered = sorted_calls(calls)

    for rule in config.get("required_order", []):
        before = str(rule.get("before", ""))
        after = str(rule.get("after", ""))
        before_index = first_index(ordered, before)
        after_index = first_index(ordered, after)
        passed = before_index is not None and after_index is not None and before_index < after_index
        checks.append(check(f"required_order:{before}:before:{after}", passed, 0.05))
        if not passed:
            violations.append(f"wrong call order: {before} before {after}")
            add_cap(caps, config, "wrong_call_order")

    for rule in config.get("read_before_write", []):
        read_tool = str(rule.get("read_tool", ""))
        write_tool = str(rule.get("write_tool", ""))
        entity_param = str(rule.get("entity_param", ""))
        read_index = first_index(ordered, read_tool)
        write_index = first_index(ordered, write_tool)
        order_ok = read_index is not None and write_index is not None and read_index < write_index
        param_ok = True
        if order_ok and entity_param:
            read_params = call_params(ordered[read_index])
            write_params = call_params(ordered[write_index])
            if entity_param in read_params and entity_param in write_params:
                param_ok = read_params[entity_param] == write_params[entity_param]
        passed = bool(order_ok and param_ok)
        checks.append(check(f"read_before_write:{read_tool}:before:{write_tool}", passed, 0.06))
        if not passed:
            violations.append(f"missing read-before-write: {read_tool} before {write_tool}")
            add_cap(caps, config, "missing_read_before_write")
    return checks, violations, caps


def simulate_call(
    state: dict[str, Any],
    tool: dict[str, Any],
    params: dict[str, Any],
) -> tuple[bool, str | None]:
    operation = tool.get("operation")
    entity = str(tool.get("entity", ""))
    id_param = str(tool.get("id_param", "id"))
    entity_id = params.get(id_param)
    if not entity or not isinstance(entity_id, str):
        return False, "missing entity id"

    state.setdefault(entity, {})
    entity_store = state[entity]
    if not isinstance(entity_store, dict):
        return False, f"invalid state entity store: {entity}"

    if operation == "read":
        if entity_id not in entity_store:
            return False, f"unknown entity id: {entity}/{entity_id}"
        return True, None

    if operation == "update_field":
        if entity_id not in entity_store:
            return False, f"unknown entity id: {entity}/{entity_id}"
        field = params.get(str(tool.get("field_param", "field")))
        value = params.get(str(tool.get("value_param", "value")))
        if not isinstance(field, str):
            return False, "missing update field"
        entity_store[entity_id][field] = value
        return True, None

    if operation == "create":
        if entity_id in entity_store:
            return False, f"entity already exists: {entity}/{entity_id}"
        created = {key: value for key, value in params.items() if key != id_param}
        entity_store[entity_id] = created
        return True, None

    return False, f"unsupported operation: {operation}"


def simulate_calls(
    initial_state: dict[str, Any],
    catalog_tools: dict[str, dict[str, Any]],
    calls: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    state = copy.deepcopy(initial_state)
    errors = []
    for call in sorted_calls(calls):
        tool_id = str(call.get("tool_id", ""))
        tool = catalog_tools.get(tool_id)
        if tool is None:
            continue
        if bool(tool.get("forbidden")):
            continue
        ok, error = simulate_call(state, tool, call_params(call))
        if not ok and error:
            errors.append(f"step {call.get('step')}: {error}")
    return state, errors


def score_state_diff(
    config: dict[str, Any],
    final_state: dict[str, Any],
    simulation_errors: list[str],
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    checks.append(check("simulation_no_errors", not simulation_errors, 0.08, "; ".join(simulation_errors)))
    if simulation_errors:
        violations.extend(simulation_errors)
        if any("unknown entity id" in error for error in simulation_errors):
            add_cap(caps, config, "unknown_entity")
        else:
            add_cap(caps, config, "state_diff_mismatch")

    for expected in config.get("expected_state", []):
        path = expected.get("path", [])
        value = expected.get("value")
        actual = get_path(final_state, path if isinstance(path, list) else [])
        passed = actual == value
        name = "state:" + ".".join(str(item) for item in path)
        checks.append(check(name, passed, 0.06, f"got={actual!r}"))
        if not passed:
            violations.append(f"state diff mismatch: {'.'.join(str(item) for item in path)}")
            add_cap(caps, config, "state_diff_mismatch")
    return checks, violations, caps


def score_result(
    config: dict[str, Any],
    result: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str], list[float]]:
    checks = []
    violations = []
    caps = []
    if not isinstance(result, dict):
        return checks, violations, caps

    status = result.get("status")
    expected_status = config.get("expected_status")
    status_ok = status == expected_status
    checks.append(check("result_status", status_ok, 0.08, str(status)))
    if not status_ok:
        violations.append(f"result status mismatch: {status}")
        add_cap(caps, config, "result_status_mismatch")

    allowed_statuses = set(config.get("allowed_result_statuses", []))
    if allowed_statuses:
        allowed = status in allowed_statuses
        checks.append(check("result_status_allowed", allowed, 0.03))
        if not allowed:
            violations.append(f"result status not allowed: {status}")
            add_cap(caps, config, "result_status_mismatch")

    affected = result.get("affected_entities", [])
    affected_set = {str(item) for item in affected} if isinstance(affected, list) else set()
    checks.append(check("result_affected_entities_schema", isinstance(affected, list), 0.03))
    for entity in config.get("required_affected_entities", []):
        passed = entity in affected_set
        checks.append(check(f"result_affected_entity:{entity}", passed, 0.04))
        if not passed:
            violations.append(f"missing affected entity: {entity}")

    for field in ("summary", "final_state_expectation", "policy_notes"):
        present = field in result
        checks.append(check(f"result_field_present:{field}", present, 0.02))
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
    catalog = load_json(fixture_dir / "api_catalog.json")
    initial_state = load_json(fixture_dir / "api_state.json")
    catalog_tools = tool_map(catalog)
    checks, violations, caps = score_artifact_inventory(config, artifacts_dir)

    tool_calls = None
    tool_calls_path = artifacts_dir / "tool_calls.json"
    if tool_calls_path.exists():
        tool_calls, file_checks, file_violations, file_caps = read_json_artifact(
            tool_calls_path,
            check_name="tool_calls_json_valid",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)

    calls_schema_ok = isinstance(tool_calls, dict) and isinstance(tool_calls.get("calls"), list)
    checks.append(check("tool_calls_schema", calls_schema_ok, 0.08))
    if tool_calls is None or not calls_schema_ok:
        violations.append("invalid tool_calls schema")
        add_cap(caps, config, "invalid_schema")
        calls = []
    else:
        calls = call_items(tool_calls)

    call_checks, call_violations, call_caps = score_call_schema(config, calls, catalog_tools)
    checks.extend(call_checks)
    violations.extend(call_violations)
    caps.extend(call_caps)

    expected_checks, expected_violations, expected_caps = score_expected_calls(config, calls)
    checks.extend(expected_checks)
    violations.extend(expected_violations)
    caps.extend(expected_caps)

    order_checks, order_violations, order_caps = score_order_policy(config, calls)
    checks.extend(order_checks)
    violations.extend(order_violations)
    caps.extend(order_caps)

    final_state, simulation_errors = simulate_calls(initial_state, catalog_tools, calls)
    state_checks, state_violations, state_caps = score_state_diff(
        config,
        final_state,
        simulation_errors,
    )
    checks.extend(state_checks)
    violations.extend(state_violations)
    caps.extend(state_caps)

    result = None
    result_path = artifacts_dir / "result.json"
    if result_path.exists():
        result, file_checks, file_violations, file_caps = read_json_artifact(
            result_path,
            check_name="result_json_valid",
            config=config,
        )
        checks.extend(file_checks)
        violations.extend(file_violations)
        caps.extend(file_caps)
    result_checks, result_violations, result_caps = score_result(config, result)
    checks.extend(result_checks)
    violations.extend(result_violations)
    caps.extend(result_caps)

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
