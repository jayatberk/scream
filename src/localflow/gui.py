from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tkinter as tk

from localflow.config import history_file_path
from localflow.history import HistoryEntry, read_recent_history


class LocalFlowGUI:
    def __init__(self, _config_path: Path | None = None) -> None:
        self.history_path = history_file_path()
        self.root = tk.Tk()
        self.root.title("LocalFlow History")
        self.root.geometry("860x560")
        self.root.minsize(700, 460)
        self.root.configure(bg="#edf2f7")

        self.status_text = tk.StringVar(value="Ready.")

        self._build_layout()
        self.refresh_from_disk()
        self._schedule_refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _build_layout(self) -> None:
        container = tk.Frame(self.root, bg="#edf2f7", padx=18, pady=18)
        container.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            container,
            text="LocalFlow Speech History",
            bg="#edf2f7",
            fg="#0f172a",
            font=("Helvetica", 22, "bold"),
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            container,
            text="Read-only dashboard. Dictation and transcription run separately.",
            bg="#edf2f7",
            fg="#334155",
            font=("Helvetica", 12),
        )
        subtitle.pack(anchor="w", pady=(2, 10))

        history_path_label = tk.Label(
            container,
            text=f"History file: {self.history_path}",
            bg="#edf2f7",
            fg="#475569",
            font=("Menlo", 10),
        )
        history_path_label.pack(anchor="w", pady=(0, 10))

        top = tk.Frame(container, bg="#edf2f7")
        top.pack(fill=tk.X, pady=(0, 10))

        refresh_btn = tk.Button(
            top,
            text="Refresh",
            command=self.refresh_from_disk,
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            font=("Helvetica", 12, "bold"),
        )
        refresh_btn.pack(side=tk.LEFT)

        history_frame = tk.Frame(container, bg="#edf2f7")
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_canvas = tk.Canvas(
            history_frame,
            bg="#edf2f7",
            highlightthickness=0,
            borderwidth=0,
        )
        self.history_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_canvas.configure(yscrollcommand=scrollbar.set)

        self.cards_frame = tk.Frame(self.history_canvas, bg="#edf2f7")
        self.cards_window = self.history_canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.cards_frame.bind("<Configure>", self._on_cards_configure)
        self.history_canvas.bind("<Configure>", self._on_canvas_configure)

        status_label = tk.Label(
            container,
            textvariable=self.status_text,
            bg="#edf2f7",
            fg="#334155",
            font=("Helvetica", 11),
        )
        status_label.pack(anchor="w", pady=(8, 0))

    def _on_cards_configure(self, _event) -> None:
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.history_canvas.itemconfigure(self.cards_window, width=event.width)

    def refresh_from_disk(self) -> None:
        try:
            entries = read_recent_history(limit=10, path=self.history_path)
            self._render_entries(entries)
            self.status_text.set(f"Showing {len(entries)} item(s). Last refresh: {self._now_label()}")
        except Exception as exc:
            self.status_text.set(f"Refresh failed: {exc}")
            self._render_entries([])

    def _render_entries(self, entries: list[HistoryEntry]) -> None:
        for child in self.cards_frame.winfo_children():
            child.destroy()

        if not entries:
            empty = tk.Label(
                self.cards_frame,
                text="No speech history yet.\nRun dictation to populate this view.",
                bg="#edf2f7",
                fg="#64748b",
                justify=tk.LEFT,
                font=("Helvetica", 12),
                padx=4,
                pady=12,
            )
            empty.pack(anchor="w")
            return

        for entry in entries:
            card = tk.Frame(self.cards_frame, bg="white", bd=1, relief=tk.SOLID, padx=12, pady=10)
            card.pack(fill=tk.X, pady=(0, 10))

            top = tk.Frame(card, bg="white")
            top.pack(fill=tk.X)

            timestamp_label = tk.Label(
                top,
                text=self._format_timestamp(entry.timestamp),
                bg="white",
                fg="#0f172a",
                font=("Helvetica", 11, "bold"),
            )
            timestamp_label.pack(side=tk.LEFT)

            mode_label = tk.Label(
                top,
                text=entry.mode,
                bg="#dbeafe" if entry.mode == "post-enhancer" else "#e2e8f0",
                fg="#1e3a8a" if entry.mode == "post-enhancer" else "#334155",
                font=("Helvetica", 10, "bold"),
                padx=8,
                pady=2,
            )
            mode_label.pack(side=tk.RIGHT)

            text_label = tk.Label(
                card,
                text=entry.text,
                bg="white",
                fg="#111827",
                justify=tk.LEFT,
                anchor="w",
                wraplength=760,
                font=("Helvetica", 13),
                pady=8,
            )
            text_label.pack(fill=tk.X)

    def _schedule_refresh(self) -> None:
        self.root.after(2000, self._auto_refresh)

    def _auto_refresh(self) -> None:
        try:
            entries = read_recent_history(limit=10, path=self.history_path)
            self._render_entries(entries)
            self.status_text.set(f"Showing {len(entries)} item(s). Last refresh: {self._now_label()}")
        except Exception:
            pass
        self._schedule_refresh()

    def _format_timestamp(self, timestamp: str) -> str:
        if not timestamp:
            return "Unknown time"
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%b %d, %Y %I:%M:%S %p")
        except ValueError:
            return timestamp

    def _now_label(self) -> str:
        return datetime.now().strftime("%I:%M:%S %p")

    def run(self) -> None:
        self.root.mainloop()


def run_gui(config_path: Path | None = None) -> None:
    LocalFlowGUI(config_path).run()
