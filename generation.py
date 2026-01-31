import time
import uuid
from config import PREVIEW_DIR
from ollama import generate as ollama_generate
from utils import extract_html_from_fences, sha256_text
from logging_eav import log_generation_eav

def generate_html(run_id, ollama_url, model, full_prompt, prompt_template_name):
    start = time.time()

    resp = ollama_generate(ollama_url, model, full_prompt)

    raw = resp.get("response", "")
    html_out = extract_html_from_fences(raw)

    preview_path = PREVIEW_DIR / f"{run_id}.html"
    preview_path.write_text(html_out, encoding="utf-8")

    preview_url = f"gradio_api/file=previews/{run_id}.html"

    duration = time.time() - start
    eval_count = resp.get("eval_count", 0)
    prompt_count = resp.get("prompt_eval_count", 0)
    eval_dur_ns = resp.get("eval_duration", 0)

    tps = eval_count / (eval_dur_ns / 1e9) if eval_dur_ns else None

    log_generation_eav(run_id, {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ollama_url": ollama_url,
        "model": model,
        "prompt_template_name": prompt_template_name,
        "prompt_sha256": sha256_text(full_prompt),
        "prompt_length_chars": len(full_prompt),
        "response_length_chars": len(raw),
        "generation_time_sec": round(duration, 3),
        "eval_count": eval_count,
        "eval_duration": round(eval_dur_ns / 1e9, 2), 
        "prompt_count": prompt_count,
        "tokens_per_sec": round(tps, 2) if tps else None,
        "preview_url": preview_url
    })

    return html_out, preview_url, run_id
