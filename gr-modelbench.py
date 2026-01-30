import gradio as gr
import requests

def get_models(ollama_url):
    try:
        url = ollama_url.rstrip("/") + "/api/tags"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        print(data)
        models = [m["name"] for m in data.get("models", [])]
        return gr.Dropdown(choices=models, value=models[0] if models else None)
    except Exception as e:
        return gr.Dropdown(choices=[], value=None)

def generate_text(ollama_url, model, prompt):
    if not ollama_url or not model or not prompt:
        return ""

    url = ollama_url.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        return f"Error: {e}"

with gr.Blocks(title="Remote Ollama Generator") as app:
    gr.Markdown("## 🦙 Remote Ollama Generator")

    ollama_url = gr.Textbox(
        label="Ollama Base URL",
        placeholder="http://localhost:11434"
    )

    discover_btn = gr.Button("Discover Models")

    model_dropdown = gr.Dropdown(
        label="Available Models",
        choices=[]
    )

    prompt_box = gr.Textbox(
        label="Prompt",
        lines=6,
        placeholder="Enter your prompt here..."
    )

    generate_btn = gr.Button("Generate")

    output_box = gr.Textbox(
        label="Output",
        lines=12
    )

    discover_btn.click(
        fn=get_models,
        inputs=ollama_url,
        outputs=model_dropdown
    )

    generate_btn.click(
        fn=generate_text,
        inputs=[ollama_url, model_dropdown, prompt_box],
        outputs=output_box
    )

if __name__ == "__main__":
    app.launch()

