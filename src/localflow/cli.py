from __future__ import annotations

import argparse
from pathlib import Path
import sys

from localflow.config import (
    default_config_path,
    ensure_default_config,
    load_config,
    model_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="localflow",
        description="Fully local Wispr Flow-style dictation assistant.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create default local config.")
    init_parser.add_argument("--config", type=Path, default=None, help="Custom config path.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing config.")

    run_parser = subparsers.add_parser("run", help="Run global hotkey dictation.")
    run_parser.add_argument("--config", type=Path, default=None, help="Custom config path.")

    check_parser = subparsers.add_parser("check", help="Show resolved runtime configuration.")
    check_parser.add_argument("--config", type=Path, default=None, help="Custom config path.")

    return parser


def command_init(config_path: Path | None, force: bool) -> int:
    path = ensure_default_config(config_path, overwrite=force)
    models = model_directory()
    models.mkdir(parents=True, exist_ok=True)

    print(f"Config ready: {path}")
    print(f"Model directory: {models}")
    print("Optional local rewrite model downloader: scripts/download_tinyllama.sh")
    return 0


def command_check(config_path: Path | None) -> int:
    config = load_config(config_path)
    print(f"Config path: {config_path or default_config_path()}")
    print(f"Hotkey: {config.hotkey}")
    print(f"Whisper model: {config.whisper_model}")
    print(f"Language: {config.language}")
    print(f"Auto paste: {config.auto_paste}")
    print(f"Paste mode: {config.paste_mode}")
    print(f"Voice commands: {config.enable_voice_commands}")
    print(f"Enhancer enabled: {config.enable_enhancer}")
    print(f"Enhancer model path: {config.enhancer_model_path or '(not set)'}")
    return 0


def command_run(config_path: Path | None) -> int:
    if sys.platform != "darwin":
        print("LocalFlow currently supports macOS only.")
        return 1
    from localflow.app import LocalFlowApp

    config = load_config(config_path)
    app = LocalFlowApp(config)
    app.run()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return command_init(args.config, args.force)
    if args.command == "check":
        return command_check(args.config)
    if args.command == "run":
        return command_run(args.config)

    parser.print_help(sys.stderr)
    return 2
