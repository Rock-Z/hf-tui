from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from hf_tui.app import HfTuiApp
from textual.css.query import NoMatches
from textual.widgets import Button, Input


def _write_default_config(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cache_dir": str(path.parent / "cache"),
                "active_model": "mock",
                "temperature": 0.0,
                "max_new_tokens": 8,
                "thinking": False,
                "checkpoints": [],
            }
        )
    )


async def _find(app: HfTuiApp, pilot, selector: str, expect_type=None):
    for _ in range(20):
        try:
            if expect_type is None:
                return app.screen.query_one(selector)
            return app.screen.query_one(selector, expect_type)
        except NoMatches:
            await pilot.pause()
    if expect_type is None:
        return app.screen.query_one(selector)
    return app.screen.query_one(selector, expect_type)


async def run_actions(config_path: Path, actions: list[dict]) -> None:
    app = HfTuiApp(config_path=config_path)
    async with app.run_test() as pilot:
        await pilot.pause()
        for step in actions:
            op = step["op"]
            target = step.get("target")
            value = step.get("value")

            if op == "pause":
                await pilot.pause()
            elif op == "set":
                (await _find(app, pilot, target, Input)).value = str(value)
            elif op == "focus":
                (await _find(app, pilot, target)).focus()
            elif op == "click":
                (await _find(app, pilot, target, Button)).press()
            elif op == "key":
                await pilot.press(str(value))
            elif op == "action":
                getattr(app.screen, str(value))()
            elif op == "assert_contains":
                node = await _find(app, pilot, target)
                text = getattr(node, "text", None)
                if text is None:
                    text = str(getattr(node, "renderable", ""))
                assert str(value) in str(text), f"'{value}' not found in {target}"
            elif op == "assert_exists":
                await _find(app, pilot, target)
            elif op == "assert_not_exists":
                try:
                    app.screen.query_one(target)
                except NoMatches:
                    pass
                else:
                    raise AssertionError(f"{target} unexpectedly exists")
            else:
                raise ValueError(f"Unknown op: {op}")

            await pilot.pause()


def main() -> None:
    p = argparse.ArgumentParser(description="Flexible Textual pilot harness for hf-tui")
    p.add_argument("--config", default=".hf-tui/harness-config.json")
    p.add_argument("--actions", required=True, help="Path to JSON action list")
    args = p.parse_args()

    cfg = Path(args.config).resolve()
    _write_default_config(cfg)
    actions = json.loads(Path(args.actions).read_text())
    asyncio.run(run_actions(cfg, actions))
    print(f"Harness run completed: {args.actions}")


if __name__ == "__main__":
    main()
