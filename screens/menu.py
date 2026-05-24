"""
type hype — main menu screen.

Source picker and font size now live in the Settings menu; history lives
under View. The main screen shows only what you act on every test:
duration, difficulty, and start.
"""

import tkinter as tk
from tkinter import messagebox
import threading

from themes import get_theme
from widgets import (
    make_title_bar, make_button, make_label,
    make_separator, make_shadowed_panel, make_radio_group,
    Menubar,
)
import config as cfg

from engine.sources.literature import LiteratureSource
from engine.sources.wikipedia import WikipediaSource
from engine.sources.reddit import RedditSource
from engine.sources.poetry import PoetrySource
from engine.sources.code import CodeSource

SOURCES = {
    "literature": LiteratureSource(),
    "wikipedia":  WikipediaSource(),
    "reddit":     RedditSource(),
    "poetry":     PoetrySource(),
    "code":       CodeSource(language="python"),
}

# Order shown in the Source dropdown — fixed so additions land
# predictably and code mode sits with the other writing sources.
SOURCE_ORDER = ["literature", "poetry", "wikipedia", "reddit", "code"]

DURATIONS = [
    ("15s",  15),
    ("30s",  30),
    ("1m",   60),
    ("2m",  120),
    ("5m",  300),
]

FONT_STEPS = [
    ("tiny",   -4),
    ("small",  -2),
    ("normal",  0),
    ("large",  +2),
    ("xl",     +4),
]


