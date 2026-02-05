# hf-tui

Very small Textual TUI for Hugging Face models with:
- frontend/backend split,
- one persistent config file,
- isolated cache dir,
- checkpoint menu (inspect/add/delete),
- mock + live tiny-model support.

## Core files (5)
- `src/hf_tui/cli.py`
- `src/hf_tui/app.py`
- `src/hf_tui/ui.py`
- `src/hf_tui/core.py`
- `src/hf_tui/backend.py`

Utilities:
- `src/hf_tui/config.py`

## Config
Single editable file (default): `.hf-tui/config.json`

Example:
```json
{
  "cache_dir": ".hf-tui-cache",
  "active_model": "mock",
  "temperature": 0.7,
  "max_new_tokens": 128,
  "thinking": false,
  "checkpoints": []
}
```

## Run
```bash
uv sync
uv run hf-tui --config .hf-tui/config.json
```

## Notes on generation
- Uses Transformers `pipeline("text-generation")`.
- Uses chat templating when tokenizer has `chat_template`.
- Falls back to plain text prompts for base models without chat templates.

## Live TUI verification
```bash
python -m pytest -q tests/test_live_tui_app.py
```
This drives the Textual TUI and live-loads:
- `roneneldan/TinyStories-33M` (tiny base model)
- `HuggingFaceTB/SmolLM2-135M-Instruct` (tiny chat/instruct model)

