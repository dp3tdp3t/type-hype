"""
Scoring logic: gross WPM, net WPM, accuracy, error counting.
"""


def compute_scores(typed: str, target: str, elapsed_seconds: float, backspaces: int):
    """
    Returns a dict with:
        gross_wpm   - total characters typed / 5 / minutes
        net_wpm     - gross_wpm - (uncorrected_errors / minutes)
        accuracy    - % of characters typed correctly (against target)
        errors      - number of incorrect character positions
        backspaces  - passed through as-is
        chars_typed - total characters typed (including wrong ones)
    """
    if elapsed_seconds <= 0:
        return {
            "gross_wpm": 0.0,
            "net_wpm": 0.0,
            "accuracy": 0.0,
            "errors": 0,
            "backspaces": backspaces,
            "chars_typed": 0,
        }

    minutes = elapsed_seconds / 60.0
    chars_typed = len(typed)

    # Gross WPM: all keystrokes / 5 / minutes
    gross_wpm = (chars_typed / 5.0) / minutes

    # Count character-level errors (positions where typed != target)
    errors = 0
    for i, ch in enumerate(typed):
        if i >= len(target) or ch != target[i]:
            errors += 1

    # Net WPM subtracts uncorrected error words (errors / 5) per minute
    error_words = errors / 5.0
    net_wpm = max(0.0, gross_wpm - (error_words / minutes))

    # Accuracy: correct chars / total typed
    correct = chars_typed - errors
    accuracy = (correct / chars_typed * 100.0) if chars_typed > 0 else 0.0

    return {
        "gross_wpm": round(gross_wpm, 1),
        "net_wpm": round(net_wpm, 1),
        "accuracy": round(accuracy, 1),
        "errors": errors,
        "backspaces": backspaces,
        "chars_typed": chars_typed,
    }
