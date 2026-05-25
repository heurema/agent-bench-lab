from __future__ import annotations

import os
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def copy_tree_contents(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def main() -> int:
    task_id = os.environ.get("AGENT_BENCH_TASK_ID")
    case_id = os.environ.get("AGENT_BENCH_CASE_ID")
    artifacts_dir = os.environ.get("AGENT_BENCH_ARTIFACTS_DIR")
    if not task_id or not case_id or not artifacts_dir:
        raise SystemExit("missing AGENT_BENCH_TASK_ID, AGENT_BENCH_CASE_ID, or AGENT_BENCH_ARTIFACTS_DIR")

    runpy.run_path(str(ROOT / "scripts" / "create_sample_artifacts.py"), run_name="__main__")
    source = ROOT / "examples" / "artifacts" / task_id / case_id
    if not source.is_dir():
        raise SystemExit(f"no sample artifacts for {task_id}/{case_id}")
    copy_tree_contents(source, Path(artifacts_dir))
    print(f"mock artifacts written for {task_id}/{case_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
