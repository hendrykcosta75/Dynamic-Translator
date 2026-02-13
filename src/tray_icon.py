import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw

class TrayIcon:
    def __init__(self, on_quit_callback):
        self.on_quit_callback = on_quit_callback
        self.icon = None
        self.thread = None

    def create_image(self):
        # Generate a simple icon
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(50, 50, 50))
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
            fill=(200, 200, 200)
        )
        return image

    def run(self):
        self.thread = threading.Thread(target=self._run_icon)
        self.thread.daemon = True
        self.thread.start()

    def _run_icon(self):
        menu = Menu(
            MenuItem('Quit', self.on_quit)
        )
        self.icon = Icon("DynamicTranslator", self.create_image(), "Dynamic Translator", menu)
        self.icon.run()

    def on_quit(self, icon, item):
        icon.stop()
        if self.on_quit_callback:
            self.on_quit_callback()
