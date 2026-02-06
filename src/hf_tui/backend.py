from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Iterable

_HF_RUNTIME_LOCK = threading.Lock()
_HF_RUNTIME_CONFIGURED = False


def _configure_hf_runtime() -> None:
    """Avoid tqdm multiprocessing locks in threaded UI contexts."""
    global _HF_RUNTIME_CONFIGURED
    if _HF_RUNTIME_CONFIGURED:
        return
    with _HF_RUNTIME_LOCK:
        if _HF_RUNTIME_CONFIGURED:
            return
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        try:
            from tqdm.std import TqdmDefaultWriteLock

            # Some TTY/test contexts raise ValueError here (not OSError),
            # which tqdm doesn't catch; fallback to thread lock only.
            def _safe_create_mp_lock(cls):
                if hasattr(cls, "mp_lock"):
                    return
                try:
                    from multiprocessing import RLock

                    cls.mp_lock = RLock()
                except Exception:
                    cls.mp_lock = None

            TqdmDefaultWriteLock.create_mp_lock = classmethod(_safe_create_mp_lock)
        except Exception:
            pass
        try:
            from huggingface_hub.utils import disable_progress_bars

            disable_progress_bars()
        except Exception:
            # Best-effort only; env vars above still apply.
            pass
        _HF_RUNTIME_CONFIGURED = True


def load_engine(
    model_id: str,
    cache_dir: str | Path,
    *,
    trust_remote_code: bool = False,
):
    if model_id == "mock":
        return {"kind": "mock", "model_id": "mock"}

    _configure_hf_runtime()
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(
        model_id,
        cache_dir=str(cache),
        trust_remote_code=trust_remote_code,
    )
    if tok.pad_token is None and tok.eos_token is not None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=str(cache),
        trust_remote_code=trust_remote_code,
    )
    pipe = pipeline("text-generation", model=model, tokenizer=tok)
    return {"kind": "hf", "model_id": model_id, "tokenizer": tok, "pipe": pipe}


def _build_plain_prompt(history: Iterable[dict[str, str]], prompt: str, thinking: bool) -> str:
    parts: list[str] = []
    if thinking:
        parts.append("System: Think step by step internally; return only final concise answer.")
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
        elif role == "system":
            parts.append(f"System: {content}")
    parts.append(f"User: {prompt}")
    parts.append("Assistant:")
    return "\n".join(parts)


def _build_messages(history: Iterable[dict[str, str]], prompt: str, thinking: bool) -> list[dict[str, str]]:
    msgs = list(history)
    if thinking:
        msgs = [
            {"role": "system", "content": "Think step by step internally; return only final concise answer."},
            *msgs,
        ]
    msgs.append({"role": "user", "content": prompt})
    return msgs


def generate(
    engine: dict,
    prompt: str,
    *,
    history: Iterable[dict[str, str]] | None = None,
    thinking: bool,
    temperature: float,
    max_new_tokens: int,
) -> str:
    if engine["kind"] == "mock":
        return f"{'[thinking] ' if thinking else ''}Echo: {prompt}"

    tok = engine["tokenizer"]
    pipe = engine["pipe"]
    history = history or []
    max_new_tokens = max(int(max_new_tokens), 1)
    do_sample = temperature > 0
    gen_kwargs = {"max_new_tokens": max_new_tokens, "do_sample": do_sample}
    if do_sample:
        gen_kwargs["temperature"] = temperature

    if getattr(tok, "chat_template", None):
        messages = _build_messages(history, prompt, thinking)
        try:
            prompt_text = tok.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            prompt_text = _build_plain_prompt(history, prompt, thinking)
    else:
        prompt_text = _build_plain_prompt(history, prompt, thinking)

    try:
        out = pipe(prompt_text, return_full_text=False, **gen_kwargs)
        return str(out[0]["generated_text"]).strip()
    except TypeError:
        out = pipe(prompt_text, **gen_kwargs)
        text = str(out[0]["generated_text"])
        if text.startswith(prompt_text):
            text = text[len(prompt_text) :]
        return text.strip()
