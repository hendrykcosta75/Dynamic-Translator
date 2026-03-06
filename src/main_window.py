import tkinter as tk
from tkinter import messagebox
import threading
import queue
import os

# ─── Color Palette ───────────────────────────────────────────────────────────
COLORS = {
    'bg':             '#0f0f1a',
    'surface':        '#1a1a2e',
    'card':           '#232340',
    'accent':         '#818cf8',
    'accent_hover':   '#6366f1',
    'accent_dim':     '#4f46e5',
    'text':           '#e2e8f0',
    'text_secondary': '#94a3b8',
    'text_muted':     '#475569',
    'border':         '#2a2a45',
    'success':        '#34d399',
    'error':          '#f87171',
    'input_bg':       '#12122a',
    'input_border':   '#333355',
    'hover':          '#1f1f3a',
}

FONT = 'Segoe UI'


# ─── Custom Widgets ──────────────────────────────────────────────────────────

class ToggleSwitch(tk.Canvas):
    """Modern pill-shaped toggle switch."""

    def __init__(self, parent, variable=None, command=None,
                 width=44, height=24, canvas_bg=None, **kwargs):
        bg = canvas_bg or COLORS['bg']
        super().__init__(parent, width=width, height=height,
                         bg=bg, highlightthickness=0, bd=0, **kwargs)
        self.w = width
        self.h = height
        self.variable = variable or tk.BooleanVar(value=False)
        self.command = command
        self.r = height // 2
        self.kr = self.r - 3

        self.bind('<Button-1>', self._toggle)
        self.variable.trace_add('write', lambda *_: self._draw())
        self._draw()

    def _toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def _draw(self):
        self.delete('all')
        on = self.variable.get()
        track = COLORS['accent'] if on else COLORS['text_muted']
        r = self.r

        # Rounded track
        self.create_oval(0, 0, r * 2, r * 2, fill=track, outline='')
        self.create_oval(self.w - r * 2, 0, self.w, r * 2, fill=track, outline='')
        self.create_rectangle(r, 0, self.w - r, r * 2, fill=track, outline='')

        # Knob
        cx = (self.w - r) if on else r
        cy = r
        kr = self.kr
        self.create_oval(cx - kr, cy - kr, cx + kr, cy + kr,
                         fill='#ffffff', outline='')


class NavButton(tk.Frame):
    """Sidebar navigation button with active indicator."""

    def __init__(self, parent, text, command=None, **kwargs):
        super().__init__(parent, bg=COLORS['bg'], cursor='hand2', **kwargs)
        self.command = command
        self.is_active = False
        self._bg = COLORS['bg']

        # Left accent bar
        self.bar = tk.Frame(self, width=3, bg=COLORS['bg'])
        self.bar.pack(side='left', fill='y')

        # Content
        self.content = tk.Frame(self, bg=self._bg)
        self.content.pack(side='left', fill='both', expand=True, padx=(10, 14), pady=10)

        self.label = tk.Label(self.content, text=text, font=(FONT, 10),
                              bg=self._bg, fg=COLORS['text_secondary'])
        self.label.pack(side='left')

        for w in (self, self.content, self.label):
            w.bind('<Button-1>', lambda _: self._click())
            w.bind('<Enter>', lambda _: self._enter())
            w.bind('<Leave>', lambda _: self._leave())

    def _click(self):
        if self.command:
            self.command()

    def _enter(self):
        if not self.is_active:
            self._apply_bg(COLORS['hover'])

    def _leave(self):
        if not self.is_active:
            self._apply_bg(COLORS['bg'])

    def set_active(self, active):
        self.is_active = active
        if active:
            self._apply_bg(COLORS['surface'])
            self.bar.configure(bg=COLORS['accent'])
            self.label.configure(fg=COLORS['text'])
        else:
            self._apply_bg(COLORS['bg'])
            self.bar.configure(bg=COLORS['bg'])
            self.label.configure(fg=COLORS['text_secondary'])

    def _apply_bg(self, color):
        self._bg = color
        for w in (self, self.content, self.label):
            w.configure(bg=color)


# ─── Main Window ─────────────────────────────────────────────────────────────

