from __future__ import annotations

from pathlib import Path

from textual.app import App

from hf_tui.core import Core
from hf_tui.ui import ChatScreen


class HfTuiApp(App[None]):
    CSS = """
    #model_row Input { width: 1fr; }
    #model_row Button { width: 12; }
    #main_row { height: 1fr; }
    #chat { width: 1fr; }
    #download_sidebar { width: 40; border: round $panel; padding: 0 1; }
    #download_log { height: 1fr; }
    #loader { height: 3; }
    #chat_actions Input#prompt { width: 1fr; }
    #temp, #tokens { width: 10; }
    #chat_actions Button#send { width: 12; }
    #manager_actions Input { width: 1fr; }
    #manager_actions Button { width: 16; }
    #models { height: 1fr; }
    """

    def __init__(self, config_path: str | Path) -> None:
        super().__init__()
        self.core = Core(config_path)

    def on_mount(self) -> None:
        self.push_screen(ChatScreen(self.core))
