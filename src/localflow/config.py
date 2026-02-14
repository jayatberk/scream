from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

DEFAULT_CONFIG_TEXT = """# LocalFlow configuration
hotkey = "<cmd_r>"
sample_rate = 16000
whisper_model = "tiny.en"
language = "en"
auto_paste = true
paste_mode = "clipboard" # clipboard | type
enable_voice_commands = true
enable_enhancer = false
enhancer_model_path = ""
enhancer_temperature = 0.1
"""


@dataclass
class FlowConfig:
    hotkey: str
    sample_rate: int
    whisper_model: str
    language: str | None
    auto_paste: bool
    paste_mode: str
    enable_voice_commands: bool
    enable_enhancer: bool
    enhancer_model_path: str
    enhancer_temperature: float


def app_support_directory() -> Path:
    return Path.home() / "Library" / "Application Support" / "localflow"


def default_config_path() -> Path:
    return app_support_directory() / "config.toml"


def model_directory() -> Path:
    return app_support_directory() / "models"


def history_file_path() -> Path:
    return app_support_directory() / "history.jsonl"


def ensure_default_config(path: Path | None = None, overwrite: bool = False) -> Path:
    target = path or default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if overwrite or not target.exists():
        target.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
    return target


def set_enable_enhancer(enabled: bool, path: Path | None = None) -> Path:
    target = ensure_default_config(path)
    value = "true" if enabled else "false"
    content = target.read_text(encoding="utf-8")
    pattern = r"(?m)^(\s*enable_enhancer\s*=\s*)(?:true|false|[^\n#]+)(\s*(?:#.*)?)$"
    updated, count = re.subn(pattern, rf"\1{value}\2", content, count=1)
    if count == 0:
        if updated and not updated.endswith("\n"):
            updated += "\n"
        updated += f"enable_enhancer = {value}\n"
    target.write_text(updated, encoding="utf-8")
    return target


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def _as_int(value: object, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _as_float(value: object, default: float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    return default


def load_config(path: Path | None = None) -> FlowConfig:
    target = path or default_config_path()
    if not target.exists():
        ensure_default_config(target)
    data = _parse_config_text(target.read_text(encoding="utf-8"))

    hotkey = _normalize_hotkey(str(data.get("hotkey", "<cmd_r>")))
    sample_rate = _as_int(data.get("sample_rate", 16000), 16000)
    whisper_model = str(data.get("whisper_model", "tiny.en"))

    raw_language = data.get("language", "en")
    language = None if raw_language in {"", None} else str(raw_language)

    auto_paste = _as_bool(data.get("auto_paste", True), True)
    paste_mode = str(data.get("paste_mode", "clipboard")).strip().lower()
    if paste_mode not in {"clipboard", "type"}:
        paste_mode = "clipboard"

    enable_voice_commands = _as_bool(data.get("enable_voice_commands", True), True)
    enable_enhancer = _as_bool(data.get("enable_enhancer", False), False)
    enhancer_model_path = str(data.get("enhancer_model_path", "")).strip()
    enhancer_temperature = _as_float(data.get("enhancer_temperature", 0.1), 0.1)

    return FlowConfig(
        hotkey=hotkey,
        sample_rate=sample_rate,
        whisper_model=whisper_model,
        language=language,
        auto_paste=auto_paste,
        paste_mode=paste_mode,
        enable_voice_commands=enable_voice_commands,
        enable_enhancer=enable_enhancer,
        enhancer_model_path=enhancer_model_path,
        enhancer_temperature=enhancer_temperature,
    )


def _parse_config_text(text: str) -> dict[str, object]:
    if tomllib is not None:
        return tomllib.loads(text)
    return _parse_flat_toml_like(text)


def _parse_flat_toml_like(text: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        parsed[key] = _parse_scalar(value)
    return parsed


def _parse_scalar(value: str) -> object:
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1]
    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        return value[1:-1]

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"

    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _normalize_hotkey(hotkey: str) -> str:
    normalized = hotkey.strip()
    # Backward compatibility for older config examples.
    normalized = normalized.replace("+space", "+<space>")
    normalized = normalized.replace("+ Space", "+<space>")
    normalized = normalized.replace("+SPACE", "+<space>")
    if normalized in {"cmd_r", "right_cmd", "right command", "right-command"}:
        return "<cmd_r>"
    if normalized in {
        "cmd+shift",
        "cmd + shift",
        "command+shift",
        "command + shift",
        "<cmd>+shift",
        "<cmd>+<shift>",
        "cmd+<shift>",
        "cmd_r+space",
        "cmd_r+<space>",
        "cmd_r + space",
        "right command + space",
        "right-command+space",
        "<cmd_r>+space",
        "<cmd_r>+<space>",
    }:
        return "<cmd>+<shift>"
    if normalized in {
        "cmd_r+shift_r",
        "right command + right shift",
        "right-command+right-shift",
        "<cmd_r>+<shift_r>",
        "<cmd_r>+<shift>",
        "<cmd_r>+shift_r",
    }:
        return "<cmd_r>"
    return normalized
