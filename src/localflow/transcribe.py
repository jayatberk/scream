from __future__ import annotations

import numpy as np
from faster_whisper import WhisperModel


class WhisperTranscriber:
    def __init__(self, model_name: str = "tiny.en", device: str = "auto") -> None:
        self.model = WhisperModel(model_name, device=device, compute_type="int8")

    def transcribe(self, audio: np.ndarray, language: str | None = "en") -> str:
        if audio.size == 0:
            return ""

        segments, _info = self.model.transcribe(
            audio,
            language=language,
            beam_size=1,
            best_of=1,
            vad_filter=True,
            condition_on_previous_text=False,
            temperature=0.0,
        )
        parts = [segment.text.strip() for segment in segments if segment.text and segment.text.strip()]
        return " ".join(parts).strip()

