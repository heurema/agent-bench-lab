from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REQUIRED_TASK_FIELDS = {
    "id",
    "version",
    "name",
    "category",
    "purpose",
    "agent_role",
    "user_prompt",
    "available_tools",
    "forbidden_tools",
    "environment_setup",
    "input_fixtures",
    "required_final_artifact",
    "success_criteria",
    "scoring_rubric",
    "hidden_tests",
    "partial_credit_rules",
    "common_failure_modes",
    "expected_trace_signals",
    "what_to_log",
    "how_to_compare_runs",
    "variants",
    "anti_overfitting_strategy",
    "implementation_notes",
    "meta",
}


def repo_root_from(path: str | Path | None = None) -> Path:
    return Path(path or ".").resolve()


def load_task(task_dir: Path) -> dict[str, Any]:
    task_file = task_dir / "task.json"
    if not task_file.exists():
        raise FileNotFoundError(f"Missing task.json in {task_dir}")
    return json.loads(task_file.read_text(encoding="utf-8"))


def load_task_schema(root: Path) -> dict[str, Any]:
    schema_file = root / "schemas" / "task.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(f"Missing task schema: {schema_file}")
    return json.loads(schema_file.read_text(encoding="utf-8"))


def iter_task_dirs(root: Path):
    tasks_root = root / "tasks"
    if not tasks_root.exists():
        return
    for path in sorted(tasks_root.iterdir()):
        if path.is_dir() and (path / "task.json").exists():
            yield path


def list_tasks(root: Path) -> list[dict[str, Any]]:
    tasks = []
    for task_dir in iter_task_dirs(root):
        task = load_task(task_dir)
        tasks.append({
            "id": task.get("id", task_dir.name),
            "version": task.get("version", "unknown"),
            "name": task.get("name", ""),
            "category": task.get("category", ""),
            "status": task.get("implementation_status", "unknown"),
        })
    return tasks


def _format_schema_error(error) -> str:
    path = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"schema {path}: {error.message}"


def _validate_rubric_weights(task: dict[str, Any]) -> list[str]:
    errors = []
    weights = task.get("scoring_rubric", [])
    if isinstance(weights, list) and weights:
        total = 0.0
        for item in weights:
            if not isinstance(item, dict):
                continue
            try:
                total += float(item.get("weight", 0))
            except (TypeError, ValueError):
                return errors
        if abs(total - 100.0) > 0.01:
            errors.append(f"scoring_rubric weights should sum to 100, got {total}")
    return errors


def validate_task(task: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    errors = []
    if schema is None:
        missing = sorted(REQUIRED_TASK_FIELDS - set(task.keys()))
        for field in missing:
            errors.append(f"missing required field: {field}")
    else:
        validator = Draft202012Validator(schema)
        schema_errors = sorted(
            validator.iter_errors(task),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
        errors.extend(_format_schema_error(error) for error in schema_errors)
    errors.extend(_validate_rubric_weights(task))
    return errors


def validate_task_dir(root: Path, task_dir: Path, schema: dict[str, Any]) -> tuple[str, list[str]]:
    task_file = task_dir / "task.json"
    try:
        task = load_task(task_dir)
    except JSONDecodeError as exc:
        return task_dir.name, [f"invalid JSON in {task_file}: {exc}"]

    task_id = task.get("id", task_dir.name)
    errors = validate_task(task, schema=schema)
    if task_id != task_dir.name:
        errors.append(f"task id {task_id!r} does not match directory {task_dir.name!r}")
    for required_file in ("prompt.md", "scorer.py"):
        if not (task_dir / required_file).exists():
            errors.append(f"missing task file: {task_dir / required_file}")
    for fixture in task.get("input_fixtures", []):
        if isinstance(fixture, str) and not (root / fixture).exists():
            errors.append(f"missing input fixture: {fixture}")
    return str(task_id), errors


def validate_all(root: Path) -> dict[str, list[str]]:
    result = {}
    schema = load_task_schema(root)
    for task_dir in iter_task_dirs(root):
        task_id, errors = validate_task_dir(root, task_dir, schema)
        result[task_id] = errors
    return result