class MenuScreen(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.theme = get_theme()

        conf = cfg.load()
        self.selected_duration   = tk.IntVar(value=conf.get("last_duration", 60))
        self.selected_difficulty = tk.StringVar(value="normal")
        self.selected_source_key = tk.StringVar(value=conf.get("last_source", "literature"))
        self.font_offset_var     = tk.IntVar(value=conf.get("font_size_offset", 0))
        self.status_var          = tk.StringVar(value="")

        self._reddit_source = SOURCES["reddit"]
        saved_subs = conf.get("subreddits", ["AskReddit", "todayilearned", "explainlikeimfive"])
        self._reddit_source.set_subreddits(saved_subs)

        self._build_ui()
        self._on_source_changed()

    # ═══════════════════════════════════ BUILD

    def _build_ui(self):
        t = self.theme
        self.configure(bg=t["bg"])

        make_title_bar(self, "type hype", t, on_close=self.app.destroy)
        self._build_menubar()

        outer = tk.Frame(self, bg=t["bg"], padx=16, pady=10)
        outer.pack(fill="both", expand=True)

        # ── logo
        logo_frame = tk.Frame(outer, bg=t["bg"])
        logo_frame.pack(fill="x", pady=(0, 10))
        tk.Label(logo_frame, text="type hype",
                 bg=t["bg"], fg=t["fg"],
                 font=t["font_display"]).pack()
        tk.Label(logo_frame, text="train your fingers, free your mind",
                 bg=t["bg"], fg=t["fg"],
                 font=t["font_small"]).pack(pady=(2, 0))

        self._build_source_info(outer)
        self._build_duration_panel(outer)
        self._build_start_button(outer)

        # ── status bar
        status_bar = tk.Frame(self, bg=t["bg"], relief=t["statusbar_relief"], bd=1)
        status_bar.pack(fill="x", side="bottom")
        tk.Label(status_bar, textvariable=self.status_var,
                 bg=t["bg"], fg=t["fg"],
                 font=t["font_small"], anchor="w").pack(fill="x", padx=4, pady=2)

    def _build_menubar(self):
        t = self.theme
        bar = Menubar(self, t)
        bar.pack(fill="x", side="top")

        # File
        file_menu = bar.add("File")
        file_menu.add_command("Quit  ⌘Q", command=self.app.destroy)

        # View
        view_menu = bar.add("View")
        view_menu.add_command("History…", command=self.app.show_history)

        # Source (flattened from Settings → Source for simpler UX)
        source_menu = bar.add("Source")
        for key in SOURCE_ORDER:
            source_menu.add_command(
                SOURCES[key].name.lower(),
                command=lambda k=key: self._on_source_selected(k),
            )

        # Font Size
        font_menu = bar.add("Font Size")
        for label, offset in FONT_STEPS:
            font_menu.add_command(
                label,
                command=lambda o=offset: self._on_font_selected(o),
            )

        # Help
        help_menu = bar.add("Help")
        help_menu.add_command(
            "About type hype…",
            command=lambda: messagebox.showinfo(
                "type hype",
                "type hype — a typing test for the rest of us.",
            ),
        )

        self._menubar = bar  # so we can rebuild check marks on change

        # 1px black line under the menubar
        tk.Frame(self, bg=t["separator_color"], height=1).pack(
            fill="x", side="top")

    def _build_source_info(self, parent):
        t = self.theme
        outer, panel = make_shadowed_panel(parent, t)
        outer.pack(fill="x", pady=(0, 8))

        header = tk.Frame(panel, bg=t["bg"])
        header.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(header, text="content source",
                 bg=t["bg"], fg=t["fg"],
                 font=t["font_ui_bold"]).pack(side="left")
        self._refresh_btn = make_button(header, "↻ refresh", t,
                                        command=self._fetch_source, width=10)
        self._refresh_btn.pack(side="right")

        make_separator(panel, t)

        self._source_meta = tk.Label(panel, text="", bg=t["bg"], fg=t["fg"],
                                     font=t["font_small"], anchor="w")
        self._source_meta.pack(fill="x", padx=8, pady=4)

        self._reddit_frame = tk.Frame(panel, bg=t["bg"])
        self._build_reddit_editor(self._reddit_frame)

    def _build_reddit_editor(self, parent):
        t = self.theme
        tk.Label(parent, text="subreddits:", bg=t["bg"], fg=t["fg"],
                 font=t["font_ui_bold"]).pack(anchor="w", padx=8, pady=(4, 0))

        self._sub_list_frame = tk.Frame(parent, bg=t["bg"])
        self._sub_list_frame.pack(fill="x", padx=8)
        self._refresh_sub_list()

        add_row = tk.Frame(parent, bg=t["bg"])
        add_row.pack(fill="x", padx=8, pady=4)

        self._sub_entry = tk.Entry(add_row, bg=t["input_bg"], fg=t["fg"],
                                   font=t["font_ui"], relief=t["frame_relief"],
                                   bd=t["border_width"], width=18,
                                   insertbackground=t["fg"])
        self._sub_entry.pack(side="left", padx=(0, 4))
        self._sub_entry.insert(0, "subreddit name")
        self._sub_entry.bind("<FocusIn>",
            lambda e: self._sub_entry.delete(0, "end")
            if self._sub_entry.get() == "subreddit name" else None)

        make_button(add_row, "+ add", t,
                    command=self._add_subreddit, width=8).pack(side="left")

    def _refresh_sub_list(self):
        t = self.theme
        for w in self._sub_list_frame.winfo_children():
            w.destroy()
        for sub in self._reddit_source.subreddits:
            row = tk.Frame(self._sub_list_frame, bg=t["bg"])
            row.pack(anchor="w")
            tk.Label(row, text=f"r/{sub}", bg=t["bg"], fg=t["fg"],
                     font=t["font_ui"]).pack(side="left")
            tk.Button(row, text="✕", bg=t["bg"], fg=t["timer_fg"],
                      font=t["font_small"], relief="flat", bd=0, cursor="hand2",
                      command=lambda s=sub: self._remove_subreddit(s)).pack(side="left", padx=2)

    def _add_subreddit(self):
        val = self._sub_entry.get().strip().lstrip("r/")
        if val and val not in self._reddit_source.subreddits and val != "subreddit name":
            self._reddit_source.subreddits.append(val)
            cfg.set_value("subreddits", self._reddit_source.subreddits)
            # Invalidate the cache so stale passages from the old sub
            # list don't sneak into the next test before refresh.
            self._reddit_source.clear_cache()
            self._refresh_sub_list()
            self._on_source_changed()
            self._sub_entry.delete(0, "end")

    def _remove_subreddit(self, sub):
        if sub in self._reddit_source.subreddits:
            self._reddit_source.subreddits.remove(sub)
            cfg.set_value("subreddits", self._reddit_source.subreddits)
            # Invalidate the cache so the removed sub's passages aren't
            # served up on the next test.
            self._reddit_source.clear_cache()
            self._refresh_sub_list()
            self._on_source_changed()

    def _build_duration_panel(self, parent):
        t = self.theme
        outer, panel = make_shadowed_panel(parent, t)
        outer.pack(fill="x", pady=(0, 8))

        make_label(panel, "  test duration", t, font_key="font_ui_bold",
                   anchor="w").pack(fill="x", padx=6, pady=(6, 2))
        make_separator(panel, t)

        make_radio_group(
            panel, t,
            variable=self.selected_duration,
            options=DURATIONS,
            command=lambda secs: cfg.set_value("last_duration", secs),
            btn_width=6,
        ).pack(pady=8, padx=6)

    def _build_start_button(self, parent):
        t = self.theme
        outer, panel = make_shadowed_panel(parent, t)
        outer.pack(fill="x", pady=(4, 0))
        make_button(panel, "▶  start test", t,
                    command=self._start_test, width=18).pack(
            fill="x", padx=8, pady=8)

    # ═══════════════════════════════════ ACTIONS

    def _on_source_selected(self, key):
        self.selected_source_key.set(key)
        cfg.set_value("last_source", key)
        self._on_source_changed()

    def _on_source_changed(self):
        key = self.selected_source_key.get()
        source = SOURCES.get(key)

        if key == "reddit":
            self._reddit_frame.pack(fill="x")
        else:
            self._reddit_frame.pack_forget()

        if source is None:
            return

        name = source.name.lower()
        if source.is_ready():
            count = len(source.get_corpus())
            self._source_meta.configure(
                text=f"✓  {name} ready — {count} items cached",
                fg=self.theme["fg"])
            self.status_var.set(f"ready: {name} — press start to begin.")
        else:
            self._source_meta.configure(
                text=f"⚠  {name} not yet fetched — click ↻ refresh",
                fg=self.theme["incorrect_fg"])
            self.status_var.set(f"{name} needs to be fetched first.")

    def _fetch_source(self):
        key = self.selected_source_key.get()
        source = SOURCES.get(key)
        if source is None:
            return

        self._refresh_btn.configure(state="disabled")
        self.status_var.set(f"fetching {source.name.lower()}…")

        # Marshal all Tk updates back to the main thread. Tkinter is
        # NOT thread-safe; calling widget.configure() or var.set() from
        # a worker thread can deadlock the Tk event loop. A non-200
        # response (e.g. 404 for a misspelled subreddit) hits this
        # exact deadlock path.
        def on_main(fn):
            try:
                self.after(0, fn)
            except Exception:
                pass

        def worker():
            def cb(msg):
                on_main(lambda m=msg: self.status_var.set(m.lower()))

            error_msg = None
            ok = False
            try:
                ok = source.fetch(status_cb=cb)
            except Exception as e:
                error_msg = str(e)

            def finalize():
                name = source.name.lower()
                try:
                    if error_msg is not None:
                        self.status_var.set(f"⚠ fetch error: {error_msg}")
                    elif ok:
                        self._on_source_changed()
                        self.status_var.set(f"✓ {name} fetched successfully.")
                    else:
                        if not self.status_var.get().startswith("⚠ fetch error"):
                            self.status_var.set(
                                f"⚠ {name} fetch failed — "
                                "check the subreddit name and your connection.")
                        # Make the empty state visible too — without this
                        # the panel still says "ready: N items" from the
                        # previous fetch even though we cleared the cache.
                        self._on_source_changed()
                    self._refresh_btn.configure(state="normal")
                except Exception:
                    pass

            on_main(finalize)

        threading.Thread(target=worker, daemon=True).start()

    def _on_font_selected(self, offset):
        self.font_offset_var.set(offset)
        cfg.set_value("font_size_offset", offset)
        self.app.font_size_offset = offset

    def _start_test(self):
        key    = self.selected_source_key.get()
        source = SOURCES.get(key, SOURCES["literature"])

        if not source.is_ready():
            ok = messagebox.askyesno(
                "source not ready",
                f"{source.name.lower()} hasn't been fetched yet.\n\nfetch it now?"
            )
            if ok:
                self._fetch_source()
            return

        passage, meta = source.get_passage(self.selected_duration.get())
        self.app.start_test(
            duration=self.selected_duration.get(),
            difficulty=self.selected_difficulty.get(),
            passage=passage,
            meta=meta,
            source_key=key,
        )
