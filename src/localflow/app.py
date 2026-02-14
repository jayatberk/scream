from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time
import sys

from pynput import keyboard

from localflow.audio import AudioRecorder
from localflow.commands import apply_voice_commands
from localflow.config import FlowConfig
from localflow.enhance import LocalEnhancer
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
        self._hotkey = keyboard.HotKey(keyboard.HotKey.parse(config.hotkey), self._toggle_recording)
        self._state_lock = threading.Lock()
        self._processing = False
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _on_press(self, key: keyboard.KeyCode | keyboard.Key) -> None:
        if self._listener is None:
            return
        self._hotkey.press(self._listener.canonical(key))

    def _on_release(self, key: keyboard.KeyCode | keyboard.Key) -> None:
        if self._listener is None:
            return
        self._hotkey.release(self._listener.canonical(key))

    def _toggle_recording(self) -> None:
        with self._state_lock:
            if self._processing:
                print("[localflow] Still processing previous clip.")
                return

            if self.recorder.recording:
                audio, duration = self.recorder.stop()
                if duration < 0.2 or audio.size == 0:
                    print("[localflow] Clip too short.")
                    return
                self._processing = True
                print(f"[localflow] Processing {duration:.1f}s clip...")
                self._executor.submit(self._process_audio, audio)
                return

            self.recorder.start()
            print("[localflow] Recording...")

    def _process_audio(self, audio) -> None:
        try:
            text = self.transcriber.transcribe(audio, language=self.config.language)
            if self.config.enable_voice_commands:
                text = apply_voice_commands(text)
            if self.config.enable_enhancer:
                text = self.enhancer.enhance(text)

            if text:
                emit_text(text, auto_paste=self.config.auto_paste, paste_mode=self.config.paste_mode)
                print(f"[localflow] {text}")
            else:
                print("[localflow] No speech detected.")
        except Exception as exc:
            print(f"[localflow] Error: {exc}")
        finally:
            with self._state_lock:
                self._processing = False

    def run(self) -> None:
        print("[localflow] Running in fully local mode.")
        print(f"[localflow] Hotkey: {self.config.hotkey}")
        print(f"[localflow] Whisper model: {self.config.whisper_model}")
        print(f"[localflow] Enhancer: {self.enhancer.status}")
        print("[localflow] Press Ctrl+C to exit.")

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

        try:
            while self._listener.is_alive():
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        if self.recorder.recording:
            self.recorder.stop()
        if self._listener is not None:
            self._listener.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)
