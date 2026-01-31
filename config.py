from pathlib import Path

LOG_FILE = Path("log.csv")
OLLAMA_URL_FILE = Path("ollama_url.txt")
PREVIEW_DIR = Path("previews")
PREVIEW_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "You're a helpful coding assistant. "
    "Return only the requested code and nothing else."
)
