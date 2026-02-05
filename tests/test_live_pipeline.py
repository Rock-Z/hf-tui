from pathlib import Path

from hf_tui.core import Core


def test_live_tiny_model_pipeline_and_cache_isolation(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    core = Core(cfg)
    core.cfg["cache_dir"] = str(tmp_path / "cache")
    core._save()
    core.cache_dir = Path(core.cfg["cache_dir"])

    msg = core.load_model("sshleifer/tiny-gpt2")
    assert "Loaded sshleifer/tiny-gpt2" in msg

    snapshots = list(core.send("Say hello", temperature=0.0, max_new_tokens=8, thinking=False))
    assert snapshots
    assert "Assistant:" in "\n".join(snapshots[-1])

    matches = [p for p in Path(core.cfg["cache_dir"]).rglob("*") if p.name.startswith("models--sshleifer--tiny-gpt2")]
    assert matches
