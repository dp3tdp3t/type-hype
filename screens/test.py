"""
type hype screen — live character highlighting, timer, WPM counter.
Supports font size offset (from config) and Ctrl+=/- live resize.
"""

import tkinter as tk
import time

from themes import get_theme
from widgets import make_title_bar, make_separator, make_shadowed_panel
from engine.scorer import compute_scores
import config as cfg


class TestScreen(tk.Frame):
    def __init__(self, master, app, duration: int, difficulty: str,
                 passage: str, meta: str = "", source_key: str = "literature"):
        super().__init__(master)
        self.app = app
        self.theme_name = app.theme_name
        self.theme = get_theme(self.theme_name)
        self.duration = duration
        self.difficulty = difficulty
        self.passage = passage
        self.meta = meta
        self.source_key = source_key

        self.typed = ""
        self.backspaces = 0
        self.start_time = None
        self.elapsed = 0.0
        self.running = False
        self._timer_id = None

        # Font size offset (from app or config)
        self._font_offset = getattr(app, "font_size_offset", cfg.get("font_size_offset") or 0)

        self._build_ui()
        self._render_passage()
        self.after(100, self._focus_input)

    # ═══════════════════════════════════════════════════════════════ FONT HELPERS

    def _mono_font(self, base_size=14, bold=False):
        t = self.theme
        family = t["font_mono"][0]
        size = base_size + self._font_offset
        size = max(8, min(size, 36))
        return (family, size, "bold") if bold else (family, size)

    def _ui_font(self, base_size=None, bold=False):
        t = self.theme
        family = t["font_ui"][0]
        if base_size is None:
            base_size = t["font_ui"][1]
        size = base_size + max(0, self._font_offset // 2)
        size = max(7, min(size, 24))
        return (family, size, "bold") if bold else (family, size)

    # ═══════════════════════════════════════════════════════════════ BUILD

    def _build_ui(self):
        t = self.theme
        self.configure(bg=t["bg"])

        make_title_bar(self, f"type hype — {self.duration}s  |  {t['name']}",
                       t, on_close=self._confirm_quit)

        # ── Stats bar
        stats_outer, stats_bar = make_shadowed_panel(self, t)
        stats_outer.pack(fill="x", padx=8, pady=(6, 0))

        self.timer_label = tk.Label(
            stats_bar, text=f"{self.duration}s",
            bg=t["bg"], fg=t["timer_fg"],
            font=self._mono_font(16, bold=True), width=6)
        self.timer_label.pack(side="left", padx=10, pady=4)

        tk.Frame(stats_bar, bg=t["separator_color"], width=1).pack(side="left", fill="y", pady=4)

        for attr, label_text in [
            ("gross_wpm_label", "gross wpm"),
            ("net_wpm_label",   "net wpm"),
            ("bs_label",        "backspaces"),
            ("acc_label",       "accuracy"),
        ]:
            tk.Frame(stats_bar, bg=t["separator_color"], width=1).pack(
                side="left", fill="y", pady=4) if attr != "gross_wpm_label" else None
            f = tk.Frame(stats_bar, bg=t["bg"])
            f.pack(side="left", padx=8, pady=4)
            tk.Label(f, text=label_text, bg=t["bg"], fg=t["separator_color"],
                     font=self._ui_font(8)).pack()
            val = "0" if attr == "bs_label" else "—"
            lbl = tk.Label(f, text=val, bg=t["bg"], fg=t["wpm_fg"],
                           font=self._mono_font(13, bold=True))
            lbl.pack()
            setattr(self, attr, lbl)

        # Font size controls in stats bar
        tk.Frame(stats_bar, bg=t["separator_color"], width=1).pack(side="right", fill="y", pady=4)
        font_frame = tk.Frame(stats_bar, bg=t["bg"])
        font_frame.pack(side="right", padx=6, pady=4)
        tk.Label(font_frame, text="Font", bg=t["bg"], fg=t["separator_color"],
                 font=self._ui_font(8)).pack()
        btn_row = tk.Frame(font_frame, bg=t["bg"])
        btn_row.pack()
        tk.Button(btn_row, text="A-", command=self._font_down,
                  bg=t["button_bg"], fg=t["fg"],
                  relief=t["border_relief_raised"], bd=t["border_width"],
                  font=self._ui_font(8), cursor="hand2", padx=2).pack(side="left")
        tk.Button(btn_row, text="A+", command=self._font_up,
                  bg=t["button_bg"], fg=t["fg"],
                  relief=t["border_relief_raised"], bd=t["border_width"],
                  font=self._ui_font(9, bold=True), cursor="hand2", padx=2).pack(side="left", padx=2)

        # Give up
        tk.Button(stats_bar, text="✖ give up", bg=t["button_bg"], fg=t["timer_fg"],
                  relief=t["border_relief_raised"], bd=t["border_width"],
                  font=self._ui_font(bold=True), command=self._confirm_quit,
                  cursor="hand2").pack(side="right", padx=10, pady=4)

        # ── Passage display
        passage_shadow, passage_outer = make_shadowed_panel(self, t)
        passage_outer.configure(bg=t["input_bg"])
        passage_shadow.pack(fill="both", expand=True, padx=8, pady=8)

        self.passage_text = tk.Text(
            passage_outer,
            wrap="word",
            font=self._mono_font(14),
            bg=t["input_bg"], fg=t["untyped_fg"],
            relief="flat", bd=0,
            state="disabled",
            cursor="arrow",
            padx=12, pady=10,
        )
        self.passage_text.pack(fill="both", expand=True)
        self._configure_passage_tags()

        # ── Invisible input capture
        self.input_capture = tk.Entry(
            self, bg=t["bg"], fg=t["bg"],
            insertbackground=t["bg"],
            relief="flat", bd=0, font=("Courier", 1), width=1,
        )
        self.input_capture.place(x=-200, y=-200)
        self.input_capture.bind("<KeyPress>",   self._on_keypress)
        self.input_capture.bind("<BackSpace>",  self._on_backspace)
        self.input_capture.bind("<Control-equal>",  lambda e: self._font_up())
        self.input_capture.bind("<Control-minus>",   lambda e: self._font_down())
        self.input_capture.bind("<Control-KP_Add>",  lambda e: self._font_up())
        self.input_capture.bind("<Control-KP_Subtract>", lambda e: self._font_down())

        # ── Status/meta bar
        status_bar = tk.Frame(self, bg=t["bg"], relief=t["statusbar_relief"], bd=1)
        status_bar.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="start typing to begin the test…")
        meta_text = f"  {self.meta}  |  " if self.meta else "  "
        self.status_var.set(f"{meta_text}start typing to begin…")
        tk.Label(status_bar, textvariable=self.status_var,
                 bg=t["bg"], fg=t["separator_color"],
                 font=self._ui_font(8), anchor="w").pack(fill="x", padx=4, pady=2)

    def _configure_passage_tags(self):
        t = self.theme
        self.passage_text.tag_configure("correct",   foreground=t["correct_fg"])
        self.passage_text.tag_configure("incorrect", foreground=t["incorrect_fg"],
                                        background="#FFE0E0")
        self.passage_text.tag_configure("untyped",   foreground=t["untyped_fg"])
        self.passage_text.tag_configure("cursor_pos",
                                        background=t["cursor_color"],
                                        foreground=t["input_bg"])

    def _focus_input(self):
        # Reclaim OS-level keyboard focus AND Tk-level focus, and
        # repeat the dance a few times in case any of the previous
        # screen's widgets (a tk.Entry the user typed in, a Button
        # that was just clicked) left the focus state in flux.
        self._reclaim_focus(attempts_left=5)

    def _reclaim_focus(self, attempts_left: int):
        try:
            self.app.claim_focus()
            # Reset Tk's internal focus tracking by pointing focus at
            # the toplevel first, then redirecting to our Entry.
            self.app.focus_set()
            self.input_capture.focus_set()
        except Exception:
            pass
        if attempts_left > 0:
            self.after(80, lambda: self._reclaim_focus(attempts_left - 1))

    # ═══════════════════════════════════════════════════════════════ FONT RESIZE

    def _font_up(self):
        self._font_offset = min(self._font_offset + 2, 14)
        self._apply_font_resize()

    def _font_down(self):
        self._font_offset = max(self._font_offset - 2, -4)
        self._apply_font_resize()

    def _apply_font_resize(self):
        cfg.set_value("font_size_offset", self._font_offset)
        self.app.font_size_offset = self._font_offset
        self.passage_text.configure(font=self._mono_font(14))
        self.input_capture.focus_set()

    # ═══════════════════════════════════════════════════════════════ PASSAGE RENDER

    def _render_passage(self):
        tw = self.passage_text
        tw.configure(state="normal")
        tw.delete("1.0", "end")
        tw.insert("end", self.passage)

        for tag in ("correct", "incorrect", "untyped", "cursor_pos"):
            tw.tag_remove(tag, "1.0", "end")

        for i, ch in enumerate(self.typed):
            start = f"1.0+{i}c"
            end   = f"1.0+{i+1}c"
            tag   = "correct" if (i < len(self.passage) and ch == self.passage[i]) else "incorrect"
            tw.tag_add(tag, start, end)

        pos = len(self.typed)
        if pos < len(self.passage):
            tw.tag_add("cursor_pos", f"1.0+{pos}c", f"1.0+{pos+1}c")
            tw.see(f"1.0+{pos}c")

        tw.configure(state="disabled")

    # ═══════════════════════════════════════════════════════════════ INPUT

    def _on_keypress(self, event):
        # Ctrl+= / Ctrl+- handled by separate bindings
        if event.state & 0x4:   # Control held
            return "break"

        # Map Return to a literal '\n' so multi-line passages (code
        # mode) can be typed. Tk gives event.char='\r' or '' for
        # Return depending on platform, so we normalize via keysym.
        if event.keysym == "Return":
            char = "\n"
        else:
            char = event.char

        if not self.running:
            if char and event.keysym not in (
                    "BackSpace", "Tab", "Escape", "Delete"):
                self._start_timer()
            else:
                return "break"

        if not self.running:
            return "break"

        if not char or event.keysym in (
                "BackSpace", "Tab", "Escape", "Delete",
                "Left", "Right", "Up", "Down", "Home", "End",
                "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
        ):
            return "break"

        if len(self.typed) < len(self.passage):
            self.typed += char
            self._render_passage()
            self._update_stats()
            if len(self.typed) >= len(self.passage):
                self._end_test()

        return "break"

    def _on_backspace(self, event):
        if not self.running:
            return "break"
        if self.typed:
            self.typed = self.typed[:-1]
            self.backspaces += 1
            self.bs_label.configure(text=str(self.backspaces))
            self._render_passage()
            self._update_stats()
        return "break"

    # ═══════════════════════════════════════════════════════════════ TIMER

    def _start_timer(self):
        self.running = True
        self.start_time = time.time()
        meta_prefix = f"{self.meta}  |  " if self.meta else ""
        self.status_var.set(f"  {meta_prefix}test in progress…")
        self._tick()

    def _tick(self):
        if not self.running:
            return
        self.elapsed = time.time() - self.start_time
        remaining = max(0, self.duration - self.elapsed)
        self.timer_label.configure(text=f"{int(remaining)}s")
        if remaining <= 10:
            self.timer_label.configure(fg="#FF0000")
        self._update_stats()
        if remaining <= 0:
            self._end_test()
        else:
            self._timer_id = self.after(100, self._tick)

    def _update_stats(self):
        elapsed = max(self.elapsed, 0.1)
        scores = compute_scores(self.typed, self.passage, elapsed, self.backspaces)
        self.gross_wpm_label.configure(text=str(scores["gross_wpm"]))
        self.net_wpm_label.configure(text=str(scores["net_wpm"]))
        self.acc_label.configure(text=f"{scores['accuracy']}%")

    # ═══════════════════════════════════════════════════════════════ END

    def _end_test(self):
        if not self.running:
            return
        self.running = False
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self.elapsed = time.time() - self.start_time if self.start_time else 0
        scores = compute_scores(self.typed, self.passage, self.elapsed, self.backspaces)
        self.status_var.set("  test complete!")
        self.timer_label.configure(text="done!", fg=self.theme["correct_fg"])
        self.after(500, lambda: self.app.show_results(
            scores=scores,
            duration=self.duration,
            difficulty=self.difficulty,
            elapsed=self.elapsed,
            source_key=self.source_key,
            meta=self.meta,
        ))

    def _confirm_quit(self):
        from tkinter import messagebox
        if self.running:
            if not messagebox.askyesno("give up?", "quit this test?"):
                self.input_capture.focus_set()
                return
            self.running = False
            if self._timer_id:
                self.after_cancel(self._timer_id)
        self.app.show_menu()
