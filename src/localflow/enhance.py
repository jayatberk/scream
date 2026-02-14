from __future__ import annotations

from pathlib import Path
import os


class LocalEnhancer:
    def __init__(self, enabled: bool, model_path: str, temperature: float = 0.1) -> None:
        self.enabled = enabled
        self.model_path = model_path
        self.temperature = temperature
        self._model = None
        self._error: str | None = None
        if self.enabled:
            self._load()

    @property
    def status(self) -> str:
        if not self.enabled:
            return "disabled"
        if self._error:
            return f"disabled ({self._error})"
        return "enabled"

    def _load(self) -> None:
        if not self.model_path:
            self._error = "enhancer_model_path is empty"
            return

        model_file = Path(self.model_path).expanduser()
        if not model_file.exists():
            self._error = f"model file not found: {model_file}"
            return

        try:
            from llama_cpp import Llama
        except Exception:
            self._error = "llama-cpp-python not installed"
            return

        threads = max(1, (os.cpu_count() or 2) - 1)
        self._model = Llama(
            model_path=str(model_file),
            n_ctx=2048,
            n_threads=threads,
            verbose=False,
        )

    def enhance(self, text: str) -> str:
        if not text.strip() or self._model is None:
            return text

        prompt = (
            "You clean raw speech-to-text output.\n"
            "Rules:\n"
            "- Preserve meaning.\n"
            "- Keep wording close to the original.\n"
            "- Fix punctuation, capitalization, and obvious transcription mistakes.\n"
            "- Return only cleaned text.\n\n"
            f"Input:\n{text}\n\n"
            "Cleaned:"
        )
        max_tokens = max(64, min(256, len(text) * 2))
        completion = self._model.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=self.temperature,
            top_p=0.9,
            stop=["\n\nInput:", "\n\nRules:"],
        )
        generated = completion["choices"][0]["text"].strip()
        return generated or text

