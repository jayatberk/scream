from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from localflow.config import history_file_path


@dataclass
class HistoryEntry:
    timestamp: str
    text: str


def append_history(text: str, path: Path | None = None, max_entries: int = 1000) -> None:
    cleaned = text.strip()
    if not cleaned:
        return

    target = path or history_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "text": cleaned,
    }
    try:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError:
        return

    _truncate_history(target, max_entries=max_entries)


def read_recent_history(limit: int = 10, path: Path | None = None) -> list[HistoryEntry]:
    target = path or history_file_path()
    if limit <= 0 or not target.exists():
        return []

    lines: deque[str] = deque(maxlen=limit)
    try:
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    except OSError:
        return []

    results: list[HistoryEntry] = []
    for raw in reversed(lines):
        try:
            payload = json.loads(raw)
            timestamp = str(payload.get("timestamp", ""))
            text = str(payload.get("text", "")).strip()
            if text:
                results.append(HistoryEntry(timestamp=timestamp, text=text))
        except Exception:
            results.append(HistoryEntry(timestamp="", text=raw))
    return results


def _truncate_history(path: Path, max_entries: int) -> None:
    if max_entries <= 0 or not path.exists():
        return

    kept: deque[str] = deque(maxlen=max_entries)
    total = 0
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                total += 1
                kept.append(stripped)
    except OSError:
        return

    if total <= max_entries:
        return

    try:
        with path.open("w", encoding="utf-8") as handle:
            for line in kept:
                handle.write(line + "\n")
    except OSError:
        return