class MainWindow:
    def __init__(self, root, translator_service, selection_monitor):
        self.root = root
        self.translator = translator_service
        self.monitor = selection_monitor

        self.root.title("Dynamic Translator")
        self.root.geometry("720x480")
        self.root.minsize(620, 400)
        self.root.configure(bg=COLORS['bg'])
        self.root.attributes('-topmost', True)

        # Dark title-bar (Windows 10/11)
        self.root.update_idletasks()
        self._apply_dark_titlebar()

        # ── Layout ──
        main = tk.Frame(root, bg=COLORS['bg'])
        main.pack(fill='both', expand=True)

        # Sidebar
        self.sidebar = tk.Frame(main, bg=COLORS['bg'], width=170)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Vertical separator
        tk.Frame(main, bg=COLORS['border'], width=1).pack(side='left', fill='y')

        # Content
        self.content = tk.Frame(main, bg=COLORS['bg'])
        self.content.pack(side='left', fill='both', expand=True)

        self._build_sidebar()
        self._build_pages()

        # Thread-safe queue
        self.update_queue = queue.Queue()
        self._poll_queue()

        # Connect monitor callback
        self.monitor.on_selection_callback = self.on_selection
        self.current_translation_thread = None
        self.stop_event = threading.Event()

        # Default page
        self._show_page('translation')

    # ── Dark title bar ──────────────────────────────────────────────────────

    def _apply_dark_titlebar(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20,
                ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
        except Exception:
            pass

    # ── Sidebar ─────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        # App name
        hdr = tk.Frame(self.sidebar, bg=COLORS['bg'])
        hdr.pack(fill='x', padx=18, pady=(22, 28))
        tk.Label(hdr, text="Dynamic", font=(FONT, 15, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(anchor='w')
        tk.Label(hdr, text="Translator", font=(FONT, 15),
                 bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor='w')

        # Nav buttons
        self.nav = {}
        self.nav['translation'] = NavButton(
            self.sidebar, "Traducao",
            command=lambda: self._show_page('translation'))
        self.nav['translation'].pack(fill='x')

        self.nav['settings'] = NavButton(
            self.sidebar, "Configuracoes",
            command=lambda: self._show_page('settings'))
        self.nav['settings'].pack(fill='x')

        # Spacer
        tk.Frame(self.sidebar, bg=COLORS['bg']).pack(fill='both', expand=True)

        # Monitoring toggle
        sep = tk.Frame(self.sidebar, bg=COLORS['border'], height=1)
        sep.pack(fill='x', padx=18)

        tog_frame = tk.Frame(self.sidebar, bg=COLORS['bg'])
        tog_frame.pack(fill='x', padx=18, pady=14)

        self.monitoring_var = tk.BooleanVar(value=True)

        row = tk.Frame(tog_frame, bg=COLORS['bg'])
        row.pack(fill='x')

        self.status_dot = tk.Label(row, text="*", font=(FONT, 10),
                                   bg=COLORS['bg'], fg=COLORS['success'])
        self.status_dot.pack(side='left', padx=(0, 5))

        self.status_label = tk.Label(row, text="Ativo", font=(FONT, 9),
                                     bg=COLORS['bg'], fg=COLORS['text_secondary'])
        self.status_label.pack(side='left')

        self.toggle = ToggleSwitch(row, variable=self.monitoring_var,
                                   command=self._toggle_monitoring)
        self.toggle.pack(side='right')

    # ── Pages ───────────────────────────────────────────────────────────────

    def _build_pages(self):
        self.pages = {}

        self.pages['translation'] = tk.Frame(self.content, bg=COLORS['bg'])
        self._build_translation_page(self.pages['translation'])

        self.pages['settings'] = tk.Frame(self.content, bg=COLORS['bg'])
        self._build_settings_page(self.pages['settings'])

    def _show_page(self, name):
        for p in self.pages.values():
            p.pack_forget()
        for key, btn in self.nav.items():
            btn.set_active(key == name)
        self.pages[name].pack(fill='both', expand=True)

    # ── Translation Page ────────────────────────────────────────────────────

    def _build_translation_page(self, parent):
        # Header
        hdr = tk.Frame(parent, bg=COLORS['bg'])
        hdr.pack(fill='x', padx=24, pady=(22, 0))

        tk.Label(hdr, text="Traducao", font=(FONT, 18, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(side='left')

        self.translation_status = tk.Label(
            hdr, text="Aguardando selecao...", font=(FONT, 9),
            bg=COLORS['bg'], fg=COLORS['text_muted'])
        self.translation_status.pack(side='right')

        # Card container
        card = tk.Frame(parent, bg=COLORS['surface'],
                        highlightbackground=COLORS['border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=24, pady=16)

        self.text_area = tk.Text(
            card, wrap=tk.WORD, font=(FONT, 12),
            bg=COLORS['surface'], fg=COLORS['text'],
            insertbackground=COLORS['text'],
            selectbackground=COLORS['accent_dim'],
            selectforeground=COLORS['text'],
            relief='flat', padx=16, pady=16, borderwidth=0,
        )
        self.text_area.pack(fill='both', expand=True)
        self.text_area.insert('1.0', "Selecione qualquer texto para traduzir...")

        # Mousewheel scrolling
        self.text_area.bind('<MouseWheel>',
            lambda e: self.text_area.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # ── Settings Page ───────────────────────────────────────────────────────

    def _build_settings_page(self, parent):
        hdr = tk.Frame(parent, bg=COLORS['bg'])
        hdr.pack(fill='x', padx=24, pady=(22, 8))
        tk.Label(hdr, text="Configuracoes", font=(FONT, 18, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(side='left')

        wrap = tk.Frame(parent, bg=COLORS['bg'])
        wrap.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        # ── Provider ──
        self._section_label(wrap, "PROVEDOR DE TRADUCAO")
        prov_card = self._card(wrap)

        self.provider_var = tk.StringVar(value=self.translator.provider)
        self._radio_row(prov_card, "OpenAI", "openai", self.provider_var,
                        "Traducao com IA (recomendado)")
        tk.Frame(prov_card, bg=COLORS['border'], height=1).pack(fill='x', padx=14)
        self._radio_row(prov_card, "Google Translate", "google", self.provider_var,
                        "Gratuito, sem necessidade de API key")

        # ── API Key ──
        self._section_label(wrap, "OPENAI API KEY")
        key_card = self._card(wrap)
        key_inner = tk.Frame(key_card, bg=COLORS['card'])
        key_inner.pack(fill='x', padx=14, pady=12)

        self.api_key_var = tk.StringVar(value=self.translator.api_key or "")
        self._styled_entry(key_inner, self.api_key_var, show="*")

        # ── Model ──
        self._section_label(wrap, "MODELO")
        mod_card = self._card(wrap)
        mod_inner = tk.Frame(mod_card, bg=COLORS['card'])
        mod_inner.pack(fill='x', padx=14, pady=12)

        self.model_var = tk.StringVar(value=self.translator.model)
        self._styled_entry(mod_inner, self.model_var)
        tk.Label(mod_inner, text="Ex: gpt-4o, gpt-4o-mini, gpt-3.5-turbo",
                 font=(FONT, 8), bg=COLORS['card'],
                 fg=COLORS['text_muted']).pack(anchor='w', pady=(4, 0))

        # ── Save Button ──
        btn = tk.Label(wrap, text="  Salvar  ", font=(FONT, 10, 'bold'),
                       bg=COLORS['accent'], fg='#ffffff', cursor='hand2',
                       padx=20, pady=8)
        btn.pack(anchor='w', pady=(16, 0))
        btn.bind('<Button-1>', lambda _: self._save_settings())
        btn.bind('<Enter>', lambda _: btn.configure(bg=COLORS['accent_hover']))
        btn.bind('<Leave>', lambda _: btn.configure(bg=COLORS['accent']))

    # ── Settings helpers ────────────────────────────────────────────────────

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=(FONT, 9, 'bold'),
                 bg=COLORS['bg'], fg=COLORS['text_secondary']
                 ).pack(anchor='w', pady=(14, 6))

    def _card(self, parent):
        c = tk.Frame(parent, bg=COLORS['card'],
                     highlightbackground=COLORS['border'], highlightthickness=1)
        c.pack(fill='x')
        return c

    def _styled_entry(self, parent, variable, show=""):
        e = tk.Entry(parent, textvariable=variable, font=(FONT, 10),
                     bg=COLORS['input_bg'], fg=COLORS['text'],
                     insertbackground=COLORS['text'], relief='flat',
                     highlightthickness=1,
                     highlightbackground=COLORS['input_border'],
                     highlightcolor=COLORS['accent'],
                     show=show)
        e.pack(fill='x', ipady=8)
        return e

    def _radio_row(self, parent, text, value, variable, description=""):
        bg = COLORS['card']
        frame = tk.Frame(parent, bg=bg, cursor='hand2')
        frame.pack(fill='x', padx=14, pady=10)

        canvas = tk.Canvas(frame, width=18, height=18, bg=bg,
                           highlightthickness=0, bd=0)
        canvas.pack(side='left', padx=(0, 10), pady=2)

        txt_frame = tk.Frame(frame, bg=bg)
        txt_frame.pack(side='left', fill='x')

        lbl = tk.Label(txt_frame, text=text, font=(FONT, 10),
                       bg=bg, fg=COLORS['text'])
        lbl.pack(anchor='w')

        desc_lbl = None
        if description:
            desc_lbl = tk.Label(txt_frame, text=description, font=(FONT, 8),
                                bg=bg, fg=COLORS['text_muted'])
            desc_lbl.pack(anchor='w')

        def draw():
            canvas.delete('all')
            sel = variable.get() == value
            outline = COLORS['accent'] if sel else COLORS['text_muted']
            canvas.create_oval(1, 1, 17, 17, outline=outline, width=2)
            if sel:
                canvas.create_oval(5, 5, 13, 13, fill=COLORS['accent'], outline='')

        draw()
        variable.trace_add('write', lambda *_: draw())

        def click(_=None):
            variable.set(value)

        for w in [frame, canvas, txt_frame, lbl] + ([desc_lbl] if desc_lbl else []):
            w.bind('<Button-1>', click)

    # ── Save / Env ──────────────────────────────────────────────────────────

    def _save_settings(self):
        key = self.api_key_var.get().strip()
        provider = self.provider_var.get()
        model = self.model_var.get().strip()

        self.translator.api_key = key
        self.translator.provider = provider
        self.translator.model = model

        # Reinit OpenAI client if needed
        if provider == "openai" and key:
            try:
                from openai import OpenAI
                self.translator.openai_client = OpenAI(api_key=key)
            except Exception:
                pass

        self._write_env(key, provider, model)
        self._toast("Configuracoes salvas!")

    def _write_env(self, key, provider, model):
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()

        lines = [l for l in lines
                 if not l.startswith("OPENAI_API_KEY=")
                 and not l.startswith("TRANSLATOR_PROVIDER=")
                 and not l.startswith("OPENAI_MODEL=")]

        lines.append(f"OPENAI_API_KEY={key}\n")
        lines.append(f"TRANSLATOR_PROVIDER={provider}\n")
        lines.append(f"OPENAI_MODEL={model}\n")

        with open(env_path, 'w') as f:
            f.writelines(lines)

    def _toast(self, message):
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        t.attributes('-topmost', True)

        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 100
        y = self.root.winfo_y() + self.root.winfo_height() - 60
        t.geometry(f"+{x}+{y}")

        f = tk.Frame(t, bg=COLORS['success'])
        f.pack()
        tk.Label(f, text=f"  {message}  ", font=(FONT, 10),
                 bg=COLORS['success'], fg='#ffffff', pady=8, padx=8).pack()

        t.after(2000, t.destroy)

    # ── Monitoring ──────────────────────────────────────────────────────────

    def _toggle_monitoring(self):
        on = self.monitoring_var.get()
        self.monitor.is_monitoring = on
        if on:
            self.status_dot.configure(fg=COLORS['success'])
            self.status_label.configure(text="Ativo")
        else:
            self.status_dot.configure(fg=COLORS['text_muted'])
            self.status_label.configure(text="Pausado")

    # ── Translation pipeline ────────────────────────────────────────────────

    def on_selection(self, text):
        if not self.monitoring_var.get():
            return

        self.stop_event.set()
        if self.current_translation_thread and self.current_translation_thread.is_alive():
            self.current_translation_thread.join(timeout=0.1)
        self.stop_event.clear()

        self.update_queue.put(("CLEAR", ""))
        self.update_queue.put(("STATUS", "Traduzindo..."))

        self.current_translation_thread = threading.Thread(
            target=self._run_translation,
            args=(text, self.provider_var.get(), self.model_var.get()))
        self.current_translation_thread.start()

    def _run_translation(self, text, provider, model):
        try:
            for chunk in self.translator.translate_stream(text, provider, model):
                if self.stop_event.is_set():
                    break
                self.update_queue.put(("APPEND", chunk))
            self.update_queue.put(("STATUS", "Concluido"))
        except Exception as e:
            self.update_queue.put(("APPEND", f"\n[Error: {e}]"))
            self.update_queue.put(("STATUS", "Erro"))

    def _poll_queue(self):
        try:
            while True:
                action, data = self.update_queue.get_nowait()
                if action == "CLEAR":
                    self.text_area.delete('1.0', tk.END)
                elif action == "APPEND":
                    self.text_area.insert(tk.END, data)
                    self.text_area.see(tk.END)
                elif action == "STATUS":
                    self.translation_status.configure(text=data)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll_queue)
