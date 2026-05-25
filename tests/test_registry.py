from pathlib import Path

from agent_bench_lab.registry import load_task, load_task_schema, list_tasks, validate_task, validate_all


def test_list_tasks_has_core_tasks():
    root = Path(__file__).resolve().parents[1]
    ids = {task["id"] for task in list_tasks(root)}
    assert {"CODE-01", "TERM-02", "APP-04", "DATA-01", "DOC-01", "IF-01", "SEC-01"}.issubset(ids)


def test_validate_all_tasks():
    root = Path(__file__).resolve().parents[1]
    results = validate_all(root)
    assert results
    assert all(not errors for errors in results.values())


def test_validate_task_uses_json_schema():
    root = Path(__file__).resolve().parents[1]
    task = load_task(root / "tasks" / "IF-01")
    schema = load_task_schema(root)
    task["meta"]["repeatability_score"] = 6

    errors = validate_task(task, schema=schema)

    assert any("schema meta.repeatability_score" in error for error in errors)
