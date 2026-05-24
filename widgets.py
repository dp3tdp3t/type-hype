"""
Reusable widget helpers — System 1.0 aesthetic.

Title bar gets stripes, centered title, close box at left, and (by default)
drags the parent toplevel window. A `make_grow_box` helper at the bottom
right of the window provides resize.
"""

import tkinter as tk


# ───────────────────────────────────────────────────────────── title bar

_TITLE_BAR_HEIGHT = 20
_STRIPE_ROWS = (3, 5, 7, 9, 11, 13)
_CLOSE_BOX_SIZE = 11
_CLOSE_BOX_LEFT = 8


def make_title_bar(parent, title: str, theme: dict,
                   on_close=None, drag_target=None) -> tk.Frame:
    """
    System 1.0 title bar with horizontal stripes, centered title, and a
    close box at the left. Dragging the bar moves `drag_target` — defaults
    to the toplevel containing `parent`, which is what you want for the
    borderless app window.
    """
    bar = tk.Frame(parent, bg=theme["title_bar_bg"], height=_TITLE_BAR_HEIGHT)
    bar.pack(fill="x", side="top")
    bar.pack_propagate(False)

    canvas = tk.Canvas(
        bar,
        height=_TITLE_BAR_HEIGHT,
        bg=theme["title_bar_bg"],
        highlightthickness=0,
        bd=0,
    )
    canvas.pack(fill="both", expand=True)

    fg = theme["title_bar_fg"]
    bg = theme["title_bar_bg"]

    def redraw(_event=None):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1:
            return
        h = _TITLE_BAR_HEIGHT

        for y in _STRIPE_ROWS:
            canvas.create_line(0, y, w, y, fill=fg, width=1)
        canvas.create_line(0, 0, w, 0, fill=fg, width=1)
        canvas.create_line(0, h - 1, w, h - 1, fill=fg, width=1)

        # erase stripes behind the (overlaid) close box widget
        canvas.create_rectangle(_CLOSE_BOX_LEFT - 4, 1,
                                _CLOSE_BOX_LEFT + _CLOSE_BOX_SIZE + 4, h - 1,
                                fill=bg, outline="")

        # centered title, with stripes erased behind it
        cx = w // 2
        ghost = canvas.create_text(cx, h // 2, text=title,
                                   fill=fg, font=theme["font_title"])
        bbox = canvas.bbox(ghost)
        canvas.delete(ghost)
        if bbox is not None:
            pad = 8
            canvas.create_rectangle(bbox[0] - pad, 1,
                                    bbox[2] + pad, h - 1,
                                    fill=bg, outline="")
        canvas.create_text(cx, h // 2, text=title,
                           fill=fg, font=theme["font_title"])

    canvas.bind("<Configure>", redraw)

    # close box: a real widget so its click takes priority over the
    # canvas-wide drag binding below
    if on_close:
        cb_y = (_TITLE_BAR_HEIGHT - _CLOSE_BOX_SIZE) // 2
        close_box = tk.Frame(
            bar,
            bg=bg,
            highlightbackground=fg,
            highlightcolor=fg,
            highlightthickness=1,
            width=_CLOSE_BOX_SIZE,
            height=_CLOSE_BOX_SIZE,
            cursor="hand2",
        )
        close_box.place(x=_CLOSE_BOX_LEFT, y=cb_y)

        def _press(_e):
            close_box.configure(bg=fg)

        def _release(_e):
            close_box.configure(bg=bg)
            x, y = _e.x, _e.y
            if 0 <= x <= _CLOSE_BOX_SIZE and 0 <= y <= _CLOSE_BOX_SIZE:
                on_close()

        close_box.bind("<ButtonPress-1>", _press)
        close_box.bind("<ButtonRelease-1>", _release)

    # drag the toplevel by clicking on the canvas (close box is on top
    # of the canvas so it'll capture its own clicks)
    if drag_target is None:
        try:
            drag_target = parent.winfo_toplevel()
        except Exception:
            drag_target = None
    if drag_target is not None:
        _bind_drag(canvas, drag_target)

    # 1px separator under the title bar
    tk.Frame(parent, bg=theme["separator_color"], height=1).pack(
        fill="x", side="top")

    return bar


