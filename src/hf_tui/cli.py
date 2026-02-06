from __future__ import annotations

import argparse
import os
from pathlib import Path

from hf_tui.app import HfTuiApp
from hf_tui.config import load_config, resolve_cache_dir


def main() -> None:
    p = argparse.ArgumentParser(description="Minimal HF TUI")
    p.add_argument("--config", default=".hf-tui/config.json", help="Single persistent config file")
    args = p.parse_args()

    cfg_path = Path(args.config).resolve()
    cfg = load_config(cfg_path)
    cache_dir = resolve_cache_dir(cfg, cfg_path)
    os.environ["HF_HOME"] = str(cache_dir)
    os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    HfTuiApp(config_path=cfg_path).run()


if __name__ == "__main__":
    main()
