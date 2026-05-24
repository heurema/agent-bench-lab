from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("name")
    args = parser.parse_args()
    root = Path.cwd()
    task_dir = root / "tasks" / args.task_id
    fixture_dir = root / "fixtures" / "public" / args.task_id / "case_001"
    task_dir.mkdir(parents=True, exist_ok=False)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    task = {
        "id": args.task_id,
        "version": "0.1.0",
        "name": args.name,
        "category": "todo",
        "purpose": "TODO",
        "agent_role": "TODO",
        "user_prompt": "TODO",
        "available_tools": [],
        "forbidden_tools": [],
        "environment_setup": "TODO",
        "input_fixtures": [f"fixtures/public/{args.task_id}/case_001"],
        "required_final_artifact": "TODO",
        "success_criteria": [],
        "scoring_rubric": [{"component": "TODO", "weight": 100, "description": "TODO"}],
        "hidden_tests": [],
        "partial_credit_rules": "TODO",
        "common_failure_modes": [],
        "expected_trace_signals": [],
        "what_to_log": [],
        "how_to_compare_runs": [],
        "variants": [],
        "anti_overfitting_strategy": "TODO",
        "implementation_notes": "TODO",
        "meta": {"difficulty": "M", "estimated_runtime_minutes": 8, "cost_sensitivity": "M", "repeatability_score": 5, "contamination_risk": 1},
    }
    (task_dir / "task.json").write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
    (task_dir / "prompt.md").write_text("TODO\n", encoding="utf-8")
    (task_dir / "scorer.py").write_text("def score(task_dir, fixture_dir, artifacts_dir):\n    return {'score': 0.0, 'success': False, 'checks': []}\n", encoding="utf-8")
    print(f"Created {task_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