def _bind_drag(widget, target):
    """Bind widget so click-drag moves `target` (a Toplevel-like window)."""
    state = {}

    def on_press(e):
        state["off_x"] = e.x_root - target.winfo_x()
        state["off_y"] = e.y_root - target.winfo_y()

    def on_motion(e):
        if "off_x" not in state:
            return
        x = e.x_root - state["off_x"]
        y = e.y_root - state["off_y"]
        target.geometry(f"+{x}+{y}")

    widget.bind("<ButtonPress-1>", on_press)
    widget.bind("<B1-Motion>", on_motion)


# ───────────────────────────────────────────────────────────── grow box

_GROW_BOX_SIZE = 15


def make_grow_box(parent, theme: dict, resize_target=None) -> tk.Frame:
    """
    Bottom-right resize handle — the System 1.0 diagonal-stripe grip.
    Call with `resize_target=app` (or any toplevel). The caller decides
    where to place it; typically `.place(relx=1.0, rely=1.0, anchor='se')`
    on the toplevel itself.

    Returns a Frame wrapping the inner Canvas. The Frame wrapper exists
    so callers can call `.tkraise()` on the result — `tk.Canvas` overrides
    both `lift` and `tkraise` (in Python 3.14+) to operate on canvas items
    rather than the widget itself, which would crash without a tag arg.
    """
    if resize_target is None:
        resize_target = parent.winfo_toplevel()

    frame = tk.Frame(parent, bg=theme["bg"])
    canvas = tk.Canvas(
        frame,
        width=_GROW_BOX_SIZE,
        height=_GROW_BOX_SIZE,
        bg=theme["bg"],
        highlightthickness=0,
        bd=0,
        cursor="bottom_right_corner",
    )
    canvas.pack()

    fg = theme["fg"]
    bg = theme["bg"]
    s = _GROW_BOX_SIZE

    # solid border on top + left edges, plus diagonal stripe pattern
    canvas.create_rectangle(0, 0, s - 1, s - 1, outline=fg, width=1, fill=bg)
    for off in (3, 6, 9):
        canvas.create_line(off, s - 2, s - 2, off, fill=fg, width=1)

    state = {}

    def on_press(e):
        state["start_x"] = e.x_root
        state["start_y"] = e.y_root
        state["start_w"] = resize_target.winfo_width()
        state["start_h"] = resize_target.winfo_height()

    def on_motion(e):
        if "start_x" not in state:
            return
        dx = e.x_root - state["start_x"]
        dy = e.y_root - state["start_y"]
        new_w = max(560, state["start_w"] + dx)
        new_h = max(380, state["start_h"] + dy)
        resize_target.geometry(f"{new_w}x{new_h}")

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_motion)

    return frame


# ───────────────────────────────────────────────────────────── info strip

def make_info_strip(parent, theme: dict, items) -> tk.Frame:
    """System 1.0 info band ('3 items   227K in disk   173K available')."""
    strip = tk.Frame(parent, bg=theme["bg"])
    strip.pack(fill="x", side="top")
    inner = tk.Frame(strip, bg=theme["bg"])
    inner.pack(fill="x", padx=8, pady=2)
    for text in items:
        tk.Label(inner, text=text, bg=theme["bg"], fg=theme["fg"],
                 font=theme["font_small"]).pack(side="left", padx=12)
    tk.Frame(parent, bg=theme["separator_color"], height=1).pack(
        fill="x", side="top")
    return strip


# ───────────────────────────────────────────────────────────── shadowed panel

def make_shadowed_panel(parent, theme: dict, **kwargs):
    """
    Returns (outer, inner). Pack `outer` into the parent layout; put
    children inside `inner`. The outer adds a 3px drop shadow on the
    right + bottom edges, the way classic Mac windows sit on the desktop.
    """
    SHADOW = 3
    outer = tk.Frame(parent, bg=theme["bg"])
    inner = tk.Frame(
        outer,
        bg=theme["bg"],
        relief=theme["panel_relief"],
        bd=theme["border_width"],
        **kwargs,
    )
    shadow_right = tk.Frame(outer, bg=theme["shadow_color"], width=SHADOW)
    shadow_bottom = tk.Frame(outer, bg=theme["shadow_color"], height=SHADOW)

    inner.grid(row=0, column=0, sticky="nsew")
    shadow_right.grid(row=0, column=1, sticky="ns")
    shadow_bottom.grid(row=1, column=0, columnspan=2, sticky="ew")
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(0, weight=1)

    return outer, inner


# ───────────────────────────────────────────────────────────── radio group

