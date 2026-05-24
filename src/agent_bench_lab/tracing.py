from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class TraceLogger:
    def __init__(self, path: Path, run_id: str):
        self.path = path
        self.run_id = run_id
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, event_type: str, actor: str, metadata: dict[str, Any] | None = None, input_text: str | None = None, output_text: str | None = None) -> None:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "event_type": event_type,
            "actor": actor,
            "metadata": metadata or {},
        }
        if input_text is not None:
            payload["input_hash"] = sha256_text(input_text)
        if output_text is not None:
            payload["output_hash"] = sha256_text(output_text)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
