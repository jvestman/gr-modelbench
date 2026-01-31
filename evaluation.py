from logging_eav import log_generation_eav

def save_evaluation(
    run_id,
    color_typography,
    layout,
    correctness,
    functionality,
    comments
):
    if not run_id:
        return "No generation to evaluate."

    log_generation_eav(run_id, {
        "eval_visual_color_typography": color_typography,
        "eval_layout_structure": layout,
        "eval_correctness": correctness,
        "eval_functionality": functionality,
        "eval_comments": comments.strip() if comments else ""
    })

    return "✅ Evaluation saved"
