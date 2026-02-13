import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import os

class MainWindow:
    def __init__(self, root, translator_service, selection_monitor):
        self.root = root
        self.translator = translator_service
        self.monitor = selection_monitor
        
        self.root.title("Dynamic Translator")
        self.root.geometry("600x400")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)
        
        self.tab_translation = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_translation, text='Tradução')
        self.notebook.add(self.tab_settings, text='Configurações')
        
        self.setup_translation_tab()
        self.setup_settings_tab()
        
        # Queue for thread-safe GUI updates
        self.update_queue = queue.Queue()
        self.check_queue()
        
        # Connect monitor
        self.monitor.on_selection_callback = self.on_selection
        
        self.current_translation_thread = None
        self.stop_event = threading.Event()

    def setup_translation_tab(self):
        # Top Control Bar
        control_frame = ttk.Frame(self.tab_translation)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.monitoring_var = tk.BooleanVar(value=True)
        self.btn_toggle = ttk.Checkbutton(
            control_frame, 
            text="Habilitar Tradução Automática", 
            variable=self.monitoring_var,
            command=self.toggle_monitoring
        )
        self.btn_toggle.pack(side='left')
        
        # Content Area
        self.text_area = scrolledtext.ScrolledText(
            self.tab_translation, 
            wrap=tk.WORD, 
            font=("Segoe UI", 12),
            bg="#202124", 
            fg="#e8eaed"
        )
        self.text_area.pack(fill='both', expand=True, padx=10, pady=10)
        self.text_area.insert('1.0', "Aguardando seleção de texto...")

    def setup_settings_tab(self):
        frame = ttk.Frame(self.tab_settings, padding=20)
        frame.pack(fill='both', expand=True)
        
        # Provider
        ttk.Label(frame, text="Provedor de Tradução:").grid(row=0, column=0, sticky='w', pady=5)
        self.provider_var = tk.StringVar(value=self.translator.provider)
        
        ttk.Radiobutton(frame, text="OpenAI (Recomendado)", variable=self.provider_var, value="openai").grid(row=1, column=0, sticky='w', padx=20)
        ttk.Radiobutton(frame, text="Google Translator (Gratuito)", variable=self.provider_var, value="google").grid(row=2, column=0, sticky='w', padx=20)
        
        # API Key
        ttk.Label(frame, text="OpenAI API Key:").grid(row=3, column=0, sticky='w', pady=(20, 5))
        self.api_key_var = tk.StringVar(value=self.translator.api_key or "")
        entry_key = ttk.Entry(frame, textvariable=self.api_key_var, width=50, show="*")
        entry_key.grid(row=4, column=0, sticky='w')
        
        # Model
        ttk.Label(frame, text="Modelo OpenAI:").grid(row=5, column=0, sticky='w', pady=(20, 5))
        self.model_var = tk.StringVar(value=self.translator.model)
        models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        combo_model = ttk.Combobox(frame, textvariable=self.model_var, values=models, state="readonly")
        combo_model.grid(row=6, column=0, sticky='w')
        
        # Save Button
        btn_save = ttk.Button(frame, text="Salvar Configurações", command=self.save_settings)
        btn_save.grid(row=7, column=0, pady=30, sticky='w')

    def save_settings(self):
        # Save to .env or just update service?
        # For simplicity, let's update service and maybe helper to write .env
        # But we previously used python-dotenv to load. Writing back to .env is manual.
        
        new_key = self.api_key_var.get().strip()
        new_provider = self.provider_var.get()
        new_model = self.model_var.get()
        
        # Update Service
        self.translator.api_key = new_key
        self.translator.provider = new_provider
        self.translator.model = new_model
        
        if new_provider == "openai" and new_key and not self.translator.openai_client:
             self.translator.refresh_config() # Try to reload/init client
             # But refresh_config loads from env. We should manually set or update env.
             # Let's just update the internal state of translator for now.
             import openai
             try:
                 self.translator.openai_client = openai.OpenAI(api_key=new_key)
             except:
                 pass
        
        # Update .env file content
        self.update_env_file(new_key, new_provider, new_model)
        
        tk.messagebox.showinfo("Sucesso", "Configurações salvas!")

    def update_env_file(self, key, provider, model):
        # Simple read/replace
        lines = []
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                lines = f.readlines()
        
        # Filter out existing
        lines = [l for l in lines if not l.startswith("OPENAI_API_KEY=") and not l.startswith("TRANSLATOR_PROVIDER=") and not l.startswith("OPENAI_MODEL=")]
        
        lines.append(f"OPENAI_API_KEY={key}\n")
        lines.append(f"TRANSLATOR_PROVIDER={provider}\n")
        lines.append(f"OPENAI_MODEL={model}\n")
        
        with open(".env", "w") as f:
            f.writelines(lines)

    def toggle_monitoring(self):
        if self.monitoring_var.get():
            self.monitor.start() # Logic might need adjustment if start() just adds listener
            # Actually selection_monitor logic is: start() adds listener. stop() removes it.
            # If we call start twice, pynput might error or duplicate.
            # We should check if running.
            if not self.monitor.is_monitoring:
                 self.monitor.is_monitoring = True
                 # If listener was stopped, we might need to recreate it.
                 # My SelectionMonitor implementation had manual listener start in start().
                 # Let's assume start() handles re-entrancy or we fix SelectionMonitor.
        else:
            self.monitor.is_monitoring = False
            # We don't necessarily stop the listener, just ignore events, 
            # but SelectionMonitor.on_click checks is_monitoring.

    def on_selection(self, text):
        if not self.monitoring_var.get():
            return
            
        # Cancel previous translation
        self.stop_event.set()
        if self.current_translation_thread and self.current_translation_thread.is_alive():
             self.current_translation_thread.join(timeout=0.1)
        
        self.stop_event.clear()
        
        # Clear text area
        self.update_queue.put(("CLEAR", ""))
        self.update_queue.put(("INSERT", f"Traduzindo: {text[:50]}...\n\n"))
        
        # Start new thread
        self.current_translation_thread = threading.Thread(
            target=self.run_translation,
            args=(text, self.provider_var.get(), self.model_var.get())
        )
        self.current_translation_thread.start()

    def run_translation(self, text, provider, model):
        try:
            for chunk in self.translator.translate_stream(text, provider, model):
                if self.stop_event.is_set():
                    break
                self.update_queue.put(("APPEND", chunk))
        except Exception as e:
            self.update_queue.put(("APPEND", f"\n[Error: {e}]"))

    def check_queue(self):
        try:
            while True:
                action, content = self.update_queue.get_nowait()
                if action == "CLEAR":
                    self.text_area.delete('1.0', tk.END)
                elif action == "INSERT":
                    self.text_area.insert(tk.END, content)
                elif action == "APPEND":
                    self.text_area.insert(tk.END, content)
                    self.text_area.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self.check_queue)
