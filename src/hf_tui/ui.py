from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Checkbox, Footer, Header, Input, Label, ListItem, ListView, TextArea

from hf_tui.core import Core


class ModelManagerModal(ModalScreen[None]):
    CSS = "#manager {width: 90%; height: 80%; border: round $accent; background: $surface;}"

    def __init__(self, core: Core) -> None:
        super().__init__()
        self.core = core

    def compose(self) -> ComposeResult:
        with Vertical(id="manager"):
            yield Label("Model Manager", id="manager_title")
            yield ListView(id="models")
            with Horizontal():
                yield Input(placeholder="model id or HF URL", id="manage_input")
                yield Button("Add", id="add")
                yield Button("Delete Selected", id="delete")
                yield Button("Refresh", id="refresh")
                yield Button("Close", id="close")

    def on_mount(self) -> None:
        self._refresh_models()

    def _refresh_models(self) -> None:
        lst = self.query_one("#models", ListView)
        lst.clear()
        for model, present in self.core.checkpoints():
            lst.append(ListItem(Label(f"{model} {'✅' if present else '⬜'}")))

    def _selected_model(self) -> str | None:
        item = self.query_one("#models", ListView).highlighted_child
        return None if not item else str(item.query_one(Label).renderable).split(" ", 1)[0]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            m = self.query_one("#manage_input", Input).value.strip()
            if m:
                self.core.add_checkpoint(m)
            self._refresh_models()
        elif event.button.id == "delete":
            m = self._selected_model()
            if m:
                self.core.delete_checkpoint(m)
            self._refresh_models()
        elif event.button.id == "refresh":
            self._refresh_models()
        elif event.button.id == "close":
            self.dismiss(None)


class ChatScreen(Screen[None]):
    BINDINGS = [("m", "manage_models", "Models")]

    def __init__(self, core: Core) -> None:
        super().__init__()
        self.core = core

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal():
                yield Input(placeholder="model id / HF URL / mock", id="model")
                yield Button("Load", id="load")
                yield Button("Models", id="open_models")
            yield Label("Ready", id="status")
            yield TextArea("", id="chat", read_only=True)
            with Horizontal():
                yield Input(placeholder="Prompt", id="prompt")
                yield Input(value=str(self.core.cfg.get("temperature", 0.7)), id="temp")
                yield Input(value=str(self.core.cfg.get("max_new_tokens", 128)), id="tokens")
                yield Checkbox("thinking", value=bool(self.core.cfg.get("thinking", False)), id="thinking")
                yield Button("Send", id="send")
        yield Footer()

    def action_manage_models(self) -> None:
        self.app.push_screen(ModelManagerModal(self.core))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        status = self.query_one("#status", Label)
        if event.button.id == "open_models":
            self.action_manage_models()
            return
        if event.button.id == "load":
            m = self.query_one("#model", Input).value or "mock"
            status.update(self.core.load_model(m))
            return
        if event.button.id != "send":
            return
        prompt = self.query_one("#prompt", Input).value
        t = float(self.query_one("#temp", Input).value or 0.7)
        n = int(self.query_one("#tokens", Input).value or 128)
        thinking = self.query_one("#thinking", Checkbox).value
        for tr in self.core.send(prompt, temperature=t, max_new_tokens=n, thinking=thinking):
            self.query_one("#chat", TextArea).text = "\n\n".join(tr)
