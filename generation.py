import time
import uuid
from config import PREVIEW_DIR
from ollama import generate as ollama_generate
from utils import extract_html_from_fences, sha256_text
from logging_eav import log_generation_eav


def extract_text_from_response(resp, backend):
    """Normalize text output across backends."""
    if backend == "ollama":
        return resp.get("response", "")

    elif backend == "openai":
        # समर्थन both completion + chat formats
        if "choices" in resp and resp["choices"]:
            choice = resp["choices"][0]

            if "text" in choice:  # /v1/completions
                return choice.get("text", "")

            if "message" in choice:  # /v1/chat/completions
                return choice["message"].get("content", "")

        return ""

    return ""


def extract_metrics(resp, backend):
    """Normalize metrics across backends."""
    if backend == "ollama":
        eval_count = resp.get("eval_count", 0)
        prompt_count = resp.get("prompt_eval_count", 0)
        eval_dur_ns = resp.get("eval_duration", 0)

    elif backend == "openai":
        usage = resp.get("usage", {})
        eval_count = usage.get("completion_tokens", 0)
        prompt_count = usage.get("prompt_tokens", 0)
        timings = resp.get("timings", {})
        eval_dur_ns = timings.get("predicted_ms", 0) * 1000 * 1000

    else:
        eval_count = prompt_count = eval_dur_ns = 0

    eval_duration = round(eval_dur_ns / 1e9, 2) if eval_dur_ns else None
    tps = eval_count / (eval_dur_ns / 1e9) if eval_dur_ns else None
    tokens_per_sec = round(tps, 2) if tps else None

    return eval_count, prompt_count, eval_duration, tokens_per_sec


def generate_html(run_id, ollama_url, model, full_prompt, prompt_template_name, backend="ollama"):
    start = time.time()

    resp = ollama_generate(ollama_url, model, full_prompt, backend)

    # ✅ unified text extraction
    raw = extract_text_from_response(resp, backend)
    html_out = extract_html_from_fences(raw)

    preview_path = PREVIEW_DIR / f"{run_id}.html"
    preview_path.write_text(html_out, encoding="utf-8")

    preview_url = f"gradio_api/file=previews/{run_id}.html"

    duration = time.time() - start

    # ✅ unified metrics
    eval_count, prompt_count, eval_duration, tokens_per_sec = extract_metrics(resp, backend)

    log_generation_eav(run_id, {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ollama_url": ollama_url,
        "model": model,
        "backend": backend,
        "prompt_template_name": prompt_template_name,
        "prompt_sha256": sha256_text(full_prompt),
        "prompt_length_chars": len(full_prompt),
        "response_length_chars": len(raw),
        "generation_time_sec": round(duration, 3),
        "eval_count": eval_count,
        "eval_duration": eval_duration,
        "prompt_count": prompt_count,
        "tokens_per_sec": tokens_per_sec,
        "preview_url": preview_url
    })

    return html_out, preview_url, run_id, eval_count, eval_duration, tokens_per_sec