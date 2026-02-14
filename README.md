# LocalFlow (Local Wispr Flow Clone)

LocalFlow is a macOS-only, fully local dictation tool:
- Push-to-talk style global hotkey dictation.
- On-device speech-to-text with open-source Whisper (`tiny.en` by default).
- Optional local rewrite/cleanup using a small GGUF model via `llama.cpp`.
- Auto-paste into the currently focused app.

No cloud APIs are required for runtime.

## What It Replicates

- Fast voice capture.
- Real-time transcription.
- Text cleanup for clearer writing.
- Drop text directly where your cursor is.

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.9+
- Microphone access
- `brew install portaudio`
- Accessibility + Input Monitoring permissions for your terminal/app

## Install

```bash
cd /Users/jay/Downloads/loudly
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional rewrite model support:

```bash
pip install -e '.[rewrite]'
```

## Initialize

```bash
localflow init
```

This creates the config file at:

- `~/Library/Application Support/localflow/config.toml`

The app stores local models in:

- `~/Library/Application Support/localflow/models`

## Run

```bash
localflow run
```

Default toggle key: `Right Command + Right Shift` (`<cmd_r>+<shift_r>`)

- Press once: start recording
- Press again: stop, transcribe, clean, and paste

## GUI

Open a simple GUI to:
- View last 10 spoken items

```bash
localflow gui
```

## Optional: Download a Small Local Rewrite Model

```bash
bash scripts/download_tinyllama.sh
```

Then set `enable_enhancer = true` and point `enhancer_model_path` in your config.

## Config

Example config:

```toml
hotkey = "<cmd_r>+<shift_r>"
sample_rate = 16000
whisper_model = "tiny.en"
language = "en"
auto_paste = true
paste_mode = "clipboard" # clipboard or type
enable_voice_commands = true
enable_enhancer = false
enhancer_model_path = ""
enhancer_temperature = 0.1
```

`whisper_model` can be `tiny`, `tiny.en`, `base`, etc. Smaller models are faster and lighter.

## Voice Commands

When enabled:
- Saying `new line` inserts `\n`
- Saying `new paragraph` inserts `\n\n`

## Notes

- This project is designed to stay local at runtime on macOS.
- First Whisper model load may download weights once, then run from local cache.
- Spoken history is stored at `~/Library/Application Support/localflow/history.jsonl`.
