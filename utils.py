import hashlib
import html
import re

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_html_from_fences(text: str) -> str:
    pattern = re.compile(r"```html\s*(.*?)\s*```", re.I | re.S)
    match = pattern.search(text)
    return match.group(1).strip() if match else text.strip()

def wrap_iframe(html_content: str) -> str:
    escaped = html.escape(html_content)
    return f"""
    <iframe
        sandbox="allow-scripts allow-same-origin"
        style="width:100%; height:600px; border:none;"
        srcdoc="{escaped}"
    ></iframe>
    """
