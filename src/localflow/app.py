from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys
import re

from pynput import keyboard

from localflow.audio import AudioRecorder
from localflow.commands import apply_voice_commands
from localflow.config import FlowConfig
from localflow.enhance import LocalEnhancer
from localflow.history import append_history
from localflow.output import emit_text
from localflow.transcribe import WhisperTranscriber


class LocalFlowApp:
    def __init__(self, config: FlowConfig) -> None:
        if sys.platform != "darwin":
            raise RuntimeError("LocalFlow supports macOS only.")
        self.config = config
        self.recorder = AudioRecorder(sample_rate=config.sample_rate)
        self.transcriber = WhisperTranscriber(model_name=config.whisper_model)
        self.enhancer = LocalEnhancer(
            enabled=config.enable_enhancer,
            model_path=config.enhancer_model_path,
            temperature=config.enhancer_temperature,
        )

        self._listener: keyboard.Listener | None = None
        self._side_specific_hotkey = bool(re.search(r"<(?:cmd|ctrl|shift|alt)_[lr]>", config.hotkey))
        self._hotkey_keys = set(keyboard.HotKey.parse(config.hotkey))
        self._pressed_hotkey_keys: set[keyboard.KeyCode | keyboard.Key] = set()
        self._toggle_mode = config.hotkey == "<cmd_r>+<space>"
        self._hotkey_activated = False
        self._state_lock = threading.Lock()
        self._processing = False
        self._clip_started_at: float | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _on_press(self, key: keyboard.KeyCode | keyboard.Key) -> None:
        if self._listener is None:
            return
        normalized = self._normalize_listener_key(key)
        if normalized not in self._hotkey_keys:
            return
        with self._state_lock:
            self._pressed_hotkey_keys.add(normalized)
            if self._pressed_hotkey_keys == self._hotkey_keys:
                if self._hotkey_activated:
                    return
                self._hotkey_activated = True
                if self._processing:
                    print("[localflow] Still processing previous clip.")
                    return
                if self._toggle_mode:
                    if self.recorder.recording:
                        self._finish_recording_locked()
                    else:
                        self.recorder.start()
                        self._clip_started_at = time.monotonic()
                        print("[localflow] Recording...")
                    return
                if not self.recorder.recording:
                    self.recorder.start()
                    self._clip_started_at = time.monotonic()
                    print("[localflow] Recording...")

    def _on_release(self, key: keyboard.KeyCode | keyboard.Key) -> None:
        if self._listener is None:
            return
        normalized = self._normalize_listener_key(key)
        with self._state_lock:
            self._pressed_hotkey_keys.discard(normalized)
            if self._pressed_hotkey_keys != self._hotkey_keys:
                self._hotkey_activated = False
            if self._toggle_mode:
                return
            if self._processing or not self.recorder.recording:
                return
            if self._pressed_hotkey_keys == self._hotkey_keys:
                return
            self._finish_recording_locked()

    def _normalize_listener_key(self, key: keyboard.KeyCode | keyboard.Key) -> keyboard.KeyCode | keyboard.Key:
        if self._listener is None:
            return key
        if self._side_specific_hotkey and isinstance(key, keyboard.Key) and key.value.vk is not None:
            # Preserve right/left modifier identity for combos like <cmd_r>+<shift_r>.
            return keyboard.KeyCode.from_vk(key.value.vk)
        return self._listener.canonical(key)

    def _finish_recording_locked(self) -> None:
        audio, duration = self.recorder.stop()
        clip_started_at = self._clip_started_at
        self._clip_started_at = None
        if duration < 0.2 or audio.size == 0:
            print("[localflow] Clip too short.")
            return
        self._processing = True
        print(f"[localflow] Processing {duration:.1f}s clip...")
        self._executor.submit(self._process_audio, audio, clip_started_at)

    def _process_audio(self, audio, clip_started_at: float | None) -> None:
        try:
            raw_text = self.transcriber.transcribe(audio, language=self.config.language)
            text = raw_text
            if self.config.enable_voice_commands:
                text = apply_voice_commands(text)
            pre_enhancer_text = text
            enhancer_elapsed: float | None = None
            if self.config.enable_enhancer:
                enhancer_started_at = time.monotonic()
                text = self.enhancer.enhance(text)
                enhancer_elapsed = max(0.0, time.monotonic() - enhancer_started_at)

            if text:
                history_mode = "post-enhancer" if self.config.enable_enhancer else "pre-enhancer"
                history_text = text if self.config.enable_enhancer else pre_enhancer_text
                print(f"[localflow] Before enhancer: {pre_enhancer_text}")
                print(f"[localflow] After enhancer: {text}")
                if enhancer_elapsed is not None:
                    print(f"[localflow] Enhancer time: {enhancer_elapsed:.2f}s")
                append_history(history_text, mode=history_mode)
                emit_text(text, auto_paste=self.config.auto_paste, paste_mode=self.config.paste_mode)
                print(f"[localflow] {text}")
                if clip_started_at is not None:
                    total_elapsed = max(0.0, time.monotonic() - clip_started_at)
                    print(f"[localflow] Start->text time: {total_elapsed:.2f}s")
            else:
                print("[localflow] No speech detected.")
        except Exception as exc:
            print(f"[localflow] Error: {exc}")
        finally:
            with self._state_lock:
                self._processing = False

    def start_hotkey_listener(self, announce: bool = True) -> None:
        if self._listener is not None and self._listener.is_alive():
            return
        if announce:
            print("[localflow] Running in fully local mode.")
            print(f"[localflow] Hotkey: {self.config.hotkey}")
            print(f"[localflow] Whisper model: {self.config.whisper_model}")
            print(f"[localflow] Enhancer: {self.enhancer.status}")
            if self._toggle_mode:
                print("[localflow] Press hotkey to start recording; press again to stop and process.")
            else:
                print("[localflow] Hold hotkey to record, release to process.")
            print("[localflow] Press Ctrl+C to exit.")
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

    def run(self) -> None:
        self.start_hotkey_listener(announce=True)

        try:
            while self._listener is not None and self._listener.is_alive():
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        if self.recorder.recording:
            self.recorder.stop()
            self._clip_started_at = None
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._executor.shutdown(wait=False, cancel_futures=True)
