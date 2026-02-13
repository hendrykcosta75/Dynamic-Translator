import tkinter as tk
from tkinter import ttk

class PopupWindow:
    def __init__(self, root):
        self.root = root
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.95)

        # Style Configuration
        self.bg_color = "#202124"  # Google Translate Dark Gray
        self.fg_color = "#e8eaed"  # Light Text
        self.border_color = "#5f6368"
        
        # Main Frame with border
        self.frame = tk.Frame(
            self.window, 
            bg=self.bg_color, 
            highlightbackground=self.border_color, 
            highlightthickness=1
        )
        self.frame.pack(fill="both", expand=True)

        # Content Frame
        self.content_frame = tk.Frame(self.frame, bg=self.bg_color)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.label = tk.Label(
            self.content_frame, 
            text="", 
            bg=self.bg_color, 
            fg=self.fg_color, 
            font=("Segoe UI", 11), 
            wraplength=350, 
            justify="left"
        )
        self.label.pack(fill="both", expand=True)

        # Resize Grip (Bottom Right)
        self.grip = tk.Label(self.frame, text="◢", bg=self.bg_color, fg=self.border_color, cursor="sizing")
        self.grip.place(relx=1.0, rely=1.0, anchor="se")
        
        self.grip.bind("<ButtonPress-1>", self.start_resize)
        self.grip.bind("<B1-Motion>", self.do_resize)

        # Move Window (Drag from body)
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)
        self.frame.bind("<Button-1>", self.start_move)
        self.frame.bind("<B1-Motion>", self.do_move)

        # Close on right click
        self.label.bind("<Button-3>", lambda e: self.hide())
        self.frame.bind("<Button-3>", lambda e: self.hide())

        self.x = 0
        self.y = 0
        self.start_w = 0
        self.start_h = 0

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def start_resize(self, event):
        self.x = event.x
        self.y = event.y
        self.start_w = self.window.winfo_width()
        self.start_h = self.window.winfo_height()

    def do_resize(self, event):
        # Calculate new size
        # event.x is relative to the grip widget, so it's a bit tricky.
        # easier to use screen coordinates or just delta.
        # Let's use root coordinates.
        
        # Actually, since it's B1-Motion on the grip, event.x is pos relative to click start? No.
        # It's relative to the widget.
        
        # Let's simple way: 
        # Update width/height based on mouse movement.
        # But wait, we need global mouse pos to be accurate?
        # Simpler:
        w = self.window.winfo_width() + (event.x - self.grip.winfo_width()/2) # slight offset correction attempt
        h = self.window.winfo_height() + (event.y - self.grip.winfo_height()/2)
        
        # Minimum size
        if w < 100: w = 100
        if h < 50: h = 50
        
        # update wraplength to match width
        self.label.config(wraplength=w-40)
        
        self.window.geometry(f"{int(w)}x{int(h)}")


    def show(self, text, x, y):
        self.label.config(text=text)
        
        # Calculate initial size based on text
        self.window.update_idletasks()
        
        # Reset Wraplength to default or 350 before calculating
        self.label.config(wraplength=350)
        
        w = self.label.winfo_reqwidth() + 20
        h = self.label.winfo_reqheight() + 20
        
        # Cap max initial width
        if w > 400: w = 400
        
        # Add offset
        x += 20
        y += 20
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if x + w > screen_width: x = screen_width - w - 10
        if y + h > screen_height: y = y - h - 40
            
        self.window.geometry(f"{int(w)}x{int(h)}+{int(x)}+{int(y)}")
        self.window.deiconify()

    def hide(self):
        self.window.withdraw()
