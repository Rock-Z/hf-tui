from __future__ import annotations

from pathlib import Path

from textual.app import App

from hf_tui.core import Core
from hf_tui.ui import ChatScreen


class HfTuiApp(App[None]):
    CSS = "#chat {height: 1fr;} #temp,#tokens {width: 10;} #models {height: 8;}"

    def __init__(self, config_path: str | Path) -> None:
        super().__init__()
        self.core = Core(config_path)

    def on_mount(self) -> None:
        self.push_screen(ChatScreen(self.core))
