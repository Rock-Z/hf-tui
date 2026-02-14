from __future__ import annotations

import asyncio
import json
from pathlib import Path

from tools.tui_pilot import run_actions


def _cfg(tmp_path: Path) -> Path:
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
    return cfg


def test_tui_harness_click_and_keyboard_paths(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    actions = [
        {"op": "set", "target": "#model", "value": "mock"},
        {"op": "click", "target": "#load"},
        {"op": "set", "target": "#prompt", "value": "hello by click"},
        {"op": "click", "target": "#send"},
        {"op": "action", "value": "action_manage_models"},
        {"op": "set", "target": "#manage_input", "value": "https://huggingface.co/org/model"},
        {"op": "click", "target": "#add"},
        {"op": "key", "value": "escape"},
        {"op": "set", "target": "#prompt", "value": "hello by enter"},
        {"op": "focus", "target": "#prompt"},
        {"op": "key", "value": "enter"},
        {"op": "assert_contains", "target": "#chat", "value": "hello by click"},
        {"op": "assert_contains", "target": "#chat", "value": "hello by enter"},
        {"op": "assert_contains", "target": "#chat", "value": "Echo:"},
    ]
    asyncio.run(run_actions(cfg, actions))

    saved = json.loads(cfg.read_text())
    assert "org/model" in saved["checkpoints"]


def test_tui_harness_allows_alternate_sequences(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    actions = [
        {"op": "assert_not_exists", "target": "#manage_input"},
        {"op": "click", "target": "#open_models"},
        {"op": "assert_exists", "target": "#manage_input"},
        {"op": "set", "target": "#manage_input", "value": "org/another-model"},
        {"op": "click", "target": "#add"},
        {"op": "click", "target": "#close"},
        {"op": "set", "target": "#prompt", "value": "sequence two"},
        {"op": "click", "target": "#send"},
        {"op": "assert_contains", "target": "#chat", "value": "sequence two"},
    ]
    asyncio.run(run_actions(cfg, actions))

    saved = json.loads(cfg.read_text())
    assert "org/another-model" in saved["checkpoints"]
