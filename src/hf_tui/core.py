from __future__ import annotations

from pathlib import Path

from hf_tui.backend import generate, load_engine
from hf_tui.config import load_config, normalize_model_input, resolve_cache_dir, save_config


class Core:
    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self.cfg = load_config(self.config_path)
        self.cache_dir = resolve_cache_dir(self.cfg, self.config_path)
        self.transcript: list[str] = []
        self.messages: list[dict[str, str]] = []
        self.last_error: str | None = None
        self.trust_remote_code = bool(self.cfg.get("trust_remote_code", False))
        raw_active = self.cfg.get("active_model", "mock")
        try:
            active_model = normalize_model_input(raw_active)
        except Exception as exc:
            active_model = "mock"
            self.last_error = self._fmt_error(exc)
        try:
            self.engine = load_engine(
                active_model,
                self.cache_dir,
                trust_remote_code=self.trust_remote_code,
            )
        except Exception as exc:  # pragma: no cover - depends on external models/files
            self.engine = load_engine(
                "mock",
                self.cache_dir,
                trust_remote_code=self.trust_remote_code,
            )
            self.last_error = self._fmt_error(exc)

    def _save(self) -> None:
        save_config(self.config_path, self.cfg)

    @staticmethod
    def _fmt_error(exc: Exception) -> str:
        message = str(exc).strip() or type(exc).__name__
        if "trust_remote_code=True" in message:
            return (
                "Model requires remote code (`trust_remote_code=True`), "
                "which is currently disabled."
            )
        return f"{type(exc).__name__}: {message}"

    def clear_chat(self) -> None:
        self.transcript = []
        self.messages = []

    def checkpoints(self) -> list[tuple[str, bool]]:
        out = []
        for model in sorted(set(self.cfg.get("checkpoints", []))):
            key = f"models--{model.replace('/', '--')}"
            exists = (self.cache_dir / key).exists() or (self.cache_dir / "hub" / key).exists()
            out.append((model, exists))
        return out

    def add_checkpoint(self, raw: str) -> None:
        model = normalize_model_input(raw)
        self.cfg["checkpoints"] = sorted(set([*self.cfg.get("checkpoints", []), model]))
        self._save()

    def delete_checkpoint(self, model: str) -> None:
        self.cfg["checkpoints"] = [m for m in self.cfg.get("checkpoints", []) if m != model]
        self._save()

    def load_model(self, raw: str, *, trust_remote_code: bool | None = None) -> str:
        try:
            model = normalize_model_input(raw)
        except Exception as exc:
            self.last_error = self._fmt_error(exc)
            return f"Error loading model: {self.last_error}"
        trust = self.trust_remote_code if trust_remote_code is None else bool(trust_remote_code)
        try:
            engine = load_engine(model, self.cache_dir, trust_remote_code=trust)
        except Exception as exc:
            self.last_error = self._fmt_error(exc)
            return f"Error loading {model}: {self.last_error}"
        self.engine = engine
        self.trust_remote_code = trust
        self.cfg["active_model"] = model
        self.cfg["trust_remote_code"] = trust
        if model != "mock":
            self.add_checkpoint(model)
        self._save()
        self.last_error = None
        self.clear_chat()
        return f"Loaded {model} ({self.engine['kind']})"

    def send(self, prompt: str, *, temperature: float, max_new_tokens: int, thinking: bool):
        self.cfg["temperature"] = temperature
        self.cfg["max_new_tokens"] = max_new_tokens
        self.cfg["thinking"] = thinking
        self._save()
        if not prompt.strip():
            self.last_error = "Prompt is empty."
            yield self.transcript
            return
        self.transcript.append(f"You: {prompt}")
        try:
            ans = generate(
                self.engine,
                prompt,
                history=self.messages,
                thinking=thinking,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
            )
        except Exception as exc:
            self.last_error = self._fmt_error(exc)
            self.transcript.append(f"Assistant: [error] {self.last_error}")
            yield self.transcript
            return
        self.messages.append({"role": "user", "content": prompt})
        self.messages.append({"role": "assistant", "content": ans})
        self.last_error = None
        self.transcript.append(f"Assistant: {ans}")
        yield self.transcript