def make_radio_group(parent, theme: dict, variable, options,
                     command=None, btn_width: int = 6, pad: int = 4) -> tk.Frame:
    """
    System 1.0 radio group — a row of buttons where the selected one is
    rendered fully inverted (black bg, white fg). `options` is a list of
    (label, value) tuples; `variable` is any tk.Variable; `command` is
    called with the chosen value on every selection change.

    Built from Frame+Label rather than tk.Button because macOS overrides
    tk.Button's bg/fg with native rendering, hiding the inversion.

    The group traces the variable, so external mutations (e.g. from a
    menu dropdown) re-render the selection.
    """
    container = tk.Frame(parent, bg=theme["bg"])
    items = []

    def render():
        current = variable.get()
        for lbl, value in items:
            if value == current:
                lbl.configure(bg=theme["button_active_bg"],
                              fg=theme["button_active_fg"])
            else:
                lbl.configure(bg=theme["button_bg"],
                              fg=theme["button_fg"])

    def select(value):
        variable.set(value)
        if command:
            command(value)

    for label, value in options:
        border = tk.Frame(container, bg=theme["fg"])
        border.pack(side="left", padx=pad)
        lbl = tk.Label(
            border, text=label,
            bg=theme["button_bg"],
            fg=theme["button_fg"],
            font=theme["font_ui_bold"],
            width=btn_width,
            pady=3,
            cursor="hand2",
        )
        lbl.pack(padx=1, pady=1, fill="both", expand=True)
        lbl.bind("<Button-1>", lambda _e, v=value: select(v))
        items.append((lbl, value))

    variable.trace_add("write", lambda *_: render())
    render()
    return container


# ───────────────────────────────────────────────────────────── menubar + dropdowns

class DropdownMenu(tk.Frame):
    """A System 1.0-styled dropdown menu.

    Implemented as a Frame inside the main toplevel (positioned via
    `place()`), NOT as a separate Toplevel. On macOS, even an
    overrideredirect Toplevel disturbs the parent window's event
    dispatch enough that clicks on the parent stop firing after the
    dropdown closes. Keeping everything inside one window avoids that
    entirely.
    """

    def __init__(self, root, theme: dict):
        # Parent is the root toplevel so we can place ourselves
        # anywhere over the main app, including on top of other widgets.
        super().__init__(root, bg=theme["fg"])
        self.theme = theme
        self._inner = tk.Frame(self, bg=theme["bg"])
        self._inner.pack(padx=1, pady=1)
        self._on_dismiss = None
        self._visible = False

    def add_command(self, label: str, command=None, checked: bool = False):
        t = self.theme
        prefix = "✓ " if checked else "    "
        row = tk.Label(
            self._inner, text=f"{prefix}{label}",
            bg=t["bg"], fg=t["fg"],
            font=t["font_ui"],
            anchor="w", padx=14, pady=3,
        )
        row.pack(fill="x")

        def on_enter(_e):
            row.configure(bg=t["highlight_bg"], fg=t["highlight_fg"])

        def on_leave(_e):
            row.configure(bg=t["bg"], fg=t["fg"])

        def on_click(_e):
            if command:
                command()
            self.hide()

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        row.bind("<Button-1>", on_click)
        return row

    def add_separator(self):
        tk.Frame(self._inner, bg=self.theme["separator_color"],
                 height=1).pack(fill="x", padx=2, pady=2)

    def show_at(self, x: int, y: int):
        """Position at root-relative coordinates and raise above siblings."""
        # Convert root-relative coords to coords relative to our parent.
        top = self.master.winfo_toplevel()
        local_x = x - top.winfo_rootx()
        local_y = y - top.winfo_rooty()
        self.place(x=local_x, y=local_y)
        self.tkraise()
        self._visible = True

    def hide(self):
        self.place_forget()
        self._visible = False
        if self._on_dismiss:
            self._on_dismiss()

    def is_visible(self) -> bool:
        return self._visible


