from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from localflow.config import default_config_path, load_config, set_enable_enhancer
from localflow.history import read_recent_history


class LocalFlowGUI:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or default_config_path()
        self.root = tk.Tk()
        self.root.title("LocalFlow")
        self.root.geometry("760x460")
        self.root.minsize(640, 400)

        self.enhancer_enabled = tk.BooleanVar(value=False)
        self.status_text = tk.StringVar(value="")

        self._build_layout()
        self.refresh_from_disk()
        self._schedule_refresh()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(container, text="LocalFlow Settings", font=("Helvetica", 17, "bold"))
        title.pack(anchor="w")

        subtitle = ttk.Label(
            container,
            text="Toggle enhancer and view your last 10 spoken entries.",
        )
        subtitle.pack(anchor="w", pady=(2, 10))

        top = ttk.Frame(container)
        top.pack(fill=tk.X, pady=(0, 10))

        toggle = ttk.Checkbutton(
            top,
            text="Enable enhancer",
            variable=self.enhancer_enabled,
        )
        toggle.pack(side=tk.LEFT)

        save_btn = ttk.Button(top, text="Save", command=self.save_settings)
        save_btn.pack(side=tk.LEFT, padx=(8, 0))

        refresh_btn = ttk.Button(top, text="Refresh", command=self.refresh_from_disk)
        refresh_btn.pack(side=tk.LEFT, padx=(8, 0))

        config_label = ttk.Label(container, text=f"Config: {self.config_path}")
        config_label.pack(anchor="w", pady=(0, 8))

        history_label = ttk.Label(container, text="Last 10 spoken items")
        history_label.pack(anchor="w")

        history_frame = ttk.Frame(container)
        history_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_list = tk.Listbox(
            history_frame,
            yscrollcommand=scrollbar.set,
            font=("Menlo", 12),
            activestyle="none",
        )
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_list.yview)

        status_label = ttk.Label(container, textvariable=self.status_text)
        status_label.pack(anchor="w", pady=(8, 0))

    def refresh_from_disk(self) -> None:
        config = load_config(self.config_path)
        self.enhancer_enabled.set(config.enable_enhancer)
        self._refresh_history()
        self.status_text.set("Loaded current config and history.")

    def _refresh_history(self) -> None:
        entries = read_recent_history(limit=10)
        self.history_list.delete(0, tk.END)
        if not entries:
            self.history_list.insert(tk.END, "No speech history yet.")
            return

        for entry in entries:
            prefix = entry.timestamp if entry.timestamp else "unknown-time"
            self.history_list.insert(tk.END, f"{prefix}  {entry.text}")

    def save_settings(self) -> None:
        set_enable_enhancer(self.enhancer_enabled.get(), self.config_path)
        state = "on" if self.enhancer_enabled.get() else "off"
        self.status_text.set(f"Saved: enhancer is {state}.")
        self._refresh_history()

    def _schedule_refresh(self) -> None:
        self.root.after(2500, self._auto_refresh)

    def _auto_refresh(self) -> None:
        self._refresh_history()
        self._schedule_refresh()

    def run(self) -> None:
        self.root.mainloop()


def run_gui(config_path: Path | None = None) -> None:
    LocalFlowGUI(config_path).run()
