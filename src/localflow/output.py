from __future__ import annotations

import time

import pyperclip

try:
    import pyautogui
except Exception:
    pyautogui = None


def _paste_shortcut() -> tuple[str, str]:
    return ("command", "v")


def emit_text(text: str, auto_paste: bool, paste_mode: str) -> None:
    if not text:
        return

    if not auto_paste:
        print(text)
        return

    if paste_mode == "type":
        if pyautogui is None:
            print(text)
            return
        pyautogui.write(text, interval=0.0)
        return

    pyperclip.copy(text)
    if pyautogui is None:
        print(text)
        return
    time.sleep(0.05)
    modifier, key = _paste_shortcut()
    pyautogui.hotkey(modifier, key)
