from __future__ import annotations

import asyncio
import json
from pathlib import Path

from hf_tui.app import HfTuiApp
from textual.css.query import NoMatches
from textual.widgets import Button


def test_live_tui_load_base_and_chat_models(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "cache_dir": str(cache_dir),
                "active_model": "mock",
                "temperature": 0.0,
                "max_new_tokens": 12,
                "thinking": False,
                "checkpoints": [],
            }
        )
    )

    async def run() -> None:
        app = HfTuiApp(config_path=cfg)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            model_input = screen.query_one("#model")
            prompt_input = screen.query_one("#prompt")
            chat = screen.query_one("#chat")

            model_input.value = "roneneldan/TinyStories-33M"
            screen.query_one("#load", Button).press()
            await pilot.pause()
            prompt_input.value = "Write one short sentence about a cat."
            screen.query_one("#send", Button).press()
            await pilot.pause()
            assert "Assistant:" in chat.text

            model_input.value = "HuggingFaceTB/SmolLM2-135M-Instruct"
            screen.query_one("#load", Button).press()
            await pilot.pause()
            prompt_input.value = "Say hello in five words."
            screen.query_one("#send", Button).press()
            await pilot.pause()
            assert "Assistant:" in chat.text

    asyncio.run(run())

    saved = json.loads(cfg.read_text())
    assert "roneneldan/TinyStories-33M" in saved["checkpoints"]
    assert "HuggingFaceTB/SmolLM2-135M-Instruct" in saved["checkpoints"]


def test_model_menu_is_modal_popup(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "cache_dir": str(tmp_path / "cache"),
                "active_model": "mock",
                "temperature": 0.0,
                "max_new_tokens": 12,
                "thinking": False,
                "checkpoints": [],
            }
        )
    )

    async def run() -> None:
        app = HfTuiApp(config_path=cfg)
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            try:
                screen.query_one("#models")
                raise AssertionError("models list should not exist in chat screen")
            except NoMatches:
                pass

            screen.action_manage_models()
            await pilot.pause()

            modal = app.screen
            modal.query_one("#manage_input").value = "https://huggingface.co/org/model"
            modal.query_one("#add", Button).press()
            await pilot.pause()
            modal.query_one("#close", Button).press()
            await pilot.pause()

    asyncio.run(run())
    saved = json.loads(cfg.read_text())
    assert "org/model" in saved["checkpoints"]
