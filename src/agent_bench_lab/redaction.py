from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"
REDACTED_KEY = "[REDACTED_KEY]"

UNSAFE_TEXT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\banswer[_ -]?key\b",
        r"\bhidden[_ -]?label(s)?\b",
        r"\bprivate[_ -]?threshold\b",
        r"\bprotected[_ -]?scorer[_ -]?config\b",
        r"\bscorer[_ -]?config\b",
        r"\bcanary\b",
        r"\bCANARY_",
        r"\bHONEY_",
        r"\bhoney row\b",
        r"\bsecret\b",
        r"\btoken\b",
        r"\bapi[_ -]?key\b",
        r"\bexpected\s*=",
        r"\bexpected\s*:",
        r"\bcorrect answer\b",
        r"\bprivate rubric\b",
        r"\bcustomer[_ -]?private\b",
        r"fixtures/private",
        r"(^|/)private/",
        r"\braw[_ -]?trace\b",
        r"\braw[_ -]?diagnostics\b",
    ]
]


def is_public_safe_text(text: str) -> bool:
    return not any(pattern.search(text) for pattern in UNSAFE_TEXT_PATTERNS)


def redact_text(text: str) -> str:
    if is_public_safe_text(text):
        return text
    return REDACTED


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, Mapping):
        redacted: dict[str, Any] = {}
        for key, value in obj.items():
            safe_key = str(key) if is_public_safe_text(str(key)) else REDACTED_KEY
            redacted[safe_key] = redact_obj(value)
        return redacted
    if isinstance(obj, tuple):
        return tuple(redact_obj(item) for item in obj)
    if isinstance(obj, Sequence) and not isinstance(obj, bytes | bytearray):
        return [redact_obj(item) for item in obj]
    return obj
