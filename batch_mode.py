# batch_mode.py
import threading
import time
import uuid
from generation import generate_html
from rendering import wrap_iframe 
from utils import extract_html_from_fences
#from log_util import log_generation_eav  # optional helper for logging

def create_jobs(models, prompt_names, prompt_texts):
    """
    Create a list of jobs with unique IDs, models, prompts.
    """
    jobs = []
    for model in models:
        for pname, ptext in zip(prompt_names, prompt_texts):
            jobs.append({
                "id": str(uuid.uuid4()),
                "model": model,
                "prompt_name": pname,
                "prompt_text": ptext,
                "status": "pending",
                "stats": "",
                "html_output": None,
                "iframe": None,
                "evaluation": None,
                "raw_output": None
            })
    return jobs


def run_jobs_background(jobs_list, ollama_url, update_callback=None):
    """
    Sequentially execute pending jobs in background.
    Calls update_callback(jobs_list) after each job update.
    """
    for job in jobs_list:
        if job["status"] == "pending":
            job["status"] = "running"
            if update_callback:
                update_callback(jobs_list)

            try:
                raw_output, _preview_url, _run_id, eval_tokens, eval_duration, tokens_per_sec = generate_html(
                    job["id"],
                    ollama_url,
                    job["model"],
                    job["prompt_text"],
                    job["prompt_name"]
                )
                html_output = extract_html_from_fences(raw_output)
                iframe = wrap_iframe(html_output)

                job.update({
                    "status": "done",
                    "stats": f"{eval_tokens} tokens; {eval_duration}s; {tokens_per_sec} tokens/s",
                    "raw_output": raw_output,
                    "html_output": html_output,
                    "iframe": iframe,
                    "preview_url": _preview_url
                })

            except Exception as e:
                job["status"] = "error"
                job["raw_output"] = str(e)

            if update_callback:
                update_callback(jobs_list)
            time.sleep(0.1)  # allow UI to refresh
