"""
Theme definitions for type hype — System 1.0 (Mac OS 1.0) aesthetic.

Single light theme. Fonts are resolved lazily once a Tk root exists, so we
can pick the best available Chicago-style family rather than guessing.
"""

import tkinter as tk
import tkinter.font as tkfont


_MONO_FONT_FAMILY = "Monaco"

# Chicago-style display font candidates, best first. If the user installs
# a Chicago lookalike (e.g. ChicagoFLF, ChiKareGo2), we'll pick it up.
_UI_FONT_CANDIDATES = [
    "Chicago",
    "ChicagoFLF",
    "Chicago Plain",
    "ChiKareGo2",
    "ChiKareGo",
    "Charcoal CY",
    "Charcoal",
    "Geneva",
]

_DISPLAY_FONT_CANDIDATES = [
    "Chicago",
    "ChicagoFLF",
    "Chicago Plain",
    "ChiKareGo2",
    "ChiKareGo",
    "Charcoal CY",
    "Charcoal",
    "Geneva",
]

_resolved = False
_UI_FAMILY = "Geneva"
_DISPLAY_FAMILY = "Geneva"


def _resolve_fonts():
    """Pick the best installed Chicago-ish families. Idempotent."""
    global _resolved, _UI_FAMILY, _DISPLAY_FAMILY
    if _resolved:
        return
    try:
        # Needs a Tk root to query families.
        if tk._default_root is None:
            tmp = tk.Tk()
            tmp.withdraw()
            families = set(tkfont.families())
            tmp.destroy()
        else:
            families = set(tkfont.families())
        for c in _UI_FONT_CANDIDATES:
            if c in families:
                _UI_FAMILY = c
                break
        for c in _DISPLAY_FONT_CANDIDATES:
            if c in families:
                _DISPLAY_FAMILY = c
                break
    except Exception:
        pass
    _resolved = True


def _theme():
    _resolve_fonts()
    return {
        "name": "system 1.0",

        "bg": "#FFFFFF",
        "fg": "#000000",
        "title_bar_bg": "#FFFFFF",
        "title_bar_fg": "#000000",
        "accent": "#000000",
        "shadow_color": "#000000",

        "button_bg": "#FFFFFF",
        "button_fg": "#000000",
        "button_active_bg": "#000000",
        "button_active_fg": "#FFFFFF",
        "highlight_bg": "#000000",
        "highlight_fg": "#FFFFFF",

        "input_bg": "#FFFFFF",
        "input_fg": "#000000",

        "correct_fg": "#000000",
        "incorrect_fg": "#CC0000",
        "untyped_fg": "#888888",
        "cursor_color": "#000000",
        "timer_fg": "#CC0000",
        "wpm_fg": "#000000",

        "font_ui":         (_UI_FAMILY, 11),
        "font_ui_bold":    (_UI_FAMILY, 11, "bold"),
        "font_title":      (_UI_FAMILY, 12, "bold"),
        "font_small":      (_UI_FAMILY, 10),
        "font_display":    (_DISPLAY_FAMILY, 24, "bold"),
        "font_mono":       (_MONO_FONT_FAMILY, 14),
        "font_mono_large": (_MONO_FONT_FAMILY, 20, "bold"),

        "border_relief_raised": "solid",
        "border_relief_sunken": "solid",
        "border_relief_ridge":  "solid",
        "border_width": 1,
        "panel_relief": "solid",
        "frame_relief": "solid",
        "statusbar_relief": "solid",

        "menubar_bg": "#FFFFFF",
        "separator_color": "#000000",
        "scrollbar_bg": "#FFFFFF",
        "trough_color": "#FFFFFF",

        "close_box_bg": "#FFFFFF",
        "close_box_fg": "#000000",
        "radio_select_bg": "#000000",
    }


def get_theme(_name=None):
    """Return the single System 1.0 theme. `_name` accepted for back-compat."""
    return _theme()
