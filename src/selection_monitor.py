import time
import threading
import pyperclip
from pynput import mouse, keyboard
import logging

class SelectionMonitor:
    def __init__(self, on_selection_callback):
        """
        :param on_selection_callback: Function to call when text is selected. 
                                      Receives the selected text as argument.
        """
        self.on_selection_callback = on_selection_callback
        self.logger = logging.getLogger(__name__)
        self.keyboard_controller = keyboard.Controller()
        self.is_monitoring = True
        
        # State to track drag
        self.mouse_pressed = False
        self.start_pos = None

        self.last_clipboard_content = ""

    def start(self):
        self.listener = mouse.Listener(
            on_click=self.on_click
        )
        self.listener.start()
        self.logger.info("Selection monitor started.")

    def stop(self):
        self.is_monitoring = False
        if hasattr(self, 'listener'):
            self.listener.stop()

    def on_click(self, x, y, button, pressed):
        if not self.is_monitoring:
            return

        if button == mouse.Button.left:
            if pressed:
                self.mouse_pressed = True
                self.start_pos = (x, y)
            else:
                if self.mouse_pressed:
                    self.mouse_pressed = False
                    # Check if it was a drag (moved significantly)
                    # Or just a click. If it's a drag, we assume selection.
                    # We can also just try to copy on every release if it might be a selection.
                    # To avoid spamming Ctrl+C on every click, we can check distance.
                    # However, double-click selects words too.
                    
                    # Let's try to copy after a small delay to let the OS process the selection
                    # running in a separate thread to not block the mouse listener
                    threading.Thread(target=self.process_selection).start()

    def process_selection(self):
        # Allow time for the release event to complete standard OS processing
        time.sleep(0.1) 
        
        # Save current clipboard to restore it later if needed (optional, 
        # but user might be annoyed if we nuke their clipboard. 
        # For this v1, we overwrite it as stated in the plan).
        
        try:
            old_clipboard = pyperclip.paste()
        except:
            old_clipboard = ""

        # Simulate Ctrl+C
        with self.keyboard_controller.pressed(keyboard.Key.ctrl):
            self.keyboard_controller.tap('c')
        
        # Wait for clipboard to update
        time.sleep(0.1)

        try:
            new_clipboard = pyperclip.paste()
        except:
            new_clipboard = ""

        if new_clipboard and new_clipboard != old_clipboard and new_clipboard.strip():
            # Something new was copied
            self.logger.info(f"Detected selection: {new_clipboard[:20]}...")
            if self.on_selection_callback:
                self.on_selection_callback(new_clipboard)
        
        # If we wanted to be polite, we could restore the old clipboard if nothing changed,
        # but if we successfully copied new text, the user likely wanted that.
        
