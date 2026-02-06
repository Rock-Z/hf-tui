from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    LoadingIndicator,
    TextArea,
)

from hf_tui.core import Core


class ModelManagerModal(ModalScreen[None]):
    BINDINGS = [("escape", "close", "Close"), ("q", "close", "Close")]
    CSS = "#manager {width: 90%; height: 80%; border: round $accent; background: $surface;}"

    def __init__(self, core: Core) -> None:
        super().__init__()
        self.core = core

    def compose(self) -> ComposeResult:
        with Vertical(id="manager"):
            yield Label("Model Manager", id="manager_title")
            yield Label("", id="manager_status")
            yield ListView(id="models")
            with Horizontal(id="manager_actions"):
                yield Input(placeholder="model id or HF URL", id="manage_input")
                yield Button("Add", id="add")
                yield Button("Delete Selected", id="delete")
                yield Button("Refresh", id="refresh")
                yield Button("Close", id="close")

    def action_close(self) -> None:
        self.dismiss(None)

    def on_mount(self) -> None:
        self._refresh_models()

    def _refresh_models(self) -> None:
        lst = self.query_one("#models", ListView)
        lst.clear()
        for model, present in self.core.checkpoints():
            lst.append(ListItem(Label(f"{model} {'✅' if present else '⬜'}")))

    def _set_status(self, message: str) -> None:
        self.query_one("#manager_status", Label).update(message)

    def _selected_model(self) -> str | None:
        item = self.query_one("#models", ListView).highlighted_child
        return None if not item else str(item.query_one(Label).renderable).split(" ", 1)[0]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add":
            m = self.query_one("#manage_input", Input).value.strip()
            if not m:
                self._set_status("Enter a model id or URL.")
                return
            try:
                self.core.add_checkpoint(m)
                self._set_status("Added checkpoint.")
            except Exception as exc:
                self._set_status(f"Error: {type(exc).__name__}: {exc}")
            self._refresh_models()
        elif event.button.id == "delete":
            m = self._selected_model()
            if m:
                self.core.delete_checkpoint(m)
                self._set_status("Deleted checkpoint.")
            else:
                self._set_status("Select a model to delete.")
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
        self._busy = False

    def _format_float(self, value: object, default: float) -> str:
        try:
            return str(float(value))
        except (TypeError, ValueError):
            return str(default)

    def _format_int(self, value: object, default: int) -> str:
        try:
            return str(int(value))
        except (TypeError, ValueError):
            return str(default)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal(id="model_row"):
                yield Input(placeholder="model id / HF URL / mock", id="model")
                yield Checkbox(
                    "remote code",
                    value=bool(self.core.cfg.get("trust_remote_code", False)),
                    id="trust_code",
                )
                yield Button("Load", id="load")
                yield Button("Models", id="open_models")
            yield Label("Ready", id="status")
            with Horizontal(id="main_row"):
                yield TextArea("", id="chat", read_only=True)
                with Vertical(id="download_sidebar"):
                    yield Label("Model Download / Load", id="dl_title")
                    yield LoadingIndicator(id="loader")
                    yield TextArea("", id="download_log", read_only=True)
            with Horizontal(id="chat_actions"):
                yield Input(placeholder="Prompt", id="prompt")
                yield Input(
                    value=self._format_float(self.core.cfg.get("temperature", 0.7), 0.7), id="temp"
                )
                yield Input(
                    value=self._format_int(self.core.cfg.get("max_new_tokens", 128), 128),
                    id="tokens",
                )
                yield Checkbox("thinking", value=bool(self.core.cfg.get("thinking", False)), id="thinking")
                yield Button("Send", id="send")
                yield Button("Clear", id="clear")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#loader", LoadingIndicator).display = False
        self.query_one("#prompt", Input).focus()
        if self.core.last_error:
            self._set_status(f"Warning: {self.core.last_error}")

    def action_manage_models(self) -> None:
        self.app.push_screen(ModelManagerModal(self.core))

    def action_clear_chat(self) -> None:
        self.core.clear_chat()
        self.query_one("#chat", TextArea).text = ""
        self._set_status("Chat cleared.")

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Label).update(message)

    def _append_download_log(self, line: str) -> None:
        box = self.query_one("#download_log", TextArea)
        box.text = (box.text + "\n" + line).strip()

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        self._busy = busy
        self.query_one("#loader", LoadingIndicator).display = busy
        for widget_id in (
            "load",
            "send",
            "open_models",
            "model",
            "trust_code",
            "prompt",
            "temp",
            "tokens",
            "thinking",
            "clear",
        ):
            self.query_one(f"#{widget_id}").disabled = busy
        if status:
            self._set_status(status)

    def _parse_temperature(self) -> float | None:
        raw = self.query_one("#temp", Input).value.strip()
        if not raw:
            try:
                return float(self.core.cfg.get("temperature", 0.7))
            except (TypeError, ValueError):
                return 0.7
        try:
            value = float(raw)
        except ValueError:
            self._set_status("Temperature must be a number.")
            return None
        self.query_one("#temp", Input).value = str(value)
        return value

    def _parse_tokens(self) -> int | None:
        raw = self.query_one("#tokens", Input).value.strip()
        if not raw:
            try:
                return int(self.core.cfg.get("max_new_tokens", 128))
            except (TypeError, ValueError):
                return 128
        try:
            value = int(raw)
        except ValueError:
            self._set_status("Max tokens must be an integer.")
            return None
        if value <= 0:
            self._set_status("Max tokens must be > 0.")
            return None
        self.query_one("#tokens", Input).value = str(value)
        return value

    async def _handle_load(self) -> None:
        if self._busy:
            return
        m = self.query_one("#model", Input).value.strip() or "mock"
        trust_remote_code = self.query_one("#trust_code", Checkbox).value
        self._append_download_log(f"Starting load: {m}")
        self._append_download_log(f"Remote code: {'enabled' if trust_remote_code else 'disabled'}")
        self._set_busy(True, f"Loading {m} ...")
        try:
            msg = await asyncio.to_thread(
                self.core.load_model,
                m,
                trust_remote_code=trust_remote_code,
            )
        finally:
            self._set_busy(False)
        self._set_status(msg)
        if self.core.last_error:
            self._append_download_log(f"Failed load: {m} ({self.core.last_error})")
        else:
            self._append_download_log(f"Completed load: {m}")
            self.query_one("#chat", TextArea).text = ""

    async def _handle_send(self) -> None:
        if self._busy:
            return
        prompt = self.query_one("#prompt", Input).value.strip()
        if not prompt:
            self._set_status("Enter a prompt first.")
            return
        t = self._parse_temperature()
        if t is None:
            return
        n = self._parse_tokens()
        if n is None:
            return
        thinking = self.query_one("#thinking", Checkbox).value
        self._set_busy(True, "Generating response ...")
        try:
            snapshot = await asyncio.to_thread(
                lambda: list(
                    self.core.send(prompt, temperature=t, max_new_tokens=n, thinking=thinking)
                )[-1]
            )
        finally:
            self._set_busy(False)
        self.query_one("#chat", TextArea).text = "\n\n".join(snapshot)
        self.query_one("#prompt", Input).value = ""
        if self.core.last_error:
            self._set_status(f"Error: {self.core.last_error}")
        else:
            self._set_status("Ready")

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "prompt":
            await self._handle_send()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "open_models":
            self.action_manage_models()
            return
        if event.button.id == "load":
            await self._handle_load()
            return
        if event.button.id == "send":
            await self._handle_send()
            return
        if event.button.id == "clear":
            self.action_clear_chat()
