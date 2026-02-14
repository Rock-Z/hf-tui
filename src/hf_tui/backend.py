from __future__ import annotations

from pathlib import Path


def load_engine(model_id: str, cache_dir: str | Path):
    if model_id == "mock":
        return {"kind": "mock", "model_id": "mock"}

    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(model_id, cache_dir=str(cache))
    model = AutoModelForCausalLM.from_pretrained(model_id, cache_dir=str(cache))
    pipe = pipeline("text-generation", model=model, tokenizer=tok)
    return {"kind": "hf", "model_id": model_id, "tokenizer": tok, "pipe": pipe}


def generate(engine: dict, prompt: str, *, thinking: bool, temperature: float, max_new_tokens: int) -> str:
    if engine["kind"] == "mock":
        return f"{'[thinking] ' if thinking else ''}Echo: {prompt}"

    sys = "Think step by step internally; return only final concise answer." if thinking else ""
    msgs = [{"role": "user", "content": prompt}] if not sys else [
        {"role": "system", "content": sys},
        {"role": "user", "content": prompt},
    ]
    tok = engine["tokenizer"]
    pipe = engine["pipe"]

    if getattr(tok, "chat_template", None):
        out = pipe(msgs, max_new_tokens=max_new_tokens, do_sample=temperature > 0, temperature=temperature)
        result = out[0]["generated_text"]
        if isinstance(result, list):
            return str(result[-1].get("content", ""))
        return str(result)

    out = pipe(prompt, max_new_tokens=max_new_tokens, do_sample=temperature > 0, temperature=temperature)
    text = str(out[0]["generated_text"])
    return text[len(prompt) :] if text.startswith(prompt) else text
