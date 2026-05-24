from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .registry import list_tasks, repo_root_from, validate_all
from .scoring import score_task, write_score


def cmd_list_tasks(args: argparse.Namespace) -> int:
    root = repo_root_from(args.root)
    for task in list_tasks(root):
        print(f"{task['id']:8} {task['version']:8} {task['status']:18} {task['name']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = repo_root_from(args.root)
    results = validate_all(root)
    if not results:
        print("No tasks found.", file=sys.stderr)
        return 1
    failed = False
    for task_id, errors in results.items():
        if errors:
            failed = True
            print(f"[FAIL] {task_id}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[ OK ] {task_id}")
    return 1 if failed else 0


def cmd_score(args: argparse.Namespace) -> int:
    root = repo_root_from(args.root)
    artifacts = Path(args.artifacts).resolve()
    try:
        result = score_task(root=root, task_id=args.task, case_id=args.case, artifacts_dir=artifacts)
    except (AttributeError, FileNotFoundError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.output:
        write_score(result, Path(args.output).resolve())
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-bench")
    parser.add_argument("--root", default=".", help="Repository root")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-tasks", help="List task cards")
    p_list.set_defaults(func=cmd_list_tasks)

    p_validate = sub.add_parser("validate", help="Validate task card structure")
    p_validate.set_defaults(func=cmd_validate)

    p_score = sub.add_parser("score", help="Score an artifact directory")
    p_score.add_argument("--task", required=True)
    p_score.add_argument("--case", default="case_001")
    p_score.add_argument("--artifacts", required=True)
    p_score.add_argument("--output")
    p_score.set_defaults(func=cmd_score)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
