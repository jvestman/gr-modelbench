from utils import wrap_iframe

def render_preview(html_code: str, preview_url: str):
    link_md = f"🔗 **[Open preview in new tab]({preview_url})**"
    iframe = wrap_iframe(html_code)
    return link_md, iframe
