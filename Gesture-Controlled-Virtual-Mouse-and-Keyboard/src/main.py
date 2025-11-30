import tkinter as tk
from tkinter import font, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageOps
import os
import time
import threading

# --- SAFE IMPORTS ---
try:
    from Gesture_Controller import gest_control
except ImportError:
    gest_control = None
try:
    from eye import eye_move
except ImportError:
    eye_move = None
try:
    from samvk import vk_keyboard
except ImportError:
    vk_keyboard = None
try:
    from Proton import proton_chat
except ImportError:
    proton_chat = None


class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Control Hub")
        self.root.geometry('1200x800')
        self.root.configure(bg='#0A0A0A')
        self.root.resizable(False, False)
        
        # Animation variables
        self.animation_running = True
        self.pulse_value = 0
        self.active_card = None
        
        # --- COLORS ---
        self.colors = {
            'bg': '#0A0A0A',
            'card_bg': '#141414',
            'card_hover': '#1A1A1A',
            'text_primary': '#FFFFFF',
            'text_secondary': '#6B6B6B',
            'accent_green': '#00FF88',
            'accent_blue': '#00AAFF',
            'accent_yellow': '#FFAA00',
            'accent_red': '#FF4444',
            'accent_purple': '#AA44FF',
            'border': '#2A2A2A'
        }

        # --- ASSETS ---
        self.icons = {
            'mic': self.load_image('icons/bot.png', (40, 40)),
            'key': self.load_image('icons/keyboard.png', (40, 40)),
            'eye': self.load_image('icons/eye.jpeg', (40, 40)),
            'mouse': self.load_image('icons/hand.png', (40, 40)),
            'exit': self.load_image('icons/exit.png', (18, 18)),
            'settings': self.load_image('icons/settings.png', (18, 18))
        }

        # --- MAIN CONTAINER ---
        self.main_container = tk.Frame(root, bg=self.colors['bg'])
        self.main_container.pack(fill='both', expand=True)

        # --- HEADER SECTION ---
        self.create_header()

        # --- STATS BAR ---
        self.create_stats_bar()

        # --- MAIN GRID ---
        self.create_card_grid()

        # --- QUICK ACTIONS ---
        self.create_quick_actions()

        # --- FOOTER ---
        self.create_footer()

        # Start animations
        self.animate_pulse()

    def create_header(self):
        """Creates the modern header with animated elements"""
        header = tk.Frame(self.main_container, bg=self.colors['bg'])
        header.pack(pady=(40, 20), fill='x')

        # Title container
        title_frame = tk.Frame(header, bg=self.colors['bg'])
        title_frame.pack()

        # Accent line above title
        accent_canvas = tk.Canvas(title_frame, width=60, height=4, 
                                  bg=self.colors['bg'], highlightthickness=0)
        accent_canvas.pack(pady=(0, 15))
        accent_canvas.create_rectangle(0, 0, 60, 4, fill=self.colors['accent_green'], outline='')

        # Main title
        title_label = tk.Label(title_frame, text="AI CONTROL HUB", 
                               font=("Segoe UI", 42, "bold"),
                               bg=self.colors['bg'], fg=self.colors['text_primary'])
        title_label.pack()

        # Subtitle with version
        subtitle_frame = tk.Frame(title_frame, bg=self.colors['bg'])
        subtitle_frame.pack(pady=(8, 0))

        tk.Label(subtitle_frame, text="NEXT-GEN TOUCHLESS INTERFACE", 
                 font=("Segoe UI", 11, "bold"),
                 bg=self.colors['bg'], fg=self.colors['text_secondary']).pack(side='left')

        # Version badge
        version_frame = tk.Frame(subtitle_frame, bg=self.colors['accent_green'], padx=8, pady=2)
        version_frame.pack(side='left', padx=(15, 0))
        tk.Label(version_frame, text="v2.0", font=("Segoe UI", 8, "bold"),
                 bg=self.colors['accent_green'], fg=self.colors['bg']).pack()

    def create_stats_bar(self):
        """Creates the statistics/info bar"""
        stats_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        stats_frame.pack(pady=(10, 30), fill='x', padx=100)

        stats_inner = tk.Frame(stats_frame, bg=self.colors['card_bg'], padx=30, pady=15)
        stats_inner.pack()

        # Draw rounded corners (simulated with canvas)
        stats_data = [
            ("MODULES", "4 Available", self.colors['accent_green']),
            ("STATUS", "All Systems Online", self.colors['accent_blue']),
            ("MODE", "Gesture Control", self.colors['accent_purple']),
            ("LATENCY", "< 50ms", self.colors['accent_yellow'])
        ]

        for i, (label, value, color) in enumerate(stats_data):
            stat_container = tk.Frame(stats_inner, bg=self.colors['card_bg'])
            stat_container.pack(side='left', padx=30)

            # Colored dot indicator
            dot_canvas = tk.Canvas(stat_container, width=8, height=8,
                                   bg=self.colors['card_bg'], highlightthickness=0)
            dot_canvas.pack(side='left', padx=(0, 8))
            dot_canvas.create_oval(0, 0, 8, 8, fill=color, outline='')

            # Label
            tk.Label(stat_container, text=label, font=("Segoe UI", 9),
                     bg=self.colors['card_bg'], fg=self.colors['text_secondary']).pack(side='left')

            # Value
            tk.Label(stat_container, text=f"  {value}", font=("Segoe UI", 9, "bold"),
                     bg=self.colors['card_bg'], fg=self.colors['text_primary']).pack(side='left')

            # Separator
            if i < len(stats_data) - 1:
                sep = tk.Frame(stats_inner, width=1, height=30, bg=self.colors['border'])
                sep.pack(side='left', padx=20)

    def create_card_grid(self):
        """Creates the main card grid"""
        grid = tk.Frame(self.main_container, bg=self.colors['bg'])
        grid.pack(expand=True, pady=(0, 20))

        # Card Configuration
        cards_data = [
            {
                'title': "Voice Assistant",
                'subtitle': "AI Speech Commands",
                'description': "Control your system with voice",
                'icon': self.icons['mic'],
                'command': lambda: self.launch_module(proton_chat, True),
                'color': self.colors['accent_green'],
                'shortcut': "V",
                'status': "Ready"
            },
            {
                'title': "Virtual Keyboard",
                'subtitle': "Gesture Typing",
                'description': "Type without touching",
                'icon': self.icons['key'],
                'command': lambda: self.launch_module(vk_keyboard),
                'color': self.colors['accent_blue'],
                'shortcut': "K",
                'status': "Ready"
            },
            {
                'title': "Head Tracker",
                'subtitle': "Face Mouse Control",
                'description': "Move cursor with head",
                'icon': self.icons['eye'],
                'command': lambda: self.launch_module(eye_move),
                'color': self.colors['accent_yellow'],
                'shortcut': "H",
                'status': "Ready"
            },
            {
                'title': "Gesture Mouse",
                'subtitle': "Hand Tracking",
                'description': "Full hand gesture control",
                'icon': self.icons['mouse'],
                'command': lambda: self.launch_module(gest_control),
                'color': self.colors['accent_red'],
                'shortcut': "G",
                'status': "Ready"
            }
        ]

        # Create 2x2 grid
        for idx, card_data in enumerate(cards_data):
            row, col = divmod(idx, 2)
            self.create_modern_card(grid, card_data, row, col)

    def create_modern_card(self, parent, data, row, col):
        """Creates a modern card with hover effects and animations"""
        width, height = 420, 160
        
        container = tk.Frame(parent, bg=self.colors['bg'], padx=15, pady=15)
        container.grid(row=row, column=col)

        canvas = tk.Canvas(container, width=width, height=height,
                           bg=self.colors['bg'], highlightthickness=0, cursor="hand2")
        canvas.pack()

        # Store card reference
        card_id = f"card_{row}_{col}"

        def draw_card(hover=False, click=False):
            canvas.delete("all")
            
            bg = self.colors['card_hover'] if hover else self.colors['card_bg']
            if click:
                bg = '#222222'
            
            radius = 16
            color = data['color']
            
            # Main card shape (rounded rectangle)
            # Top-left corner
            canvas.create_arc((0, 0, radius*2, radius*2), start=90, extent=90, 
                             fill=bg, outline=bg)
            # Top-right corner
            canvas.create_arc((width-radius*2, 0, width, radius*2), start=0, extent=90, 
                             fill=bg, outline=bg)
            # Bottom-left corner
            canvas.create_arc((0, height-radius*2, radius*2, height), start=180, extent=90, 
                             fill=bg, outline=bg)
            # Bottom-right corner
            canvas.create_arc((width-radius*2, height-radius*2, width, height), start=270, extent=90, 
                             fill=bg, outline=bg)
            # Fill rectangles
            canvas.create_rectangle((radius, 0, width-radius, height), fill=bg, outline=bg)
            canvas.create_rectangle((0, radius, width, height-radius), fill=bg, outline=bg)

            # Left accent bar with gradient effect
            bar_width = 5
            canvas.create_rectangle((0, 20, bar_width, height-20), fill=color, outline=color)
            
            # Glow effect on hover
            if hover:
                for i in range(3):
                    glow_alpha = 0.1 - (i * 0.03)
                    canvas.create_rectangle((bar_width, 20+i*5, bar_width+10-i*3, height-20-i*5), 
                                          fill=color, outline=color, stipple='gray50')

            # Icon circle background
            icon_x, icon_y = 55, height // 2
            circle_radius = 28
            canvas.create_oval(icon_x - circle_radius, icon_y - circle_radius,
                              icon_x + circle_radius, icon_y + circle_radius,
                              fill='#1E1E1E', outline=color if hover else '#2A2A2A', width=2)

            # Icon
            if data['icon']:
                canvas.create_image(icon_x, icon_y, image=data['icon'], anchor='center')

            # Title
            canvas.create_text(105, height//2 - 28, text=data['title'],
                              font=("Segoe UI", 18, "bold"), fill=self.colors['text_primary'], anchor='w')

            # Subtitle
            canvas.create_text(105, height//2 + 2, text=data['subtitle'],
                              font=("Segoe UI", 12), fill=color, anchor='w')

            # Description
            canvas.create_text(105, height//2 + 28, text=data['description'],
                              font=("Segoe UI", 10), fill=self.colors['text_secondary'], anchor='w')

            # Shortcut badge
            badge_x = width - 50
            badge_y = 25
            canvas.create_rectangle(badge_x - 15, badge_y - 12, badge_x + 15, badge_y + 12,
                                   fill='#1E1E1E', outline=self.colors['border'])
            canvas.create_text(badge_x, badge_y, text=data['shortcut'],
                              font=("Segoe UI", 10, "bold"), fill=self.colors['text_secondary'])

            # Status indicator
            status_x = width - 70
            status_y = height - 25
            canvas.create_oval(status_x - 4, status_y - 4, status_x + 4, status_y + 4,
                              fill=self.colors['accent_green'], outline='')
            canvas.create_text(status_x + 20, status_y, text=data['status'],
                              font=("Segoe UI", 9), fill=self.colors['text_secondary'], anchor='w')

            # Arrow indicator on hover
            if hover:
                arrow_x = width - 25
                arrow_y = height // 2
                canvas.create_text(arrow_x, arrow_y, text="→",
                                  font=("Segoe UI", 16, "bold"), fill=color)

        # Initial draw
        draw_card()

        # Events
        canvas.bind("<Enter>", lambda e: draw_card(hover=True))
        canvas.bind("<Leave>", lambda e: draw_card(hover=False))
        canvas.bind("<Button-1>", lambda e: [draw_card(click=True), 
                                              self.root.after(100, data['command'])])

        return canvas

    def create_quick_actions(self):
        """Creates quick action buttons"""
        actions_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        actions_frame.pack(pady=(0, 20))

        quick_label = tk.Label(actions_frame, text="QUICK ACTIONS",
                               font=("Segoe UI", 9, "bold"),
                               bg=self.colors['bg'], fg=self.colors['text_secondary'])
        quick_label.pack(pady=(0, 10))

        buttons_frame = tk.Frame(actions_frame, bg=self.colors['bg'])
        buttons_frame.pack()

        actions = [
            ("⚙ Settings", self.colors['text_secondary'], lambda: self.show_settings()),
            ("📋 Logs", self.colors['text_secondary'], lambda: self.show_logs()),
            ("❓ Help", self.colors['text_secondary'], lambda: self.show_help()),
            ("🔄 Refresh", self.colors['accent_blue'], lambda: self.refresh_modules())
        ]

        for text, color, cmd in actions:
            btn = tk.Label(buttons_frame, text=text, font=("Segoe UI", 10),
                          bg=self.colors['card_bg'], fg=color, padx=20, pady=8, cursor="hand2")
            btn.pack(side='left', padx=5)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.colors['card_hover']))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.colors['card_bg']))
            btn.bind("<Button-1>", lambda e, c=cmd: c())

    def create_footer(self):
        """Creates the modern footer"""
        footer = tk.Frame(self.main_container, bg=self.colors['bg'])
        footer.pack(side="bottom", fill="x", pady=30, padx=50)

        # Left side - Status with animated dot
        status_frame = tk.Frame(footer, bg=self.colors['bg'])
        status_frame.pack(side="left")

        self.status_dot = tk.Canvas(status_frame, width=12, height=12,
                                    bg=self.colors['bg'], highlightthickness=0)
        self.status_dot.pack(side='left', padx=(0, 8))
        self.status_dot.create_oval(2, 2, 10, 10, fill=self.colors['accent_green'], 
                                    outline=self.colors['accent_green'], tags='dot')

        self.status_var = tk.StringVar(value="System Ready")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=("Segoe UI", 11), bg=self.colors['bg'], 
                               fg=self.colors['text_primary'])
        status_label.pack(side='left')

        # Center - Keyboard shortcuts hint
        hint_label = tk.Label(footer, text="Press V, K, H, or G for quick launch",
                             font=("Segoe UI", 9), bg=self.colors['bg'], 
                             fg=self.colors['text_secondary'])
        hint_label.pack(side='left', padx=(100, 0))

        # Right side - Exit button
        exit_frame = tk.Frame(footer, bg=self.colors['accent_red'], padx=2, pady=2)
        exit_frame.pack(side="right")

        exit_btn = tk.Button(exit_frame, text="  EXIT SYSTEM  ", 
                            command=self.exit_app,
                            bg=self.colors['bg'], fg=self.colors['accent_red'],
                            font=("Segoe UI", 10, "bold"), bd=0,
                            activebackground=self.colors['accent_red'],
                            activeforeground=self.colors['bg'], cursor="hand2",
                            padx=15, pady=8)
        exit_btn.pack()

        # Bind keyboard shortcuts
        self.root.bind('v', lambda e: self.launch_module(proton_chat, True))
        self.root.bind('k', lambda e: self.launch_module(vk_keyboard))
        self.root.bind('h', lambda e: self.launch_module(eye_move))
        self.root.bind('g', lambda e: self.launch_module(gest_control))
        self.root.bind('<Escape>', lambda e: self.exit_app())

    def animate_pulse(self):
        """Animates the status dot"""
        if not self.animation_running:
            return
            
        self.pulse_value = (self.pulse_value + 0.1) % (2 * 3.14159)
        import math
        alpha = int(180 + 75 * math.sin(self.pulse_value))
        
        # Update dot color (simulated pulse)
        if hasattr(self, 'status_dot'):
            color = self.colors['accent_green']
            self.status_dot.delete('dot')
            self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline=color, tags='dot')
        
        self.root.after(50, self.animate_pulse)

    # --- MODULE LOGIC ---
    def launch_module(self, func, is_gui=False):
        if func:
            self.root.withdraw()
            self.status_var.set("Running Module...")
            self.update_status_color(self.colors['accent_blue'])
            
            if is_gui:
                func(on_close=self.restore)
            else:
                try:
                    func()
                except Exception as e:
                    print(f"Module error: {e}")
                self.restore()
        else:
            self.status_var.set("Module Not Available")
            self.update_status_color(self.colors['accent_red'])
            self.root.after(2000, lambda: [self.status_var.set("System Ready"),
                                           self.update_status_color(self.colors['accent_green'])])

    def restore(self):
        self.root.deiconify()
        self.status_var.set("System Ready")
        self.update_status_color(self.colors['accent_green'])

    def update_status_color(self, color):
        if hasattr(self, 'status_dot'):
            self.status_dot.delete('dot')
            self.status_dot.create_oval(2, 2, 10, 10, fill=color, outline=color, tags='dot')

    def show_settings(self):
        self.status_var.set("Settings opened...")

    def show_logs(self):
        self.status_var.set("Logs opened...")

    def show_help(self):
        self.status_var.set("Help opened...")

    def refresh_modules(self):
        self.status_var.set("Refreshing modules...")
        self.update_status_color(self.colors['accent_yellow'])
        self.root.after(1000, lambda: [self.status_var.set("System Ready"),
                                       self.update_status_color(self.colors['accent_green'])])

    def exit_app(self):
        self.animation_running = False
        self.root.quit()

    # --- UI HELPERS ---
    def load_image(self, path, size):
        search_paths = [
            path,
            f"../{path}",
            f"src/{path}",
            path.replace('icons/', ''),
            f"src/icons/{path.split('/')[-1]}" if '/' in path else path
        ]
        
        for real_path in search_paths:
            if os.path.exists(real_path):
                try:
                    img = Image.open(real_path).resize(size, Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(img)
                except Exception as e:
                    continue
        return None


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernApp(root)
    root.mainloop()