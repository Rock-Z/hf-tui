from __future__ import annotations

from pathlib import Path

from hf_tui.backend import generate, load_engine
from hf_tui.config import load_config, normalize_model_input, save_config


class Core:
    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self.cfg = load_config(self.config_path)
        self.cache_dir = Path(self.cfg["cache_dir"])
        self.engine = load_engine(self.cfg.get("active_model", "mock"), self.cache_dir)
        self.transcript: list[str] = []

    def _save(self) -> None:
        save_config(self.config_path, self.cfg)

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

    def load_model(self, raw: str) -> str:
        model = normalize_model_input(raw)
        self.engine = load_engine(model, self.cache_dir)
        self.cfg["active_model"] = model
        if model != "mock":
            self.add_checkpoint(model)
        self._save()
        return f"Loaded {model} ({self.engine['kind']})"

    def send(self, prompt: str, *, temperature: float, max_new_tokens: int, thinking: bool):
        self.cfg["temperature"] = temperature
        self.cfg["max_new_tokens"] = max_new_tokens
        self.cfg["thinking"] = thinking
        self._save()
        self.transcript.append(f"You: {prompt}")
        ans = generate(
            self.engine,
            prompt,
            thinking=thinking,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
        )
        self.transcript.append(f"Assistant: {ans}")
        yield self.transcript