class Menubar(tk.Frame):
    """System 1.0-styled menubar — a row of click-to-open dropdowns.

    Each menu label opens a `DropdownMenu` Toplevel positioned beneath
    it. Click the same label again to close. Click outside any
    dropdown to dismiss. Both the menubar and dropdowns are
    overrideredirect, so OS keyboard focus stays with the main app
    window throughout.
    """

    def __init__(self, parent, theme: dict):
        super().__init__(parent, bg=theme["menubar_bg"])
        self.theme = theme
        self._items = []  # list of (label_widget, dropdown)
        self._open = None
        self._toplevel = self.winfo_toplevel()
        # Track the registered handler so we can unbind on destroy.
        self._bind_id = self._toplevel.bind(
            "<Button-1>", self._on_global_click, add="+")
        self.bind("<Destroy>", self._cleanup)

    def add(self, label: str) -> DropdownMenu:
        t = self.theme
        dropdown = DropdownMenu(self._toplevel, t)
        dropdown._on_dismiss = self._reset_labels

        lbl = tk.Label(
            self, text=label,
            bg=t["menubar_bg"], fg=t["fg"],
            font=t["font_ui"],
            padx=12, pady=2,
            cursor="hand2",
        )
        lbl.pack(side="left")

        def on_enter(_e):
            if self._open is not dropdown:
                lbl.configure(bg=t["highlight_bg"], fg=t["highlight_fg"])

        def on_leave(_e):
            if self._open is not dropdown:
                lbl.configure(bg=t["menubar_bg"], fg=t["fg"])

        def on_click(_e):
            self._toggle(dropdown, lbl)

        lbl.bind("<Enter>", on_enter)
        lbl.bind("<Leave>", on_leave)
        lbl.bind("<Button-1>", on_click)

        self._items.append((lbl, dropdown))
        return dropdown

    def _toggle(self, dropdown: DropdownMenu, lbl: tk.Label):
        if self._open is dropdown:
            dropdown.hide()
            return
        if self._open is not None:
            self._open.hide()
        x = lbl.winfo_rootx()
        y = lbl.winfo_rooty() + lbl.winfo_height()
        dropdown.show_at(x, y)
        self._open = dropdown
        # Invert this label to mark the active menu.
        lbl.configure(bg=self.theme["highlight_bg"],
                      fg=self.theme["highlight_fg"])

    def _reset_labels(self):
        t = self.theme
        for lbl, _ in self._items:
            lbl.configure(bg=t["menubar_bg"], fg=t["fg"])
        self._open = None

    def _on_global_click(self, event):
        # If this Menubar has been destroyed but the binding lingered,
        # just bail. (tkinter's unbind(seq, funcid) actually clears ALL
        # bindings for `seq`, so we leave the binding in place rather
        # than wipe out anything else attached to the toplevel.)
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        if self._open is None:
            return
        # Walk up the widget hierarchy from the click target. If we
        # pass through the open dropdown OR any of our menubar labels,
        # leave the dropdown alone — the relevant handler will manage.
        w = event.widget
        menubar_labels = {lbl for lbl, _ in self._items}
        while w is not None:
            if w is self._open or w is self._open._inner:
                return
            if w in menubar_labels:
                return
            try:
                w = w.master
            except Exception:
                w = None
        self._open.hide()

    def _cleanup(self, _e=None):
        # Don't unbind: tkinter's `unbind(seq, funcid)` is broken — it
        # clears every handler for `seq`, not just ours. We instead
        # leave the binding alive; the handler short-circuits via
        # winfo_exists once we're destroyed.
        for _, dropdown in self._items:
            try:
                dropdown.destroy()
            except Exception:
                pass
        self._items.clear()


# ───────────────────────────────────────────────────────────── basics

def make_button(parent, text: str, theme: dict, command=None, width=12) -> tk.Button:
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=theme["button_bg"],
        fg=theme["button_fg"],
        activebackground=theme["button_active_bg"],
        activeforeground=theme["button_active_fg"],
        relief=theme["border_relief_raised"],
        bd=theme["border_width"],
        font=theme["font_ui_bold"],
        width=width,
        cursor="hand2",
        padx=4, pady=3,
        highlightthickness=0,
    )


def make_panel(parent, theme: dict, **kwargs) -> tk.Frame:
    return tk.Frame(
        parent,
        bg=theme["bg"],
        relief=theme["panel_relief"],
        bd=theme["border_width"],
        **kwargs,
    )


def make_sunken_frame(parent, theme: dict, **kwargs) -> tk.Frame:
    return tk.Frame(
        parent,
        bg=theme["input_bg"],
        relief=theme["frame_relief"],
        bd=theme["border_width"],
        **kwargs,
    )


def make_label(parent, text: str, theme: dict, font_key="font_ui", **kwargs) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        bg=theme["bg"],
        fg=theme["fg"],
        font=theme[font_key],
        **kwargs,
    )


def make_separator(parent, theme: dict) -> tk.Frame:
    sep = tk.Frame(parent, bg=theme["separator_color"], height=1)
    sep.pack(fill="x", padx=0, pady=0)
    return sep


def apply_theme_to_window(window, theme: dict):
    window.configure(bg=theme["bg"])
