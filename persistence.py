from config import OLLAMA_URL_FILE

def load_ollama_url(default="http://localhost:11434"):
    if OLLAMA_URL_FILE.exists():
        return OLLAMA_URL_FILE.read_text(encoding="utf-8").strip()
    return default

def save_ollama_url(url: str):
    OLLAMA_URL_FILE.write_text(url.strip(), encoding="utf-8")
    return url
