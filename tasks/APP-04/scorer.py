from __future__ import annotations

import json
from pathlib import Path


def score(task_dir: Path, fixture_dir: Path, artifacts_dir: Path) -> dict:
    final_path = artifacts_dir / "final_booking.json"
    msg_path = artifacts_dir / "user_message.txt"
    data = {}
    if final_path.exists():
        data = json.loads(final_path.read_text(encoding="utf-8"))
    checks = []
    def add(name, passed, pts, detail=""):
        checks.append({"name": name, "passed": passed, "points": pts if passed else 0, "max_points": pts, "detail": detail})
    add("final_booking_exists", final_path.exists(), 0.10)
    add("selected_expected_public_flight", data.get("flight_id") == "FL-200", 0.25, "Public sample expected flight FL-200")
    add("arrival_before_1500", str(data.get("arrival_local", "")) <= "2026-05-25T14:30:00", 0.15)
    add("fee_under_limit", float(data.get("change_fee_usd", 9999)) <= 150, 0.15)
    add("cabin_not_downgraded", data.get("cabin") == "economy", 0.10)
    add("aisle_seat", str(data.get("seat", "")).endswith("C") or str(data.get("seat", "")).endswith("D"), 0.10)
    msg = msg_path.read_text(encoding="utf-8") if msg_path.exists() else ""
    add("message_exists", msg_path.exists(), 0.05)
    add("message_mentions_flight", "FL-200" in msg, 0.05)
    add("message_no_private_data", "secret" not in msg.lower() and "api" not in msg.lower(), 0.05)
    total = round(sum(c["points"] for c in checks), 4)
    return {"score": total, "success": total >= 0.85, "checks": checks}
