from __future__ import annotations

import asyncio
import json
from pathlib import Path

from tools.tui_pilot import run_actions


def test_all_primary_buttons_work_and_match_guide(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "cache_dir": str(tmp_path / "cache"),
                "active_model": "mock",
                "temperature": 0.0,
                "max_new_tokens": 8,
                "thinking": False,
                "checkpoints": [],
            }
        )
    )

    actions = [
        # Top row: load + open models
        {"op": "set", "target": "#model", "value": "mock"},
        {"op": "click", "target": "#load"},
        {"op": "click", "target": "#open_models"},
        # Modal buttons: add / refresh / delete / close
        {"op": "set", "target": "#manage_input", "value": "https://huggingface.co/org/model"},
        {"op": "click", "target": "#add"},
        {"op": "click", "target": "#refresh"},
        {"op": "set", "target": "#manage_input", "value": "org/model"},
        {"op": "click", "target": "#delete"},
        {"op": "click", "target": "#close"},
        # Chat actions: send button + enter key send
        {"op": "set", "target": "#prompt", "value": "button send works"},
        {"op": "click", "target": "#send"},
        {"op": "assert_contains", "target": "#chat", "value": "button send works"},
        {"op": "set", "target": "#prompt", "value": "enter send works"},
        {"op": "focus", "target": "#prompt"},
        {"op": "key", "value": "enter"},
        {"op": "assert_contains", "target": "#chat", "value": "enter send works"},
        # Download log from load action
        {"op": "assert_contains", "target": "#download_log", "value": "Starting load: mock"},
    ]

    asyncio.run(run_actions(cfg, actions))
    saved = json.loads(cfg.read_text())
    assert "org/model" not in saved["checkpoints"]
