import requests
import gradio as gr

def get_models(base_url, backend="ollama", api_key=None):
    try:
        base_url = base_url.rstrip("/")

        if backend == "ollama":
            r = requests.get(f"{base_url}/api/tags", timeout=5)
            r.raise_for_status()
            models = sorted([m["name"] for m in r.json().get("models", [])])

        elif backend == "openai":
            headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
            r = requests.get(f"{base_url}/v1/models", headers=headers, timeout=5)
            r.raise_for_status()
            models = sorted([m["id"] for m in r.json().get("data", [])])

        else:
            models = []

        return gr.Dropdown(choices=models, value=models[0] if models else None)

    except Exception:
        return gr.Dropdown(choices=[], value=None)


def generate(base_url, model, prompt, backend="ollama", api_key=None):
    base_url = base_url.rstrip("/")

    if backend == "ollama":
        r = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": 120000}
            },
            timeout=300
        )
        r.raise_for_status()
        return r.json()

    elif backend == "openai":
        headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        r = requests.post(
            f"{base_url}/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "prompt": prompt,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 64000,
                "temperature": 0.7
            },
            timeout=300
        )
        r.raise_for_status()
        return r.json()

    else:
        raise ValueError("Unsupported backend")