from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compare import compare_score_dirs, render_markdown_report, write_csv_report
from .registry import list_tasks, repo_root_from, validate_all
from .runner import run_agent_task
from .scoring import score_task, write_score
from .suite_runner import run_agent_suite


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
    agent_config = Path(args.agent_config).resolve() if args.agent_config else None
    try:
        result = score_task(
            root=root,
            task_id=args.task,
            case_id=args.case,
            artifacts_dir=artifacts,
            agent_config_path=agent_config,
            run_id=args.run_id,
        )
    except (AttributeError, FileNotFoundError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.out:
        write_score(result, Path(args.out).resolve())
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 2


def cmd_compare(args: argparse.Namespace) -> int:
    result = compare_score_dirs(Path(args.baseline).resolve(), Path(args.candidate).resolve())
    title = f"Compare: {Path(args.baseline).name} vs {Path(args.candidate).name}"
    report = render_markdown_report(result, title=title)
    if args.out:
        output_path = Path(args.out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    else:
        print(report)
    if args.csv:
        write_csv_report(result, Path(args.csv).resolve())
    if result["missing_scores"]:
        return 1
    if args.fail_on_invalid and result["invalid_runs"]:
        return 1
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    root = repo_root_from(args.root)
    agent_config = Path(args.agent_config).resolve() if args.agent_config else None
    out_dir = Path(args.out).resolve() if args.out else None
    try:
        run_record = run_agent_task(
            root=root,
            task_id=args.task,
            case_id=args.case,
            agent_cmd=args.agent_cmd,
            agent_config_path=agent_config,
            out_dir=out_dir,
            timeout_seconds=args.timeout,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary = {
        "run_id": run_record["run_id"],
        "task_id": run_record["task_id"],
        "case_id": run_record["case_id"],
        "status": run_record["status"],
        "score": run_record.get("score"),
        "success": run_record.get("success"),
        "output_path": str(Path(run_record["paths"]["artifacts"]).parent),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if run_record["status"] == "passed" else 2


def cmd_run_suite(args: argparse.Namespace) -> int:
    root = repo_root_from(args.root)
    agent_config = Path(args.agent_config).resolve() if args.agent_config else None
    out_dir = Path(args.out).resolve() if args.out else None
    try:
        suite_record = run_agent_suite(
            root=root,
            suite=args.suite,
            agent_cmd=args.agent_cmd,
            agent_config_path=agent_config,
            out_dir=out_dir,
            timeout_seconds=args.timeout,
            case_override=args.case,
            fail_fast=args.fail_fast,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary = {
        "suite_run_id": suite_record["suite_run_id"],
        "suite_id": suite_record["suite_id"],
        "suite_version": suite_record["suite_version"],
        "status": suite_record["status"],
        "total_tasks": suite_record["total_tasks"],
        "completed_tasks": suite_record["completed_tasks"],
        "failed_tasks": suite_record["failed_tasks"],
        "success_count": suite_record["success_count"],
        "average_score": suite_record["average_score"],
        "output_path": suite_record["output_path"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if suite_record["status"] == "passed" else 2


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
    p_score.add_argument("--agent-config")
    p_score.add_argument("--run-id")
    p_score.add_argument("--out", "--output", dest="out")
    p_score.set_defaults(func=cmd_score)

    p_compare = sub.add_parser("compare", help="Compare two directories of score.json files")
    p_compare.add_argument("--baseline", required=True)
    p_compare.add_argument("--candidate", required=True)
    p_compare.add_argument("--out")
    p_compare.add_argument("--csv")
    p_compare.add_argument(
        "--fail-on-invalid",
        action="store_true",
        help="Return non-zero when compared evidence contains invalid runs",
    )
    p_compare.set_defaults(func=cmd_compare)

    p_run = sub.add_parser("run", help="Run an external command against a task case")
    p_run.add_argument("--task", required=True)
    p_run.add_argument("--case", default="case_001")
    p_run.add_argument("--agent-cmd", required=True)
    p_run.add_argument("--agent-config")
    p_run.add_argument("--out")
    p_run.add_argument("--timeout", type=int, default=600)
    p_run.set_defaults(func=cmd_run)

    p_run_suite = sub.add_parser("run-suite", help="Run an external command across a suite")
    p_run_suite.add_argument("--suite", required=True)
    p_run_suite.add_argument("--agent-cmd", required=True)
    p_run_suite.add_argument("--agent-config")
    p_run_suite.add_argument("--out")
    p_run_suite.add_argument("--timeout", type=int, default=600)
    p_run_suite.add_argument("--case", help="Override suite recommended cases with one case ID")
    p_run_suite.add_argument("--fail-fast", action="store_true")
    p_run_suite.set_defaults(func=cmd_run_suite)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
