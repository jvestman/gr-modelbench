import gradio as gr
import requests
import yaml
import html
import re
import uuid
import time
import csv
from pathlib import Path

LOG_FILE = Path("log.csv")
OLLAMA_URL_FILE = Path("ollama_url.txt")

SYSTEM_PROMPT = (
    "You're a helpful coding assistant. "
    "Return only the requested code and nothing else."
)

# ---------- Ollama URL persistence ----------

def load_ollama_url(default="http://localhost:11434"):
    if OLLAMA_URL_FILE.exists():
        return OLLAMA_URL_FILE.read_text(encoding="utf-8").strip()
    return default

def save_ollama_url(url: str):
    OLLAMA_URL_FILE.write_text(url.strip(), encoding="utf-8")
    return url

# ---------- Prompt loading ----------

def load_prompts(path="prompt.yml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {item["name"]: item["prompt"] for item in data}

PROMPTS = load_prompts()

# ---------- Ollama helpers ----------

def get_models(ollama_url):
    try:
        url = ollama_url.rstrip("/") + "/api/tags"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return gr.Dropdown(choices=models, value=models[0] if models else None)
    except Exception:
        return gr.Dropdown(choices=[], value=None)

# ---------- Prompt handling ----------

def build_full_prompt(prompt_name):
    if not prompt_name:
        return ""
    user_prompt = PROMPTS.get(prompt_name, "")
    return f"{SYSTEM_PROMPT}\n\n{user_prompt}".strip()

# ---------- HTML extraction + rendering ----------

def extract_html_from_fences(text: str) -> str:
    pattern = re.compile(
        r"```html\s*(.*?)\s*```",
        re.IGNORECASE | re.DOTALL
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()

def wrap_iframe(html_content: str) -> str:
    escaped = html.escape(html_content)
    return f"""
    <iframe
        sandbox="allow-scripts allow-same-origin"
        style="width:100%; height:600px; border:none;"
        srcdoc="{escaped}"
    ></iframe>
    """

# ---------- Logging ----------

def log_generation_eav(entity_id: str, data: dict):
    file_exists = LOG_FILE.exists()

    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["entity", "attribute", "value"])

        for key, value in data.items():
            writer.writerow([entity_id, key, value])

# ---------- Generation ----------

def generate_html(ollama_url, model, full_prompt):
    start_time = time.time()
    run_id = str(uuid.uuid4())

    url = ollama_url.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False
    }

    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    resp = r.json()

    raw_output = resp.get("response", "")
    html_output = extract_html_from_fences(raw_output)

    duration_s = time.time() - start_time

    eval_count = resp.get("eval_count", 0)
    prompt_count = resp.get("prompt_eval_count", 0)
    eval_duration_ns = resp.get("eval_duration", 0)

    tokens_per_sec = (
        eval_count / (eval_duration_ns / 1e9)
        if eval_duration_ns > 0 else None
    )

    log_generation_eav(run_id, {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ollama_url": ollama_url,
        "model": model,
        "prompt_length_chars": len(full_prompt),
        "response_length_chars": len(raw_output),
        "generation_time_sec": round(duration_s, 3),
        "eval_count": eval_count,
        "prompt_count": prompt_count,
        "tokens_per_sec": round(tokens_per_sec, 2) if tokens_per_sec else None
    })

    return html_output, wrap_iframe(html_output)

# ---------- UI ----------

with gr.Blocks(title="Remote Ollama HTML Generator") as app:
    gr.Markdown("## 🦙 Remote Ollama HTML Generator")

    with gr.Row():
        ollama_url = gr.Textbox(
            label="Ollama Base URL",
            value=load_ollama_url()
        )
        discover_btn = gr.Button("Discover Models")

    # Persist URL whenever user edits it
    ollama_url.change(
        fn=save_ollama_url,
        inputs=ollama_url,
        outputs=ollama_url
    )

    model_dropdown = gr.Dropdown(label="Available Models")

    discover_btn.click(
        fn=get_models,
        inputs=ollama_url,
        outputs=model_dropdown
    )

    prompt_selector = gr.Dropdown(
        label="Prompt Template",
        choices=list(PROMPTS.keys())
    )

    full_prompt_box = gr.Textbox(
        label="Full Prompt (Editable)",
        lines=10
    )

    prompt_selector.change(
        fn=build_full_prompt,
        inputs=prompt_selector,
        outputs=full_prompt_box
    )

    generate_btn = gr.Button("Generate HTML")

    with gr.Tabs():
        with gr.Tab("HTML Source"):
            html_code = gr.Code(
                label="Generated HTML",
                language="html",
                lines=25
            )

        with gr.Tab("Rendered Preview"):
            html_iframe = gr.HTML()

    generate_btn.click(
        fn=generate_html,
        inputs=[ollama_url, model_dropdown, full_prompt_box],
        outputs=[html_code, html_iframe]
    )

if __name__ == "__main__":
    app.launch()
