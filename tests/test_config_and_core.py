from pathlib import Path

from hf_tui.config import load_config, normalize_model_input
from hf_tui.core import Core


def test_config_single_file_and_checkpoint_ops(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    data = load_config(cfg)
    assert cfg.exists()
    assert "checkpoints" in data

    core = Core(cfg)
    core.add_checkpoint("https://huggingface.co/org/model")
    assert core.checkpoints() == [("org/model", False)]
    core.delete_checkpoint("org/model")
    assert core.checkpoints() == []


def test_model_normalization() -> None:
    assert normalize_model_input("https://huggingface.co/org/model") == "org/model"
    assert normalize_model_input("mock") == "mock"
