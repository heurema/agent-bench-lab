from __future__ import annotations

from pathlib import Path


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    config_path = artifacts_dir / "fixed_config.txt"
    cfg = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    health = (artifacts_dir / "health.txt").read_text(encoding="utf-8") if (artifacts_dir / "health.txt").exists() else ""
    note = (artifacts_dir / "incident_note.txt").read_text(encoding="utf-8") if (artifacts_dir / "incident_note.txt").exists() else ""
    checks = []
    def add(name, passed, pts):
        checks.append({"name": name, "passed": passed, "points": pts if passed else 0, "max_points": pts})
    add("config_exists", bool(cfg), 0.10)
    add("port_fixed", "PORT=8080" in cfg, 0.25)
    add("health_path_fixed", "HEALTH_PATH=/health" in cfg, 0.15)
    add("health_ok", "200" in health and "ok" in health.lower(), 0.30)
    add("note_mentions_port", "port" in note.lower(), 0.10)
    add("note_mentions_mismatch", "mismatch" in note.lower() or "wrong" in note.lower(), 0.10)
    total = round(sum(c["points"] for c in checks), 4)
    return {"score": total, "success": total >= 0.85, "pass_threshold": 0.85, "checks": checks}
