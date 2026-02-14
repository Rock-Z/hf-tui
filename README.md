# hf-tui

Very small Textual TUI for Hugging Face models with:
- frontend/backend split,
- one persistent config file,
- isolated cache dir,
- model-management popup (inspect/add/delete),
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

## Quick guide
1. Install deps:
   ```bash
   uv sync
   ```
2. Run app:
   ```bash
   uv run hf-tui --config .hf-tui/config.json
   ```
3. Load a model in the top input and click **Load**.
4. Chat in the prompt box and click **Send**.
5. Open model manager popup with **Models** button (or press `m`) to add/delete/inspect checkpoints.
6. Edit `.hf-tui/config.json` directly any time to change default model/settings/checkpoints.

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

## Interactive harness (click + keyboard)
Run end-to-end harness tests that drive the real app via Textual pilot:
```bash
python -m pytest -q tests/test_tui_harness.py tests/test_live_tui_app.py tests/test_ui_button_matrix.py
```

Use the flexible action-runner for **ad-hoc agent testing** (not hard-coded to one flow):
```bash
PYTHONPATH=src python tools/tui_pilot.py   --config .hf-tui/harness-config.json   --actions tools/scenarios/smoke_click_and_keys.json

PYTHONPATH=src python tools/tui_pilot.py   --config .hf-tui/harness-config.json   --actions tools/scenarios/enter_submit_path.json
```
Action format supports ops like `set`, `click`, `key`, `focus`, `assert_contains`, `assert_exists`, `assert_not_exists`, and `pause`, so you can rapidly craft new interaction sequences while implementing features.

## Optional tmux smoke run
If you want terminal-level capture while the app runs, use:
```bash
bash tools/run_tui_tmux_smoke.sh
cat .hf-tui/smoke-tmux.log
```
This is useful for debugging focus/keypress flows from a pseudo-real terminal session.


Guide/button verification command:
```bash
python -m pytest -q tests/test_ui_button_matrix.py
```
