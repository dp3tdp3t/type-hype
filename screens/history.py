"""
History screen — scrollable table of past typing test results.
"""

import tkinter as tk
import csv
import os

from themes import get_theme
from widgets import (
    make_title_bar, make_button, make_separator, make_shadowed_panel,
)

from paths import data_file
RESULTS_FILE = data_file("typing_results.csv")

COLUMNS = [
    ("date/time",      "timestamp",    18),
    ("duration",       "duration_s",    8),
    ("gross wpm",      "gross_wpm",     9),
    ("net wpm",        "net_wpm",       9),
    ("accuracy",       "accuracy_pct",  9),
    ("errors",         "errors",        7),
    ("backspaces",     "backspaces",   10),
    ("source",         "source",       12),
    ("difficulty",     "difficulty",    9),
]


class HistoryScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.theme_name = app.theme_name
        self.theme = get_theme(self.theme_name)
        self._build_ui()

    def _build_ui(self):
        t = self.theme
        self.configure(bg=t["bg"])

        make_title_bar(self, f"typing history — {t['name']}", t,
                       on_close=self.app.show_menu)

        outer = tk.Frame(self, bg=t["bg"], padx=10, pady=8)
        outer.pack(fill="both", expand=True)

        # ── Header
        tk.Label(
            outer, text="📋  past results",
            bg=t["bg"], fg=t["accent"],
            font=(t["font_mono_large"][0], 16, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        # ── Table area
        table_outer, table_frame = make_shadowed_panel(outer, t)
        table_frame.configure(bg=t["input_bg"])
        table_outer.pack(fill="both", expand=True)

        # Header row
        header_frame = tk.Frame(table_frame, bg=t["highlight_bg"])
        header_frame.pack(fill="x")
        for col_label, _, width in COLUMNS:
            tk.Label(
                header_frame, text=col_label,
                bg=t["highlight_bg"], fg=t["highlight_fg"],
                font=t["font_ui_bold"], width=width,
                relief="flat", anchor="w", padx=4,
            ).pack(side="left")

        make_separator(table_frame, t)

        # Scrollable body
        canvas = tk.Canvas(table_frame, bg=t["input_bg"],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(table_frame, orient="vertical",
                                  command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)

        body_frame = tk.Frame(canvas, bg=t["input_bg"])
        canvas_window = canvas.create_window((0, 0), window=body_frame, anchor="nw")

        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        body_frame.bind("<Configure>", on_frame_configure)

        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)

        # Load and display rows
        rows = self._load_rows()
        if not rows:
            tk.Label(
                body_frame, text="no results yet — complete a test to see history.",
                bg=t["input_bg"], fg=t["separator_color"],
                font=t["font_ui"], pady=20,
            ).pack()
        else:
            for i, row in enumerate(reversed(rows)):  # newest first
                bg = t["input_bg"] if i % 2 == 0 else t["bg"]
                row_frame = tk.Frame(body_frame, bg=bg)
                row_frame.pack(fill="x")
                for col_label, key, width in COLUMNS:
                    val = row.get(key, "")
                    # Prettify a couple of values
                    if key == "duration_s":
                        val = f"{val}s"
                    elif key == "accuracy_pct":
                        val = f"{val}%"
                    elif key == "gross_wpm" or key == "net_wpm":
                        val = f"{val}"
                    tk.Label(
                        row_frame, text=val,
                        bg=bg, fg=t["fg"],
                        font=t["font_ui"], width=width,
                        anchor="w", padx=4,
                    ).pack(side="left")

        # Summary stats
        if rows:
            make_separator(outer, t)
            self._build_summary(outer, rows, t)

        # ── Back button
        btn_frame = tk.Frame(outer, bg=t["bg"])
        btn_frame.pack(pady=8)
        make_button(btn_frame, "🏠  main menu", t,
                    command=self.app.show_menu, width=14).pack(side="left", padx=6)
        make_button(btn_frame, "▶  new test", t,
                    command=self._new_test, width=12).pack(side="left", padx=6)

    def _load_rows(self):
        if not os.path.exists(RESULTS_FILE):
            return []
        with open(RESULTS_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _build_summary(self, parent, rows, t):
        try:
            net_wpms = [float(r["net_wpm"]) for r in rows if r.get("net_wpm")]
            gross_wpms = [float(r["gross_wpm"]) for r in rows if r.get("gross_wpm")]
            accs = [float(r["accuracy_pct"]) for r in rows if r.get("accuracy_pct")]
            bss = [int(r["backspaces"]) for r in rows if r.get("backspaces")]
        except Exception:
            return

        panel_outer, panel = make_shadowed_panel(parent, t)
        panel_outer.pack(fill="x", pady=4)
        tk.Label(panel, text="  all-time summary", bg=t["bg"], fg=t["accent"],
                 font=t["font_ui_bold"], anchor="w").pack(fill="x", padx=6, pady=(4, 0))
        make_separator(panel, t)

        row = tk.Frame(panel, bg=t["bg"])
        row.pack(pady=4)
        stats = [
            ("tests",       str(len(rows))),
            ("best net",    f"{max(net_wpms):.1f} WPM"),
            ("avg net",     f"{sum(net_wpms)/len(net_wpms):.1f} WPM"),
            ("avg gross",   f"{sum(gross_wpms)/len(gross_wpms):.1f} WPM"),
            ("avg acc",     f"{sum(accs)/len(accs):.1f}%"),
            ("avg bs",      f"{sum(bss)/len(bss):.1f}"),
        ]
        for label, val in stats:
            box = tk.Frame(row, bg=t["bg"], relief=t["panel_relief"], bd=t["border_width"])
            box.pack(side="left", padx=4, ipadx=4, ipady=2)
            tk.Label(box, text=label, bg=t["bg"], fg=t["separator_color"],
                     font=t["font_small"]).pack()
            tk.Label(box, text=val, bg=t["bg"], fg=t["wpm_fg"],
                     font=t["font_ui_bold"]).pack()

    def _new_test(self):
        from engine.sources.literature import LiteratureSource
        source = LiteratureSource()
        passage, meta = source.get_passage(60)
        self.app.start_test(duration=60, difficulty="normal",
                            passage=passage, meta=meta, source_key="literature")
