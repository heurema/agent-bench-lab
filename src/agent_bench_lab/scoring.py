from __future__ import annotations

import inspect
import importlib.util
import json
from pathlib import Path
from typing import Any

from .run_records import build_score_record

SCORER_PARAMETERS = ("task_dir", "fixture_dir", "artifacts_dir")


def load_scorer(task_dir: Path):
    scorer_path = task_dir / "scorer.py"
    if not scorer_path.exists():
        raise FileNotFoundError(f"Missing scorer.py in {task_dir}")
    spec = importlib.util.spec_from_file_location(f"scorer_{task_dir.name}", scorer_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load scorer from {scorer_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "score"):
        raise AttributeError(f"{scorer_path} must define score(task_dir, fixture_dir, artifacts_dir)")
    scorer = module.score
    signature = inspect.signature(scorer)
    parameters = list(signature.parameters.values())
    names = tuple(parameter.name for parameter in parameters)
    if names != SCORER_PARAMETERS:
        expected = ", ".join(SCORER_PARAMETERS)
        actual = ", ".join(names) or "no parameters"
        raise TypeError(f"{scorer_path} score signature must be ({expected}); got ({actual})")
    for parameter in parameters:
        if parameter.kind not in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            raise TypeError(f"{scorer_path} score parameters must be named parameters")
    return scorer


def score_task(
    root: Path,
    task_id: str,
    case_id: str,
    artifacts_dir: Path,
    agent_config_path: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    task_dir = root / "tasks" / task_id
    fixture_dir = root / "fixtures" / "public" / task_id / case_id
    if not task_dir.is_dir():
        raise FileNotFoundError(f"Unknown task: {task_id}")
    if not fixture_dir.is_dir():
        raise FileNotFoundError(f"Missing public fixture for {task_id}/{case_id}: {fixture_dir}")
    if not artifacts_dir.is_dir():
        raise FileNotFoundError(f"Missing artifacts directory: {artifacts_dir}")
    scorer = load_scorer(task_dir)
    result = scorer(task_dir=task_dir, fixture_dir=fixture_dir, artifacts_dir=artifacts_dir)
    if not isinstance(result, dict):
        raise TypeError(f"{task_dir / 'scorer.py'} score() must return a dict")
    return build_score_record(
        raw_result=result,
        task_dir=task_dir,
        artifacts_dir=artifacts_dir,
        task_id=task_id,
        case_id=case_id,
        agent_config_path=agent_config_path,
        run_id=run_id,
    )


def write_score(score: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(score, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
