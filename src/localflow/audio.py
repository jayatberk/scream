from __future__ import annotations

from dataclasses import dataclass, field
import threading
import time

import numpy as np
import sounddevice as sd


@dataclass
class AudioRecorder:
    sample_rate: int = 16000
    channels: int = 1
    blocksize: int = 1024
    dtype: str = "float32"
    _frames: list[np.ndarray] = field(default_factory=list)
    _stream: sd.InputStream | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _started_at: float | None = None

    @property
    def recording(self) -> bool:
        return self._stream is not None

    def _callback(self, indata, _frames, _time, _status) -> None:
        with self._lock:
            self._frames.append(indata.copy())

    def start(self) -> None:
        if self._stream is not None:
            return
        with self._lock:
            self._frames.clear()
        self._started_at = time.monotonic()
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.blocksize,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> tuple[np.ndarray, float]:
        stream = self._stream
        self._stream = None
        started_at = self._started_at
        self._started_at = None

        if stream is None:
            return np.array([], dtype=np.float32), 0.0

        stream.stop()
        stream.close()

        with self._lock:
            if not self._frames:
                return np.array([], dtype=np.float32), 0.0
            audio = np.concatenate(self._frames, axis=0).reshape(-1).astype(np.float32)
            self._frames.clear()

        duration = 0.0 if started_at is None else max(0.0, time.monotonic() - started_at)
        return audio, duration

