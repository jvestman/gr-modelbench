import yaml
from config import SYSTEM_PROMPT

def load_prompts(path="prompt.yml"):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {item["name"]: item["prompt"] for item in data}

PROMPTS = load_prompts()

def build_full_prompt(prompt_name: str) -> str:
    if not prompt_name:
        return ""
    return f"{SYSTEM_PROMPT}\n\n{PROMPTS[prompt_name]}".strip()
