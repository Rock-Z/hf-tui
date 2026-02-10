from pathlib import Path

from hf_tui.core import Core


def test_mock_model_chat(tmp_path: Path) -> None:
    core = Core(tmp_path / "config.json")
    assert "Loaded mock" in core.load_model("mock", trust_remote_code=True)
    assert core.cfg["trust_remote_code"] is True
    tr = list(core.send("hi", temperature=0.7, max_new_tokens=16, thinking=True))[-1]
    joined = "\n".join(tr)
    assert "You: hi" in joined
    assert "Echo: hi" in joined
