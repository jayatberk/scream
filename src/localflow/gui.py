from __future__ import annotations

from pathlib import Path
import tkinter as tk

from localflow.config import default_config_path, load_config, set_enable_enhancer
from localflow.history import read_recent_history


class LocalFlowGUI:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or default_config_path()
        self.root = tk.Tk()
        self.root.title("LocalFlow")
        self.root.geometry("760x460")
        self.root.minsize(640, 400)
        self.root.configure(bg="#f3f4f6")

        self.enhancer_enabled = tk.BooleanVar(value=False)
        self.status_text = tk.StringVar(value="")

        self._build_layout()
        self.refresh_from_disk()
        self._schedule_refresh()

    def _build_layout(self) -> None:
        container = tk.Frame(self.root, bg="#f3f4f6", padx=16, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            container,
            text="LocalFlow Settings",
            bg="#f3f4f6",
            fg="#0f172a",
            font=("Helvetica", 18, "bold"),
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            container,
            text="Toggle enhancer and view your last 10 spoken entries.",
            bg="#f3f4f6",
            fg="#334155",
            font=("Helvetica", 13),
        )
        subtitle.pack(anchor="w", pady=(2, 10))

        top = tk.Frame(container, bg="#f3f4f6")
        top.pack(fill=tk.X, pady=(0, 10))

        toggle = tk.Checkbutton(
            top,
            text="Enable enhancer",
            variable=self.enhancer_enabled,
            bg="#f3f4f6",
            fg="#111827",
            selectcolor="#ffffff",
            font=("Helvetica", 13),
            activebackground="#f3f4f6",
        )
        toggle.pack(side=tk.LEFT)

        save_btn = tk.Button(
            top,
            text="Save",
            command=self.save_settings,
            bg="#0ea5e9",
            fg="white",
            activebackground="#0284c7",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            font=("Helvetica", 12, "bold"),
        )
        save_btn.pack(side=tk.LEFT, padx=(8, 0))

        refresh_btn = tk.Button(
            top,
            text="Refresh",
            command=self.refresh_from_disk,
            bg="#e2e8f0",
            fg="#0f172a",
            activebackground="#cbd5e1",
            relief=tk.FLAT,
            padx=10,
            pady=6,
            font=("Helvetica", 12),
        )
        refresh_btn.pack(side=tk.LEFT, padx=(8, 0))

        config_label = tk.Label(
            container,
            text=f"Config: {self.config_path}",
            bg="#f3f4f6",
            fg="#475569",
            font=("Helvetica", 11),
        )
        config_label.pack(anchor="w", pady=(0, 8))

        history_label = tk.Label(
            container,
            text="Last 10 spoken items",
            bg="#f3f4f6",
            fg="#0f172a",
            font=("Helvetica", 13, "bold"),
        )
        history_label.pack(anchor="w")

        history_frame = tk.Frame(container, bg="#f3f4f6")
        history_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_list = tk.Listbox(
            history_frame,
            yscrollcommand=scrollbar.set,
            font=("Menlo", 12),
            activestyle="none",
            bg="white",
            fg="#0f172a",
            selectbackground="#0ea5e9",
            selectforeground="white",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            highlightcolor="#0ea5e9",
        )
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_list.yview)

        status_label = tk.Label(
            container,
            textvariable=self.status_text,
            bg="#f3f4f6",
            fg="#334155",
            font=("Helvetica", 11),
        )
        status_label.pack(anchor="w", pady=(8, 0))

    def refresh_from_disk(self) -> None:
        try:
            config = load_config(self.config_path)
            self.enhancer_enabled.set(config.enable_enhancer)
            self._refresh_history()
            self.status_text.set("Loaded current config and history.")
        except Exception as exc:
            self.status_text.set(f"Refresh failed: {exc}")
            self.history_list.delete(0, tk.END)
            self.history_list.insert(tk.END, "Could not load config/history.")

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
        try:
            set_enable_enhancer(self.enhancer_enabled.get(), self.config_path)
            state = "on" if self.enhancer_enabled.get() else "off"
            self.status_text.set(f"Saved: enhancer is {state}.")
            self._refresh_history()
        except Exception as exc:
            self.status_text.set(f"Save failed: {exc}")

    def _schedule_refresh(self) -> None:
        self.root.after(2500, self._auto_refresh)

    def _auto_refresh(self) -> None:
        try:
            self._refresh_history()
        except Exception:
            # Keep GUI responsive even if history read fails once.
            pass
        self._schedule_refresh()

    def run(self) -> None:
        self.root.mainloop()


def run_gui(config_path: Path | None = None) -> None:
    LocalFlowGUI(config_path).run()
