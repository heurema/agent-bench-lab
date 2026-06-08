from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .redaction import redact_text

EPSILON = 1e-9


def score_key(score: dict[str, Any]) -> tuple[str, str]:
    return str(score.get("task_id", "")), str(score.get("case_id", ""))


def load_score_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_scores(root: Path) -> dict[tuple[str, str], dict[str, Any]]:
    scores = {}
    if not root.exists():
        return scores
    for path in sorted(root.rglob("score.json")):
        score = load_score_file(path)
        score["_path"] = str(path)
        scores[score_key(score)] = score
    return scores


def _score_value(score: dict[str, Any] | None) -> float | None:
    if score is None:
        return None
    value = score.get("score")
    if value is None:
        return None
    return float(value)


def _success(score: dict[str, Any] | None) -> bool:
    return bool(score and score.get("success"))


def _run_validity(score: dict[str, Any] | None) -> dict[str, Any]:
    if not score:
        return {"valid": True}
    value = score.get("run_validity")
    if isinstance(value, dict) and value.get("valid") is False:
        return {
            "valid": False,
            "category": str(value.get("category") or "unknown"),
            "diagnostic_code": str(value.get("diagnostic_code") or ""),
            "reason": str(value.get("reason") or ""),
        }
    return {"valid": True}


def _invalid_entry(
    *,
    side: str,
    task_id: str,
    case_id: str,
    score: dict[str, Any],
) -> dict[str, str]:
    validity = _run_validity(score)
    result = {
        "side": side,
        "task_id": task_id,
        "case_id": case_id,
        "category": str(validity.get("category") or "unknown"),
        "reason": str(validity.get("reason") or ""),
    }
    diagnostic_code = str(validity.get("diagnostic_code") or "")
    if diagnostic_code:
        result["diagnostic_code"] = diagnostic_code
    return result


def _status(
    delta: float | None,
    baseline: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    baseline_invalid: bool = False,
    candidate_invalid: bool = False,
) -> str:
    if baseline is None:
        return "missing_baseline"
    if candidate is None:
        return "missing_candidate"
    if baseline_invalid or candidate_invalid:
        return "invalid"
    if delta is None or abs(delta) <= EPSILON:
        return "unchanged"
    return "improved" if delta > 0 else "regressed"


