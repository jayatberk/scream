from __future__ import annotations

import re


def apply_voice_commands(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""

    replacements = (
        ("new paragraph", "\n\n"),
        ("new line", "\n"),
    )
    for spoken, token in replacements:
        cleaned = re.sub(rf"\b{re.escape(spoken)}\b", token, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[ \t]*\n[ \t]*", "\n", cleaned)
    return cleaned.strip()

