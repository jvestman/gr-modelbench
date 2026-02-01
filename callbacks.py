import gradio as gr
import threading
from patch_mode import create_jobs, run_jobs_background
from rendering import wrap_iframe
from evaluation import save_evaluation
from prompts import build_full_prompt

# In-memory job list
JOB_LIST = []

def on_generate(models, prompts, manual_prompt, ollama_url_val):
    """Create jobs and run sequentially in background."""
    global JOB_LIST 

    prompt_texts = [build_full_prompt(p) for p in prompts]  # PROMPTS can be used in main.py if needed

    if manual_prompt and manual_prompt.strip():
        prompts.append("manual")
        prompt_texts.append(manual_prompt)

    JOB_LIST = create_jobs(models, prompts, prompt_texts)

    thread = threading.Thread(
        target=run_jobs_background,
        args=(JOB_LIST, ollama_url_val, None),
        daemon=True
    )
    thread.start()
    return JOB_LIST

def display_jobs(_):
    return [[j["id"][:8], j["model"], j["prompt_name"], j["status"], j["stats"]] for j in JOB_LIST]

def on_select_job(job_row, last_job_id, evt: gr.SelectData):
    selected_job = JOB_LIST[evt.index[0]]

    if not last_job_id:
        last_job_id = gr.State()
    last_job_id.value = selected_job.get("id")

    if not selected_job:
        return "", "", "", last_job_id

    # get HTML and generate iframe
    html_out = selected_job.get("html_output")
    if not html_out:
        return "Generating…", "", "", last_job_id

    # generate iframe
    iframe_out = wrap_iframe(html_out)
    selected_job["iframe"] = iframe_out
    preview_link_str = f"🔗 **[Open preview in new tab]({selected_job['preview_url']})**"

    return html_out, iframe_out, preview_link_str, last_job_id


def save_evaluation_cb(last_job_id, color_typography, layout, correctness, functionality, comments):
    return save_evaluation(last_job_id.value, color_typography, layout, correctness, functionality, comments)
