import gradio as gr
import threading
from persistence import load_ollama_url, save_ollama_url
from ollama import get_models
from prompts import PROMPTS
from patch_mode import create_jobs, run_jobs_background
from rendering import wrap_iframe
from utils import extract_html_from_fences
from evaluation import save_evaluation
from evaluation_scales import (
    COLOR_TYPOGRAPHY_SCALE,
    LAYOUT_SCALE,
    CORRECTNESS_SCALE,
    FUNCTIONALITY_SCALE,
)

# ---------------- In-memory job list ----------------
JOB_LIST = []

with gr.Blocks(title="Patch Mode HTML Generator") as app:
    gr.Markdown("## 🦙 Patch Mode HTML Generator – Multi-job Execution")

    last_job_id = gr.State()
    jobs_state = gr.State([])  # trigger UI refresh

    # ---------------- Top row: Ollama URL, models, prompts ----------------
    with gr.Row():
        ollama_url = gr.Textbox(label="Ollama Base URL", value=load_ollama_url())
        discover_btn = gr.Button("Discover Models")
        model_selector = gr.Dropdown(label="Select Models", multiselect=True, choices=[])
        prompt_selector = gr.Dropdown(label="Select Prompts", multiselect=True, choices=list(PROMPTS))
        generate_btn = gr.Button("Generate Jobs")

    # Persist Ollama URL
    ollama_url.change(save_ollama_url, ollama_url, ollama_url)
    discover_btn.click(get_models, ollama_url, model_selector)

    # ---------------- Job List ----------------
    jobs_display = gr.DataFrame(
        headers=["Job ID", "Model", "Prompt", "Status"],
        interactive=True
    )

    # ---------------- Tabs: HTML / Preview / Evaluation ----------------
    with gr.Tabs():
        with gr.Tab("HTML Source"):
            html_code = gr.Code(language="html", lines=25)

        with gr.Tab("Rendered Preview"):
            preview_link = gr.Markdown()
            preview_iframe = gr.HTML()

        with gr.Tab("Human Evaluation"):
            with gr.Row():
                with gr.Column():
                    color_typography = gr.Radio(
                        choices=COLOR_TYPOGRAPHY_SCALE,
                        label="Color & Typography",
                        type="value"
                    )
                with gr.Column():
                    layout = gr.Radio(
                        choices=LAYOUT_SCALE,
                        label="Layout & Structure",
                        type="value"
                    )
                with gr.Column():
                    correctness = gr.Radio(
                        choices=CORRECTNESS_SCALE,
                        label="Correctness",
                        type="value"
                    )
                with gr.Column():
                    functionality = gr.Radio(
                        choices=FUNCTIONALITY_SCALE,
                        label="Functionality",
                        type="value"
                    )
            comments = gr.Textbox(
                label="Free-form evaluation comments",
                lines=5,
                placeholder="Notes, issues, strengths, edge cases, suggestions…"
            )
            save_eval_btn = gr.Button("Save Evaluation")
            eval_status = gr.Textbox(interactive=False)

    # ---------------- Callbacks ----------------
    def on_generate(models, prompts, ollama_url_val):
        """Create jobs and run them sequentially in background."""
        global JOB_LIST
        prompt_texts = [PROMPTS[p] for p in prompts]
        JOB_LIST = create_jobs(models, prompts, prompt_texts)

        # Start background thread (sequential execution)
        thread = threading.Thread(
            target=run_jobs_background,
            args=(JOB_LIST, ollama_url_val, None),  # no callback
            daemon=True
        )
        thread.start()
        return JOB_LIST

    generate_btn.click(
        fn=on_generate,
        inputs=[model_selector, prompt_selector, ollama_url],
        outputs=[jobs_state]
    )

    # ---------------- Timer to refresh DataFrame ----------------
    refresh_timer = gr.Timer(value=0.5)
    refresh_timer.tick(
        fn=lambda: [[j["id"][:8], j["model"], j["prompt_name"], j["status"]] for j in JOB_LIST],
        inputs=[],
        outputs=[jobs_display]
    )

    # ---------------- Select job to view HTML / Preview / Evaluation ----------------
    def on_select_job(job_row, evt: gr.SelectData):
        
        selected_job = JOB_LIST[evt.index[0]]
        if not selected_job:
            return "", ""

        last_job_id.value = selected_job["id"]

        # get HTML and generate iframe
        html_out = selected_job.get("html_output")
        if not html_out:
            return "Generating…", ""

        # generate iframe
        iframe_out = wrap_iframe(html_out)
        selected_job["iframe"] = iframe_out
        preview_link_str = f"🔗 **[Open preview in new tab]({selected_job["preview_url"]})**"

        return html_out, iframe_out, preview_link_str



    jobs_display.select(
        fn=on_select_job,
        inputs=[jobs_display],
        outputs=[html_code, preview_iframe, preview_link]
    )

    # ---------------- Save human evaluation ----------------
    save_eval_btn.click(
        save_evaluation,
        inputs=[last_job_id, color_typography, layout, correctness, functionality, comments],
        outputs=eval_status
    )

if __name__ == "__main__":
    app.launch(allowed_paths=["previews"])
