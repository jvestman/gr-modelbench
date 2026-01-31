import gradio as gr
from persistence import load_ollama_url, save_ollama_url
from ollama import get_models
from prompts import PROMPTS, build_full_prompt
from generation import generate_html
from rendering import render_preview
from evaluation import save_evaluation

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
            from evaluation_scales import (
            COLOR_TYPOGRAPHY_SCALE,
            LAYOUT_SCALE,
            CORRECTNESS_SCALE,
            FUNCTIONALITY_SCALE,
        )


            with gr.Tab("Human Evaluation"):
                gr.Markdown("### Human Evaluation – score each criterion")

                with gr.Row():
                    # Color & Typography
                    with gr.Column():
                        color_typography = gr.Radio(
                            choices=COLOR_TYPOGRAPHY_SCALE,
                            label="Color & Typography",
                            type="value"
                        )

                    # Layout & Structure
                    with gr.Column():
                        layout = gr.Radio(
                            choices=LAYOUT_SCALE,
                            label="Layout & Structure",
                            type="value"
                        )

                    # Correctness
                    with gr.Column():
                        correctness = gr.Radio(
                            choices=CORRECTNESS_SCALE,
                            label="Correctness",
                            type="value"
                        )

                    # Functionality
                    with gr.Column():
                        functionality = gr.Radio(
                            choices=FUNCTIONALITY_SCALE,
                            label="Functionality",
                            type="value"
                        )

                # Free-form comments below
                comments = gr.Textbox(
                    label="Free-form evaluation comments",
                    lines=5,
                    placeholder="Notes, issues, strengths, edge cases, suggestions…"
                )

                save_eval_btn = gr.Button("Save Evaluation")
                eval_status = gr.Textbox(interactive=False)




    def _generate(ollama_url, model, prompt, template):
        html_out, preview_url, run_id = generate_html(
            ollama_url, model, prompt, template
        )
        link, iframe = render_preview(html_out, preview_url)
        return html_out, iframe, link, run_id

    generate_btn.click(
        _generate,
        inputs=[ollama_url, model_dropdown, full_prompt_box, prompt_selector],
        outputs=[html_code, html_iframe, preview_link, last_run_id]
    )

    save_eval_btn.click(
        save_evaluation,
        inputs=[last_run_id, color_typography, layout, correctness, functionality, comments],
        outputs=eval_status
    )

if __name__ == "__main__":
    app.launch(allowed_paths=["previews"])
