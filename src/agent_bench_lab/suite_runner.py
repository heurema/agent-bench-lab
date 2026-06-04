from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .run_records import load_agent_config
from .runner import command_hash, run_agent_task, safe_slug, unique_run_token, utc_now, write_json


def load_suite_config(root: Path, suite: str | Path) -> dict[str, Any]:
    suite_path = Path(suite)
    if not suite_path.is_absolute():
        if suite_path.exists() or suite_path.suffix == ".json" or len(suite_path.parts) > 1:
            suite_path = (root / suite_path).resolve()
        else:
            suite_path = root / "configs" / "suites" / f"{suite_path}.json"
    if not suite_path.exists():
        raise FileNotFoundError(f"Missing suite config: {suite_path}")
    data = json.loads(suite_path.read_text(encoding="utf-8"))
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError(f"Suite config must include a non-empty tasks list: {suite_path}")
    data["_suite_path"] = str(suite_path)
    return data


def build_suite_run_id(agent_config_id: str, suite_id: str) -> str:
    return safe_slug(f"{agent_config_id}_{suite_id}_{unique_run_token()}")


def suite_cases(suite_config: dict[str, Any], case_override: str | None = None) -> list[str]:
    if case_override:
        return [case_override]
    configured = suite_config.get("recommended_cases")
    if not configured:
        return ["case_001"]
    if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
        raise ValueError("Suite recommended_cases must be a list of case IDs")
    return configured


def default_suite_out_dir(root: Path, agent_config_id: str, suite_id: str, suite_run_id: str) -> Path:
    return root / "runs" / "manual" / safe_slug(agent_config_id) / f"{safe_slug(suite_id)}_{suite_run_id}"


def _task_run_summary(run_record: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    return {
        "task_id": run_record["task_id"],
        "case_id": run_record["case_id"],
        "run_id": run_record["run_id"],
        "status": run_record["status"],
        "score": run_record.get("score"),
        "success": bool(run_record.get("success")),
        "path": str(run_dir),
    }


def _error_task_run(task_id: str, case_id: str, run_dir: Path, message: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "case_id": case_id,
        "run_id": None,
        "status": "error",
        "score": 0.0,
        "success": False,
        "path": str(run_dir),
        "error": message,
    }


def _suite_status(task_runs: list[dict[str, Any]], total_tasks: int) -> str:
    if not task_runs:
        return "error"
    failed = [item for item in task_runs if item["status"] != "passed" or not item["success"]]
    if not failed and len(task_runs) == total_tasks:
        return "passed"
    if sum(1 for item in task_runs if item["success"]) == 0:
        return "failed"
    return "partial"


def run_agent_suite(
    *,
    root: Path,
    suite: str | Path,
    agent_cmd: str,
    agent_config_path: Path | None,
    out_dir: Path | None = None,
    timeout_seconds: int = 600,
    case_override: str | None = None,
    fail_fast: bool = False,
) -> dict[str, Any]:
    suite_config = load_suite_config(root, suite)
    suite_id = str(suite_config.get("suite_id") or Path(str(suite)).stem)
    suite_version = str(suite_config.get("version", "unknown"))
    agent_config_id, agent_config_hash = load_agent_config(agent_config_path)
    suite_run_id = build_suite_run_id(agent_config_id, suite_id)
    resolved_out_dir = (
        out_dir.resolve()
        if out_dir
        else default_suite_out_dir(root, agent_config_id, suite_id, suite_run_id).resolve()
    )
    resolved_out_dir.mkdir(parents=True, exist_ok=True)

    tasks = [str(task_id) for task_id in suite_config["tasks"]]
    cases = suite_cases(suite_config, case_override=case_override)
    planned_runs = [(task_id, case_id) for task_id in tasks for case_id in cases]
    task_runs: list[dict[str, Any]] = []
    error_summary: list[str] = []
    stopped_early = False
    started_at = utc_now()

    for task_id, case_id in planned_runs:
        run_dir = resolved_out_dir / f"{safe_slug(task_id)}_{safe_slug(case_id)}"
        if run_dir.exists():
            shutil.rmtree(run_dir)
        try:
            run_record = run_agent_task(
                root=root,
                task_id=task_id,
                case_id=case_id,
                agent_cmd=agent_cmd,
                agent_config_path=agent_config_path,
                out_dir=run_dir,
                timeout_seconds=timeout_seconds,
            )
            task_run = _task_run_summary(run_record, run_dir)
        except Exception as exc:  # noqa: BLE001 - suite runner must preserve per-task failures.
            task_run = _error_task_run(task_id, case_id, run_dir, str(exc))
            error_summary.append(f"{task_id}/{case_id}: {exc}")
        task_runs.append(task_run)
        if fail_fast and (task_run["status"] != "passed" or not task_run["success"]):
            stopped_early = True
            break

    failed_tasks = sum(1 for item in task_runs if item["status"] != "passed" or not item["success"])
    success_count = sum(1 for item in task_runs if item["success"])
    scores = [float(item.get("score") or 0.0) for item in task_runs]
    completed_at = utc_now()
    suite_record = {
        "suite_run_id": suite_run_id,
        "suite_id": suite_id,
        "suite_version": suite_version,
        "agent_config_id": agent_config_id,
        "agent_config_hash": agent_config_hash,
        "agent_cmd_hash": command_hash(agent_cmd),
        "started_at": started_at,
        "completed_at": completed_at,
        "status": _suite_status(task_runs, len(planned_runs)),
        "total_tasks": len(planned_runs),
        "completed_tasks": len(task_runs),
        "failed_tasks": failed_tasks,
        "average_score": sum(scores) / len(scores) if scores else None,
        "success_count": success_count,
        "stopped_early": stopped_early,
        "output_path": str(resolved_out_dir),
        "task_runs": task_runs,
        "error_summary": error_summary,
    }
    write_json(resolved_out_dir / "suite_run.json", suite_record)
    return suite_record
