import requests
import gradio as gr

def get_models(ollama_url):
    try:
        r = requests.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return gr.Dropdown(choices=models, value=models[0] if models else None)
    except Exception:
        return gr.Dropdown(choices=[], value=None)

def generate(ollama_url, model, prompt):
    r = requests.post(
        f"{ollama_url.rstrip('/')}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=60
    )
    r.raise_for_status()
    return r.json()
