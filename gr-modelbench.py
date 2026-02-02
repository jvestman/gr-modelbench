import gradio as gr
from persistence import load_ollama_url, save_ollama_url
from ollama import get_models
from ui_components import create_ui
from callbacks import on_generate, display_jobs, on_select_job, save_evaluation_cb

with gr.Blocks(title="gr-modelbench") as app:
    ui = create_ui()

    # Ollama URL
    ui["ollama_url"].value = load_ollama_url()
    ui["ollama_url"].change(save_ollama_url, ui["ollama_url"], ui["ollama_url"])
    ui["discover_btn"].click(get_models, ui["ollama_url"], ui["model_selector"])

    # Generate jobs
    ui["generate_btn"].click(
        fn=on_generate,
        inputs=[ui["model_selector"], ui["prompt_selector"], ui["manual_prompt"], ui["ollama_url"]],
        outputs=[ui["jobs_state"]]
    )

    # Refresh DataFrame every 0.5s
    refresh_timer = gr.Timer(value=0.5)
    refresh_timer.tick(
        fn=display_jobs,
        inputs=[ui["jobs_state"]],
        outputs=[ui["jobs_display"]]
    )

    # Job selection
    ui["jobs_display"].select(
        fn=on_select_job,
        inputs=[ui["jobs_display"],ui["last_job_id"]],
        outputs=[ui["html_code"], ui["preview_iframe"], ui["preview_link"], ui["last_job_id"]]
    )

    # Save human evaluation
    ui["save_eval_btn"].click(
        save_evaluation_cb,
        inputs=[
            ui["last_job_id"],
            ui["color_typography"],
            ui["layout"],
            ui["correctness"],
            ui["functionality"],
            ui["comments"]
        ],
        outputs=[ui["eval_status"]]
    )

if __name__ == "__main__":
    app.launch(allowed_paths=["previews"])