def compare_score_dirs(baseline_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    baseline_scores = collect_scores(baseline_dir)
    candidate_scores = collect_scores(candidate_dir)
    keys = sorted(set(baseline_scores) | set(candidate_scores))
    rows = []
    policy_violations = []
    invalid_runs = []

    for task_id, case_id in keys:
        baseline = baseline_scores.get((task_id, case_id))
        candidate = candidate_scores.get((task_id, case_id))
        baseline_invalid = _run_validity(baseline).get("valid") is False
        candidate_invalid = _run_validity(candidate).get("valid") is False
        baseline_score = _score_value(baseline)
        candidate_score = _score_value(candidate)
        delta = (
            candidate_score - baseline_score
            if baseline_score is not None and candidate_score is not None
            and not baseline_invalid
            and not candidate_invalid
            else None
        )
        status = _status(delta, baseline, candidate, baseline_invalid, candidate_invalid)
        row = {
            "task_id": task_id,
            "case_id": case_id,
            "baseline_score": baseline_score,
            "candidate_score": candidate_score,
            "delta": delta,
            "baseline_success": _success(baseline),
            "candidate_success": _success(candidate),
            "baseline_valid": not baseline_invalid,
            "candidate_valid": not candidate_invalid,
            "status": status,
        }
        rows.append(row)
        if baseline and baseline_invalid:
            invalid_runs.append(
                _invalid_entry(side="baseline", task_id=task_id, case_id=case_id, score=baseline)
            )
        if candidate and candidate_invalid:
            invalid_runs.append(
                _invalid_entry(side="candidate", task_id=task_id, case_id=case_id, score=candidate)
            )
        for label, score in (("baseline", baseline), ("candidate", candidate)):
            if not score:
                continue
            for violation in score.get("policy_violations", []):
                policy_violations.append(
                    {
                        "side": label,
                        "task_id": task_id,
                        "case_id": case_id,
                        "violation": str(violation),
                    }
                )

    paired = [
        row
        for row in rows
        if row["baseline_score"] is not None
        and row["candidate_score"] is not None
        and row["baseline_valid"]
        and row["candidate_valid"]
    ]
    baseline_average = (
        sum(row["baseline_score"] for row in paired if row["baseline_score"] is not None) / len(paired)
        if paired
        else None
    )
    candidate_average = (
        sum(row["candidate_score"] for row in paired if row["candidate_score"] is not None) / len(paired)
        if paired
        else None
    )

    return {
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "total_tasks_compared": len(paired),
        "baseline_average_score": baseline_average,
        "candidate_average_score": candidate_average,
        "delta": (
            candidate_average - baseline_average
            if baseline_average is not None and candidate_average is not None
            else None
        ),
        "baseline_success_count": sum(1 for row in paired if row["baseline_success"]),
        "candidate_success_count": sum(1 for row in paired if row["candidate_success"]),
        "regressions": [row for row in paired if row["status"] == "regressed"],
        "improvements": [row for row in paired if row["status"] == "improved"],
        "unchanged": [row for row in paired if row["status"] == "unchanged"],
        "policy_violations": policy_violations,
        "invalid_runs": invalid_runs,
        "missing_scores": [row for row in rows if row["status"].startswith("missing_")],
        "rows": rows,
    }


def _format_number(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "n/a"
    if signed:
        return f"{value:+.3f}"
    return f"{value:.3f}"


def _safe_cell(value: Any) -> str:
    return redact_text(str(value))


def _format_row_item(row: dict[str, Any]) -> str:
    delta = _format_number(row["delta"], signed=True)
    return f"- {_safe_cell(row['task_id'])}/{_safe_cell(row['case_id'])}: {delta}"


def render_markdown_report(result: dict[str, Any], title: str = "Compare") -> str:
    lines = [
        f"# {title}",
        "",
        f"Tasks compared: {result['total_tasks_compared']}",
        "",
        f"Baseline average score: {_format_number(result['baseline_average_score'])}",
        f"Candidate average score: {_format_number(result['candidate_average_score'])}",
        f"Delta: {_format_number(result['delta'], signed=True)}",
        "",
        (
            "Baseline successes: "
            f"{result['baseline_success_count']}/{result['total_tasks_compared']}"
        ),
        (
            "Candidate successes: "
            f"{result['candidate_success_count']}/{result['total_tasks_compared']}"
        ),
        "",
        "## Improvements",
    ]
    lines.extend(_format_row_item(row) for row in result["improvements"][:20])
    if not result["improvements"]:
        lines.append("- none")
    lines.extend(["", "## Regressions"])
    lines.extend(_format_row_item(row) for row in result["regressions"][:20])
    if not result["regressions"]:
        lines.append("- none")
    lines.extend(["", "## Unchanged"])
    lines.extend(_format_row_item(row) for row in result["unchanged"][:20])
    if not result["unchanged"]:
        lines.append("- none")
    lines.extend(["", "## Policy Violations"])
    for item in result["policy_violations"][:20]:
        lines.append(
            "- "
            f"{_safe_cell(item['side'])} "
            f"{_safe_cell(item['task_id'])}/{_safe_cell(item['case_id'])}: "
            f"{_safe_cell(item['violation'])}"
        )
    if not result["policy_violations"]:
        lines.append("- none")
    lines.extend(["", "## Missing Scores"])
    for row in result["missing_scores"][:20]:
        lines.append(
            f"- {_safe_cell(row['task_id'])}/{_safe_cell(row['case_id'])}: "
            f"{_safe_cell(row['status'])}"
        )
    if not result["missing_scores"]:
        lines.append("- none")
    lines.extend(["", "## Run Validity"])
    for item in result.get("invalid_runs", [])[:20]:
        reason = f" - {_safe_cell(item['reason'])}" if item.get("reason") else ""
        category = _safe_cell(item["category"])
        if item.get("diagnostic_code"):
            category = f"{category}/{_safe_cell(item['diagnostic_code'])}"
        lines.append(
            "- "
            f"{_safe_cell(item['side'])} "
            f"{_safe_cell(item['task_id'])}/{_safe_cell(item['case_id'])}: "
            f"{category}"
            f"{reason}"
        )
    if not result.get("invalid_runs"):
        lines.append("- all paired run evidence is valid or lacks run_validity metadata")
    lines.extend(
        [
            "",
            "## Per-task Table",
            "",
            "| Task | Case | Baseline | Candidate | Delta | Baseline Success | Candidate Success | Status |",
            "|---|---|---:|---:|---:|---|---|---|",
        ]
    )
    for row in result["rows"]:
        lines.append(
            "| "
            f"{_safe_cell(row['task_id'])} | "
            f"{_safe_cell(row['case_id'])} | "
            f"{_format_number(row['baseline_score'])} | "
            f"{_format_number(row['candidate_score'])} | "
            f"{_format_number(row['delta'], signed=True)} | "
            f"{row['baseline_success']} | "
            f"{row['candidate_success']} | "
            f"{_safe_cell(row['status'])} |"
        )
    lines.extend(
        [
            "",
            "Warnings:",
            "- public smoke fixtures only, not decision-grade holdout",
            "- cost, latency, and tool-call fields may be empty until real run capture is wired",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv_report(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_id",
                "case_id",
                "baseline_score",
                "candidate_score",
                "delta",
                "baseline_success",
                "candidate_success",
                "status",
            ],
        )
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow(
                {
                    "task_id": _safe_cell(row["task_id"]),
                    "case_id": _safe_cell(row["case_id"]),
                    "baseline_score": row["baseline_score"],
                    "candidate_score": row["candidate_score"],
                    "delta": row["delta"],
                    "baseline_success": row["baseline_success"],
                    "candidate_success": row["candidate_success"],
                    "status": _safe_cell(row["status"]),
                }
            )
