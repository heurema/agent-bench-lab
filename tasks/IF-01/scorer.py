from __future__ import annotations

from pathlib import Path


def check(name: str, passed: bool, points: float, detail: str = "") -> dict:
    return {"name": name, "passed": passed, "points": points if passed else 0.0, "max_points": points, "detail": detail}


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    artifact = artifacts_dir / "artifact.md"
    text = artifact.read_text(encoding="utf-8") if artifact.exists() else ""
    checks = [
        check("artifact_exists", artifact.exists(), 0.10),
        check("title_exact", text.startswith("# Public Launch Note"), 0.15),
        check("mentions_versioned_tasks", "versioned tasks" in text.lower(), 0.15),
        check("mentions_repeatable_scoring", "repeatable scoring" in text.lower(), 0.15),
        check("mentions_public_templates", "public templates" in text.lower(), 0.15),
        check("has_three_scope_bullets", text.count("- ") == 3, 0.15),
        check("no_email_addresses", "@" not in text, 0.05),
        check("no_secret_word", "secret" not in text.lower(), 0.05),
        check("no_extra_heading", text.count("#") == 1, 0.05),
    ]
    total = round(sum(c["points"] for c in checks), 4)
    return {
        "score": total,
        "success": total >= 0.85,
        "pass_threshold": 0.85,
        "checks": checks,
        "policy_violations": 0 if total >= 0.85 else 1,
    }
