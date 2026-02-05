from __future__ import annotations

import json
from pathlib import Path


def load_config(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        data = {
            "cache_dir": ".hf-tui-cache",
            "active_model": "mock",
            "temperature": 0.7,
            "max_new_tokens": 128,
            "thinking": False,
            "checkpoints": [],
        }
        save_config(p, data)
        return data
    return json.loads(p.read_text())


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
