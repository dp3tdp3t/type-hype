"""
Results screen — shows scores and saves to CSV log.
"""

import tkinter as tk
import csv
import os
import datetime

from themes import get_theme
from widgets import (
    make_title_bar, make_button, make_separator, make_shadowed_panel,
)

from paths import data_file
RESULTS_FILE = data_file("typing_results.csv")
CSV_HEADERS = [
    "timestamp", "duration_s", "elapsed_s", "difficulty",
    "source", "gross_wpm", "net_wpm", "accuracy_pct", "errors",
    "backspaces", "chars_typed"
]


def save_result(row: dict):
    """Append a row to the results CSV, rewriting the whole file so any
    obsolete columns (like the dropped `theme` column) get stripped."""
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    existing = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    existing.append(row)
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS, extrasaction="ignore")
        writer.writeheader()
        for r in existing:
            writer.writerow(r)


class ResultsScreen(tk.Frame):
    def __init__(self, master, app, scores: dict, duration: int,
                 difficulty: str, elapsed: float,
                 source_key: str = "literature", meta: str = ""):
        super().__init__(master)
        self.app = app
        self.theme_name = app.theme_name
        self.theme = get_theme(self.theme_name)
        self.scores = scores
        self.duration = duration
        self.difficulty = difficulty
        self.elapsed = elapsed
        self.source_key = source_key
        self.meta = meta
        self._saved = False

        self._save_result()
        self._build_ui()

    # ------------------------------------------------------------------ save

    def _save_result(self):
        row = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_s": self.duration,
            "elapsed_s": round(self.elapsed, 2),
            "difficulty": self.difficulty,
            "source": self.source_key,
            "gross_wpm": self.scores["gross_wpm"],
            "net_wpm": self.scores["net_wpm"],
            "accuracy_pct": self.scores["accuracy"],
            "errors": self.scores["errors"],
            "backspaces": self.scores["backspaces"],
            "chars_typed": self.scores["chars_typed"],
        }
        save_result(row)
        self._saved = True

    # ------------------------------------------------------------------ build

    def _build_ui(self):
        t = self.theme
        self.configure(bg=t["bg"])

        make_title_bar(self, f"results — {t['name']}", t,
                       on_close=self.app.show_menu)

        outer = tk.Frame(self, bg=t["bg"], padx=12, pady=10)
        outer.pack(fill="both", expand=True)

        # ── Header
        header_outer, header = make_shadowed_panel(outer, t)
        header_outer.pack(fill="x", pady=(0, 8))
        tk.Label(
            header,
            text="🏆  test complete!",
            bg=t["bg"], fg=t["accent"],
            font=(t["font_mono_large"][0], 18, "bold"),
            pady=6,
        ).pack()
        tk.Label(
            header,
            text=f"duration: {self.duration}s  |  Elapsed: {self.elapsed:.1f}s  |  difficulty: {self.difficulty.title()}",
            bg=t["bg"], fg=t["separator_color"],
            font=t["font_small"],
        ).pack(pady=(0, 4))

        # ── Main score boxes
        scores_frame = tk.Frame(outer, bg=t["bg"])
        scores_frame.pack(fill="x", pady=4)

        self._score_box(scores_frame, "gross wpm",
                        str(self.scores["gross_wpm"]), t["wpm_fg"])
        self._score_box(scores_frame, "net wpm",
                        str(self.scores["net_wpm"]), t["wpm_fg"])
        self._score_box(scores_frame, "accuracy",
                        f"{self.scores['accuracy']}%", t["correct_fg"])

        # ── Secondary stats
        secondary_outer, secondary = make_shadowed_panel(outer, t)
        secondary_outer.pack(fill="x", pady=6)
        make_separator(secondary, t)

        grid = tk.Frame(secondary, bg=t["bg"])
        grid.pack(pady=6)

        self._stat_row(grid, 0, "Characters Typed:", str(self.scores["chars_typed"]))
        self._stat_row(grid, 1, "errors (uncorrected):", str(self.scores["errors"]))
        self._stat_row(grid, 2, "backspaces Used:",
                       str(self.scores["backspaces"]),
                       warn=self.scores["backspaces"] > 20)

        make_separator(secondary, t)

        # ── Save notice
        save_note = "✓ result saved to typing_results.csv" if self._saved else "⚠ could not save result."
        tk.Label(
            outer, text=save_note,
            bg=t["bg"], fg=t["correct_fg"] if self._saved else t["timer_fg"],
            font=t["font_small"],
        ).pack(pady=2)

        # ── Buttons
        btn_frame = tk.Frame(outer, bg=t["bg"])
        btn_frame.pack(pady=10)

        make_button(btn_frame, "▶  try again", t,
                    command=self._try_again, width=14).pack(side="left", padx=6)
        make_button(btn_frame, "📋  history", t,
                    command=self.app.show_history, width=12).pack(side="left", padx=6)
        make_button(btn_frame, "🏠  main menu", t,
                    command=self.app.show_menu, width=14).pack(side="left", padx=6)

    def _score_box(self, parent, label, value, color):
        t = self.theme
        box_outer, box = make_shadowed_panel(parent, t)
        box_outer.pack(side="left", expand=True, fill="x", padx=4)
        tk.Label(box, text=label,
                 bg=t["bg"], fg=t["fg"],
                 font=t["font_small"]).pack(pady=(8, 0))
        tk.Label(box, text=value,
                 bg=t["bg"], fg=color,
                 font=(t["font_mono_large"][0], 28, "bold")).pack()
        tk.Label(box, text="", bg=t["bg"]).pack(pady=4)

    def _stat_row(self, parent, row, label, value, warn=False):
        t = self.theme
        tk.Label(parent, text=label, bg=t["bg"], fg=t["fg"],
                 font=t["font_ui"], anchor="e", width=22).grid(
            row=row, column=0, padx=6, pady=2, sticky="e")
        color = t["timer_fg"] if warn else t["accent"]
        tk.Label(parent, text=value, bg=t["bg"], fg=color,
                 font=t["font_ui_bold"], anchor="w", width=10).grid(
            row=row, column=1, padx=6, pady=2, sticky="w")

    def _try_again(self):
        # Use the same singleton source instances the menu screen uses
        # so try-again actually replays the source from the just-finished
        # test (including 'code', which the old local dict didn't list
        # at all — it always fell through to literature).
        from screens.menu import SOURCES

        source = SOURCES.get(self.source_key)
        used_key = self.source_key
        if source is None or not source.is_ready():
            # The original source vanished between tests (e.g. user
            # cleared the reddit cache from another screen). Fall back
            # to literature so try-again still works.
            source = SOURCES["literature"]
            used_key = "literature"

        passage, meta = source.get_passage(self.duration)
        self.app.start_test(
            duration=self.duration,
            difficulty=self.difficulty,
            passage=passage,
            meta=meta,
            source_key=used_key,
        )
