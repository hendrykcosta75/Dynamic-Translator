import tkinter as tk

# ─── Color Palette ───────────────────────────────────────────────────────────
COLORS = {
    'bg':       '#1a1a2e',
    'accent':   '#818cf8',
    'text':     '#e2e8f0',
    'text_muted': '#475569',
    'border':   '#2a2a45',
}

FONT = 'Segoe UI'


class PopupWindow:
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.96)

        # Outer frame acts as accent border (thicker on top)
        self.outer = tk.Frame(self.window, bg=COLORS['accent'])
        self.outer.pack(fill='both', expand=True)

        # Inner frame – dark content area
        # padx=1 = thin side borders, pady=(3,1) = 3px accent top bar
        self.inner = tk.Frame(self.outer, bg=COLORS['bg'])
        self.inner.pack(fill='both', expand=True, padx=1, pady=(3, 1))

        # Text label
        self.label = tk.Label(
            self.inner,
            text="",
            bg=COLORS['bg'],
            fg=COLORS['text'],
            font=(FONT, 11),
            wraplength=380,
            justify='left',
            padx=14,
            pady=12,
        )
        self.label.pack(fill='both', expand=True)

        # Resize grip (subtle)
        self.grip = tk.Label(
            self.inner, text="\u2022\u2022", bg=COLORS['bg'],
            fg=COLORS['border'], cursor='sizing', font=(FONT, 7))
        self.grip.place(relx=1.0, rely=1.0, anchor='se', x=-4, y=-2)

        self.grip.bind("<ButtonPress-1>", self._start_resize)
        self.grip.bind("<B1-Motion>", self._do_resize)

        # Drag to move
        for w in (self.label, self.inner):
            w.bind("<Button-1>", self._start_move)
            w.bind("<B1-Motion>", self._do_move)

        # Right-click to close
        for w in (self.label, self.inner):
            w.bind("<Button-3>", lambda _: self.hide())

        self._mx = 0
        self._my = 0

    # ── Move ────────────────────────────────────────────────────────────────

    def _start_move(self, event):
        self._mx = event.x
        self._my = event.y

    def _do_move(self, event):
        dx = event.x - self._mx
        dy = event.y - self._my
        x = self.window.winfo_x() + dx
        y = self.window.winfo_y() + dy
        self.window.geometry(f"+{x}+{y}")

    # ── Resize ──────────────────────────────────────────────────────────────

    def _start_resize(self, event):
        self._mx = event.x
        self._my = event.y

    def _do_resize(self, event):
        w = self.window.winfo_width() + (event.x - self._mx)
        h = self.window.winfo_height() + (event.y - self._my)
        w = max(w, 120)
        h = max(h, 50)
        self.label.config(wraplength=w - 40)
        self.window.geometry(f"{int(w)}x{int(h)}")

    # ── Show / Hide ─────────────────────────────────────────────────────────

    def show(self, text, x, y):
        self.label.config(text=text, wraplength=380)
        self.window.update_idletasks()

        w = min(self.label.winfo_reqwidth() + 30, 420)
        h = self.label.winfo_reqheight() + 28

        # Offset from cursor
        x += 20
        y += 20

        # Keep on screen
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        if x + w > sw:
            x = sw - w - 10
        if y + h > sh:
            y = y - h - 40

        self.window.geometry(f"{int(w)}x{int(h)}+{int(x)}+{int(y)}")
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()
