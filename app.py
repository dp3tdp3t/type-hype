"""
type hype — root window and screen manager.

Borderless (overrideredirect) so our striped title bar is the only chrome;
drag via the title bar, resize via the grow box in the bottom-right.
"""

import os
import subprocess
import sys
import tkinter as tk
from themes import get_theme
from widgets import make_grow_box
import config as cfg


def _activate_self_on_macos():
    """Make our Python process the frontmost macOS app.

    Tk's `overrideredirect(True)` keeps the window from automatically
    becoming the key window, so the OS sends keystrokes to whatever
    *was* active before we launched (Terminal, the Python Launcher,
    etc.). AppleScript-activating ourselves by PID fixes that without
    requiring PyObjC."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            ["osascript", "-e",
             f'tell application "System Events" to '
             f'set frontmost of (first process whose unix id is {os.getpid()}) to true'],
            check=False, timeout=2,
        )
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.theme_name = "mac_light"
        self.font_size_offset = cfg.get("font_size_offset") or 0

        w, h = 920, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(560, 380)

        theme = get_theme()
        self.configure(bg=theme["bg"])
        self.overrideredirect(True)

        self._current_screen = None

        # global keyboard shortcuts (still work without OS chrome)
        self.bind_all("<Command-q>", lambda _e: self.destroy())
        self.bind_all("<Command-w>", lambda _e: self.destroy())
        self.bind_all("<Control-q>", lambda _e: self.destroy())

        self.show_menu()

        # grow box stays on top of every screen, anchored to the toplevel
        self._grow_box = make_grow_box(self, theme, resize_target=self)
        self._grow_box.place(relx=1.0, rely=1.0, anchor="se")

        # bring the borderless window forward + claim keyboard focus
        # (overrideredirect windows don't become "key window" automatically
        # on macOS — the topmost-flip + focus_force dance is the workaround)
        self.after(50, self.claim_focus)
        # Also force our Python process to be the frontmost macOS app,
        # otherwise keystrokes go to whatever app was active before us.
        self.after(100, _activate_self_on_macos)

    def claim_focus(self):
        """Force OS-level keyboard focus back onto this borderless window.

        Called on each screen swap so the freshly-built screen has
        keyboard focus. The custom Menubar / DropdownMenu in widgets.py
        avoids native tk.Menu popups (which steal OS focus on macOS),
        so this is now a light-touch operation."""
        try:
            self.lift()
            self.attributes("-topmost", True)
            self.update_idletasks()
            self.attributes("-topmost", False)
            self.focus_force()
        except Exception:
            pass

    def _set_screen(self, screen):
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screen
        screen.pack(fill="both", expand=True)
        if getattr(self, "_grow_box", None) is not None:
            self._grow_box.tkraise()
        # Re-claim keyboard focus after a screen swap — borderless windows
        # can drift out of the "key window" role on macOS, especially
        # after a tk.Menu popup has been opened.
        self.claim_focus()

    # ── screens

    def show_menu(self):
        from screens.menu import MenuScreen
        self._set_screen(MenuScreen(self, self))

    def start_test(self, duration: int, difficulty: str,
                   passage: str, meta: str = "", source_key: str = "literature"):
        from screens.test import TestScreen
        self._set_screen(TestScreen(self, self, duration, difficulty,
                                    passage, meta, source_key))

    def show_results(self, scores: dict, duration: int, difficulty: str,
                     elapsed: float, source_key: str = "literature", meta: str = ""):
        from screens.results import ResultsScreen
        self._set_screen(ResultsScreen(self, self, scores, duration,
                                       difficulty, elapsed, source_key, meta))

    def show_history(self):
        from screens.history import HistoryScreen
        self._set_screen(HistoryScreen(self, self))
