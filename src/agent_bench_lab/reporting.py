from __future__ import annotations

from statistics import mean
from typing import Iterable


def summarize_scores(scores: Iterable[dict]) -> dict:
    rows = list(scores)
    if not rows:
        return {"runs": 0, "success_rate": 0.0, "mean_score": 0.0}
    return {
        "runs": len(rows),
        "success_rate": sum(1 for r in rows if r.get("success")) / len(rows),
        "mean_score": mean(float(r.get("score", 0.0)) for r in rows),
    }
