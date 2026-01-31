import gradio as gr
import requests
import yaml
import html
import re
import uuid
import time
import csv
import hashlib
from pathlib import Path

# ---------- Files ----------

LOG_FILE = Path("log.csv")
OLLAMA_URL_FILE = Path("ollama_url.txt")
PREVIEW_DIR = Path("previews")
PREVIEW_DIR.mkdir(exist_ok=True)

# ---------- System Prompt ----------

SYSTEM_PROMPT = (
    "You're a helpful coding assistant. "
    "Return only the requested code and nothing else."
)

# ---------- Persistence ----------

def load_ollama_url(default="http://localhost:11434"):
    if OLLAMA_URL_FILE.exists():
        return OLLAMA_URL_FILE.read_text(encoding="utf-8").strip()
    return default

def save_ollama_url(url: str):
    OLLAMA_URL_FILE.write_text(url.strip(), encoding="utf-8")
    return url

# ---------- Prompt Loading ----------

def load_prompts(path="prompt.yml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {item["name"]: item["prompt"] for item in data}

PROMPTS = load_prompts()

# ---------- Utilities ----------

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_html_from_fences(text: str) -> str:
    pattern = re.compile(r"```html\s*(.*?)\s*```", re.I | re.S)
    match = pattern.search(text)
    return match.group(1).strip() if match else text.strip()

def wrap_iframe(html_content: str) -> str:
    escaped = html.escape(html_content)
    return f"""
    <iframe
        sandbox="allow-scripts allow-same-origin"
        style="width:100%; height:600px; border:none;"
        srcdoc="{escaped}"
    ></iframe>
    """

# ---------- Logging (EAV) ----------

def log_generation_eav(entity_id: str, data: dict):
    file_exists = LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["entity", "attribute", "value"])
        for k, v in data.items():
            writer.writerow([entity_id, k, v])

# ---------- Ollama ----------

def get_models(ollama_url):
    try:
        r = requests.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return gr.Dropdown(choices=models, value=models[0] if models else None)
    except Exception:
        return gr.Dropdown(choices=[], value=None)

# ---------- Prompt ----------

def build_full_prompt(prompt_name):
    if not prompt_name:
        return ""
    return f"{SYSTEM_PROMPT}\n\n{PROMPTS[prompt_name]}".strip()

# ---------- Generation ----------

def generate_html(ollama_url, model, full_prompt, prompt_template_name):
    run_id = str(uuid.uuid4())
    start = time.time()

    r = requests.post(
        f"{ollama_url.rstrip('/')}/api/generate",
        json={"model": model, "prompt": full_prompt, "stream": False},
        timeout=300
    )
    r.raise_for_status()
    resp = r.json()

    raw = resp.get("response", "")
    html_out = extract_html_from_fences(raw)

    # Save standalone preview file
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
        "prompt_count": prompt_count,
        "tokens_per_sec": round(tps, 2) if tps else None,
        "preview_url": preview_url
    })

    preview_link_md = f"🔗 **[Open preview in new tab]({preview_url})**"

    return html_out, wrap_iframe(html_out), preview_link_md, run_id

# ---------- Human Evaluation ----------

def save_evaluation(
    run_id,
    color_typography,
    layout,
    correctness,
    functionality,
    comments
):
    if not run_id:
        return "No generation to evaluate."

    log_generation_eav(run_id, {
        "eval_visual_color_typography": color_typography,
        "eval_layout_structure": layout,
        "eval_correctness": correctness,
        "eval_functionality": functionality,
        "eval_comments": comments.strip() if comments else ""
    })

    return "✅ Evaluation saved"

# ---------- UI ----------

with gr.Blocks(title="Remote Ollama HTML Generator") as app:
    gr.Markdown("## 🦙 Remote Ollama HTML Generator")

    last_run_id = gr.State()

    with gr.Row():
        ollama_url = gr.Textbox(label="Ollama Base URL", value=load_ollama_url())
        discover_btn = gr.Button("Discover Models")

    ollama_url.change(save_ollama_url, ollama_url, ollama_url)

    model_dropdown = gr.Dropdown(label="Model")
    discover_btn.click(get_models, ollama_url, model_dropdown)

    prompt_selector = gr.Dropdown(label="Prompt Template", choices=list(PROMPTS))
    full_prompt_box = gr.Textbox(label="Full Prompt (Editable)", lines=10)
    prompt_selector.change(build_full_prompt, prompt_selector, full_prompt_box)

    generate_btn = gr.Button("Generate HTML")

    with gr.Tabs():
        with gr.Tab("HTML Source"):
            html_code = gr.Code(language="html", lines=25)

        with gr.Tab("Rendered Preview"):
            preview_link = gr.Markdown()
            html_iframe = gr.HTML()

        with gr.Tab("Human Evaluation"):
            gr.Markdown("### Human Evaluation")

            color_typography = gr.Radio([1, 2, 3, 4, 5],
                label="Visual appearance – color & typography")

            layout = gr.Radio([1, 2, 3, 4, 5],
                label="Layout & structure")

            correctness = gr.Radio([1, 2, 3, 4, 5],
                label="Correctness (prompt adherence)")

            functionality = gr.Radio([1, 2, 3, 4, 5],
                label="Functionality")

            comments = gr.Textbox(
                label="Free-form comments",
                lines=5
            )

            save_eval_btn = gr.Button("Save Evaluation")
            eval_status = gr.Textbox(interactive=False)

    generate_btn.click(
        generate_html,
        inputs=[ollama_url, model_dropdown, full_prompt_box, prompt_selector],
        outputs=[html_code, html_iframe, preview_link, last_run_id]
    )

    save_eval_btn.click(
        save_evaluation,
        inputs=[
            last_run_id,
            color_typography,
            layout,
            correctness,
            functionality,
            comments
        ],
        outputs=eval_status
    )

if __name__ == "__main__":
    app.launch(allowed_paths=["previews"])
