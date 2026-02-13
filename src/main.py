import tkinter as tk
import threading
import sys
import os

# Add src to path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.translator_service import TranslatorService
from src.selection_monitor import SelectionMonitor
from src.main_window import MainWindow

class DynamicTranslatorApp:
    def __init__(self):
        self.root = tk.Tk()
        # self.root.withdraw() # We want it visible now
        
        self.translator = TranslatorService()
        self.monitor = SelectionMonitor(None) # Callback connected in MainWindow
        
        self.main_window = MainWindow(self.root, self.translator, self.monitor)

    def start(self):
        self.monitor.start()
        self.root.mainloop()

    def on_quit(self):
        self.monitor.stop()
        self.root.quit()
        sys.exit()

if __name__ == "__main__":
    app = DynamicTranslatorApp()
    try:
        app.start()
    except KeyboardInterrupt:
        app.on_quit()
