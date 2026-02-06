from __future__ import annotations

import json
from pathlib import Path

DEFAULT_CONFIG = {
    "cache_dir": ".hf-tui-cache",
    "active_model": "mock",
    "temperature": 0.7,
    "max_new_tokens": 128,
    "thinking": False,
    "trust_remote_code": False,
    "checkpoints": [],
}


def resolve_cache_dir(cfg: dict, config_path: str | Path) -> Path:
    raw = cfg.get("cache_dir", ".hf-tui-cache")
    cache_path = Path(raw)
    if not cache_path.is_absolute():
        cache_path = Path(config_path).resolve().parent / cache_path
    return cache_path.resolve()


def load_config(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        data = dict(DEFAULT_CONFIG)
        save_config(p, data)
        return data
    data = json.loads(p.read_text())
    merged = {**DEFAULT_CONFIG, **data}
    if merged != data:
        save_config(p, merged)
    return merged


def save_config(path: str | Path, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True))


def normalize_model_input(raw: str) -> str:
    value = raw.strip()
    if value == "mock":
        return value
    if value.startswith("http://") or value.startswith("https://"):
        parts = [x for x in value.split("huggingface.co/")[-1].split("/") if x]
        if parts and parts[0] == "models":
            parts = parts[1:]
        if len(parts) < 2:
            raise ValueError(f"Invalid HF URL: {raw}")
        return f"{parts[0]}/{parts[1]}"
    return value
