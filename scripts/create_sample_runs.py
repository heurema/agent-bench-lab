from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_bench_lab.scoring import score_task, write_score  # noqa: E402

CASES = {
    "IF-01": ("case_001", "case_002", "case_003"),
    "DATA-01": ("case_001", "case_002", "case_003"),
}
AGENT_CONFIGS = {
    "baseline": ROOT / "configs" / "agents" / "baseline.json",
    "spec_first": ROOT / "configs" / "agents" / "spec_first.json",
}


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "create_sample_artifacts.py")], check=True)
    for agent_id, config_path in AGENT_CONFIGS.items():
        for task_id, case_ids in CASES.items():
            for case_id in case_ids:
                artifacts_dir = ROOT / "examples" / "artifacts" / task_id / case_id
                result = score_task(
                    root=ROOT,
                    task_id=task_id,
                    case_id=case_id,
                    artifacts_dir=artifacts_dir,
                    agent_config_path=config_path,
                    run_id=f"{agent_id}_{task_id}_{case_id}",
                )
                output_path = ROOT / "runs" / agent_id / f"{task_id}_{case_id}" / "score.json"
                write_score(result, output_path)
    print("Sample runs created under runs/baseline and runs/spec_first")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
