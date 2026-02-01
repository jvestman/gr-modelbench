import gradio as gr
from prompts import PROMPTS
from evaluation_scales import (
    COLOR_TYPOGRAPHY_SCALE,
    LAYOUT_SCALE,
    CORRECTNESS_SCALE,
    FUNCTIONALITY_SCALE,
)

def create_ui():
    last_job_id = gr.State()
    jobs_state = gr.State([])

    # ---------------- Top row ----------------
    with gr.Row():
        ollama_url = gr.Textbox(label="Ollama Base URL")
        discover_btn = gr.Button("Discover Models")
        model_selector = gr.Dropdown(
            label="Select Models",
            multiselect=True,
            choices=[]
        )
        prompt_selector = gr.Dropdown(
            label="Select Prompt Templates",
            multiselect=True,
            choices=list(PROMPTS)
        )
        generate_btn = gr.Button("Generate Jobs")

    # ---------------- Manual prompt ----------------
    manual_prompt = gr.Textbox(
        label="Manual Prompt (overrides templates if provided)",
        lines=8,
        placeholder=(
            "Optional. If filled, this prompt will be used instead of "
            "selected prompt templates."
        )
    )

    # ---------------- Job List ----------------
    jobs_display = gr.DataFrame(
        headers=["Job ID", "Model", "Prompt", "Status"],
        interactive=True
    )

    # ---------------- Tabs ----------------
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

    return {
        # state
        "last_job_id": last_job_id,
        "jobs_state": jobs_state,

        # controls
        "ollama_url": ollama_url,
        "discover_btn": discover_btn,
        "model_selector": model_selector,
        "prompt_selector": prompt_selector,
        "manual_prompt": manual_prompt,
        "generate_btn": generate_btn,

        # outputs
        "jobs_display": jobs_display,
        "html_code": html_code,
        "preview_iframe": preview_iframe,
        "preview_link": preview_link,

        # evaluation
        "color_typography": color_typography,
        "layout": layout,
        "correctness": correctness,
        "functionality": functionality,
        "comments": comments,
        "save_eval_btn": save_eval_btn,
        "eval_status": eval_status,
    }
