import tkinter as tk
from tkinter import font, ttk
import threading
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import os
import wikipedia
import requests
import json
import time
from pynput.keyboard import Controller
from os import listdir
from os.path import isfile, join

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyD-VmK_jvneDbLsG1eOmNpcgjQFfT2UZgo"

# --- SAFE IMPORTS ---
try:
    import Gesture_Controller
except ImportError:
    Gesture_Controller = None
try:
    from eye import eye_move
except ImportError:
    eye_move = None
try:
    from samvk import vk_keyboard
except ImportError:
    vk_keyboard = None


class ProtonChatWindow:
    def __init__(self, on_close_callback=None):
        self.on_close_callback = on_close_callback

        self.root = tk.Toplevel()
        self.root.title("Proton AI")

        # Window State
        self.is_fullscreen = False
        self.prev_geom = "450x720"

        # Default Geometry
        w, h = 450, 720
        self.w = w
        self.h = h
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = int((ws / 2) - (w / 2))
        y = int((hs / 2) - (h / 2))
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # --- TRANSPARENCY SETUP ---
        TRANS_COLOR = "#add123"
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg=TRANS_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", TRANS_COLOR)
        except Exception:
            pass
        self.TRANS_COLOR = TRANS_COLOR

        # --- CUSTOM STYLES ---
        self.style = None
        self.root.after(10, self.init_styles)

        # Master Canvas
        self.container = tk.Canvas(self.root, bg=TRANS_COLOR, highlightthickness=0)
        self.container.pack(fill="both", expand=True)
        self.draw_background(w, h)

        # Dragging Logic
        self.container.bind("<Button-1>", self.start_move)
        self.container.bind("<B1-Motion>", self.do_move)
        self.root.bind("<Configure>", self.on_resize)

        # State
        self.is_awake = True
        self.is_listening_anim = False # Animation Flag
        self.file_exp_status = False
        self.files = []
        self.path = ""
        self.keyboard = Controller()
        self.active_model = "gemini-2.0-flash"
        self.stop_speaking = False

        # --- Smart Mode ---
        self.smart_mode_enabled = False
        self.awaiting_smart_confirmation = False
        self.last_unanswered_query = ""

        # TTS engine
        self.engine = None
        try:
            self.engine = pyttsx3.init("sapi5")
            try:
                voices = self.engine.getProperty("voices")
                if voices:
                    self.engine.setProperty("voice", voices[0].id)
            except Exception:
                pass
            self.engine.setProperty("rate", 170)
        except Exception:
            self.engine = None

        # UI
        self.setup_ui_content()

        self.root.update_idletasks()
        self.initial_place_input()

        # Startup
        threading.Thread(target=self.discover_model, daemon=True).start()
        self.root.after(200, self.wish)
        
        # Start Idle Animation
        self.animate_idle_dot()

    def init_styles(self):
        try:
            self.style = ttk.Style(self.root)
            try:
                self.style.theme_use("clam")
            except Exception:
                pass

            self.style.configure(
                "Dark.TScrollbar",
                troughcolor="#1E1E1E",
                background="#1E1E1E",
                bordercolor="#1E1E1E",
                arrowcolor="#888888",
                lightcolor="#1E1E1E",
                darkcolor="#1E1E1E",
            )
        except Exception:
            self.style = None

    def draw_background(self, w, h):
        self.container.delete("bg_shape")
        color = "#1E1E1E"
        radius = 25 if not self.is_fullscreen else 0

        if self.is_fullscreen:
            self.container.create_rectangle(0, 0, w, h, fill=color, outline=color, tags="bg_shape")
        else:
            self.container.create_oval(0, 0, radius * 2, radius * 2, fill=color, outline=color, tags="bg_shape")
            self.container.create_oval(w - radius * 2, 0, w, radius * 2, fill=color, outline=color, tags="bg_shape")
            self.container.create_oval(0, h - radius * 2, radius * 2, h, fill=color, outline=color, tags="bg_shape")
            self.container.create_oval(w - radius * 2, h - radius * 2, w, h, fill=color, outline=color, tags="bg_shape")
            self.container.create_rectangle(radius, 0, w - radius, h, fill=color, outline=color, tags="bg_shape")
            self.container.create_rectangle(0, radius, w, h - radius, fill=color, outline=color, tags="bg_shape")

    def on_resize(self, event):
        if event.widget == self.root:
            try:
                new_w = event.width
                new_h = event.height
            except Exception:
                new_w, new_h = self.w, self.h
            self.draw_background(new_w, new_h)

            self.input_y = new_h - 75
            self.input_w = new_w - 40

            self.container.delete("input_capsule")
            self.draw_rounded_rect_coords(
                20, self.input_y, 20 + self.input_w, self.input_y + 50, 25, "#2D2D2D", "input_capsule"
            )

            try:
                self.entry.place(x=50, y=self.input_y + 12, width=self.input_w - 100)
                self.btn_mic.place(x=20 + self.input_w - 55, y=self.input_y + 2)
            except Exception:
                pass

            try:
                self.chat_canvas.itemconfig(self.canvas_window, width=new_w - 80)
            except Exception:
                pass

    def start_move(self, event):
        if not self.is_fullscreen:
            self.x = event.x
            self.y = event.y

    def do_move(self, event):
        if not self.is_fullscreen:
            x = self.root.winfo_x() + (event.x - self.x)
            y = self.root.winfo_y() + (event.y - self.y)
            self.root.geometry(f"+{x}+{y}")

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.prev_geom = self.root.geometry()
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{w}x{h}+0+0")
        else:
            self.root.geometry(self.prev_geom)
        self.root.update()

    def setup_ui_content(self):
        # --- HEADER SECTION ---
        # We use a canvas rectangle to create a visual "Header" area that is darker/distinct if needed
        # For now, it matches the background but we layout buttons in TWO rows to prevent overlap.
        
        # 1. TITLE ROW (Top)
        self.status_dot = tk.Label(self.root, text="●", font=("Arial", 18), bg="#1E1E1E", fg="#00E676")
        self.status_dot.place(x=25, y=12)

        self.status_lbl = tk.Label(
            self.root, text="Proton AI", font=("Segoe UI", 12, "bold"), bg="#1E1E1E", fg="#FFFFFF"
        )
        self.status_lbl.place(x=50, y=15)

        # Window Controls (Top Right)
        btn_close = tk.Button(
            self.root, text="✕", font=("Arial", 11), command=self.close_window,
            bg="#1E1E1E", fg="#888888", bd=0, activebackground="#1E1E1E", activeforeground="white", cursor="hand2",
        )
        btn_close.place(relx=1.0, x=-35, y=12, width=30, height=30)

        btn_max = tk.Button(
            self.root, text="🗖", font=("Arial", 11), command=self.toggle_fullscreen,
            bg="#1E1E1E", fg="#888888", bd=0, activebackground="#1E1E1E", activeforeground="white", cursor="hand2",
        )
        btn_max.place(relx=1.0, x=-70, y=12, width=30, height=30)

        # 2. CONTROLS ROW (Immediately below title, preventing overlap)
        # Y-position = 50
        
        # Clear Button
        self.btn_clear = tk.Button(
            self.root, text="CLEAR", font=("Segoe UI", 8, "bold"),
            command=self.clear_chat, bg="#2D2D2D", fg="#888888", bd=0, cursor="hand2",
        )
        self.btn_clear.place(x=25, y=50, width=60, height=25)

        # Smart Mode Button
        self.smart_btn = tk.Button(
            self.root, text="Smart: OFF", font=("Segoe UI", 8, "bold"),
            command=self.toggle_smart_mode, bg="#2D2D2D", fg="#FFFFFF", bd=0, cursor="hand2",
        )
        self.smart_btn.place(x=95, y=50, width=80, height=25)

        # Stop Button
        self.btn_stop = tk.Button(
            self.root, text="STOP", font=("Segoe UI", 8, "bold"),
            command=self.stop_voice, bg="#2D2D2D", fg="#FF5252", bd=0, cursor="hand2",
        )
        self.btn_stop.place(x=185, y=50, width=50, height=25)

        # --- CHAT AREA ---
        # Moved down to y=85 to make room for the second row of buttons
        chat_container = tk.Frame(self.root, bg="#1E1E1E")
        chat_container.place(x=20, y=85, relwidth=1.0, width=-40, relheight=1.0, height=-175)

        self.chat_canvas = tk.Canvas(chat_container, bg="#1E1E1E", highlightthickness=0)
        self.chat_frame = tk.Frame(self.chat_canvas, bg="#1E1E1E")

        try:
            self.scrollbar = ttk.Scrollbar(
                chat_container, orient="vertical", command=self.chat_canvas.yview, style="Dark.TScrollbar"
            )
        except Exception:
            self.scrollbar = tk.Scrollbar(chat_container, orient="vertical", command=self.chat_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw", width=400)

        self.chat_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(self.canvas_window, width=e.width))

        # INPUT CAPSULE
        self.input_y = self.h - 75
        self.inp_bg_1 = self.container.create_oval(0, 0, 0, 0, fill="#2D2D2D", outline="#2D2D2D", tags="input_capsule")
        self.inp_bg_2 = self.container.create_oval(0, 0, 0, 0, fill="#2D2D2D", outline="#2D2D2D", tags="input_capsule")
        self.inp_bg_3 = self.container.create_rectangle(0, 0, 0, 0, fill="#2D2D2D", outline="#2D2D2D", tags="input_capsule")

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self.root, textvariable=self.entry_var, font=("Segoe UI", 11),
            bg="#2D2D2D", fg="white", insertbackground="white", relief="flat", bd=0, highlightthickness=0,
        )
        self.entry.bind("<Return>", self.on_enter)
        self.entry.insert(0, "Ask Proton...")
        self.entry.bind("<FocusIn>", self.clear_placeholder)
        self.entry.bind("<FocusOut>", self.add_placeholder)

        self.btn_mic = tk.Button(
            self.root, text="🎙️", font=("Segoe UI", 14), command=self.start_listening,
            bg="#2D2D2D", fg="#00E676", bd=0, width=4, cursor="hand2",
            activebackground="#2D2D2D", activeforeground="#00E676",
        )

        self.root.update()

    def initial_place_input(self):
        try:
            current_w = self.root.winfo_width() or self.w
            current_h = self.root.winfo_height() or self.h
            self.input_y = current_h - 75
            self.input_w = current_w - 40
            self.container.delete("input_capsule")
            self.draw_rounded_rect_coords(20, self.input_y, 20 + self.input_w, self.input_y + 50, 25, "#2D2D2D", "input_capsule")
            self.entry.place(x=50, y=self.input_y + 12, width=self.input_w - 100)
            self.btn_mic.place(x=20 + self.input_w - 55, y=self.input_y + 2)
        except Exception:
            pass

    def draw_rounded_rect_coords(self, x1, y1, x2, y2, radius, color, tag=None):
        self.container.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=color, outline=color, tags=tag)
        self.container.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=color, outline=color, tags=tag)
        self.container.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=color, outline=color, tags=tag)
        self.container.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=color, outline=color, tags=tag)
        self.container.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=color, outline=color, tags=tag)
        self.container.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=color, outline=color, tags=tag)

    # --- NEW CLEAR CHAT FUNCTION ---
    def clear_chat(self):
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.add_bubble("Proton", "Chat cleared.")

    # --- ANIMATION LOGIC ---
    def animate_mic_pulse(self):
        # Pulses the mic button while listening
        if self.is_listening_anim:
            current_fg = self.btn_mic.cget("fg")
            new_fg = "white" if current_fg == "#00E676" else "#00E676"
            self.btn_mic.config(fg=new_fg)
            self.root.after(500, self.animate_mic_pulse)
        else:
            self.btn_mic.config(fg="#00E676") # Reset to green

    def animate_idle_dot(self):
        # Slowly breathes the status dot
        if not self.is_listening_anim:
            current_fg = self.status_dot.cget("fg")
            # Simple toggle for breathing effect
            if current_fg == "#00E676":
                self.status_dot.config(fg="#008F4C") # Darker green
            else:
                self.status_dot.config(fg="#00E676") # Bright green
        self.root.after(1500, self.animate_idle_dot)

    # --- UI UPDATERS ---
    def safe_update_status(self, status):
        colors = {"listening": "#FF3D00", "thinking": "#FFC400", "speaking": "#2979FF", "idle": "#00E676"}
        text_map = {"listening": "Listening...", "thinking": "Thinking...", "speaking": "Speaking...", "idle": "Ready to help"}
        self.root.after(0, lambda: self._update_status_ui(colors.get(status, "#00E676"), text_map.get(status, "Ready")))

    def _update_status_ui(self, color, text):
        try:
            self.status_dot.config(fg=color)
            self.status_lbl.config(text=text)
        except Exception:
            pass

    def add_bubble(self, sender, text):
        self.root.after(0, lambda: self._create_bubble(sender, text))

    def _create_bubble(self, sender, text):
        wrapper = tk.Frame(self.chat_frame, bg="#1E1E1E", pady=5)
        wrapper.pack(fill="x", padx=10)
        if sender == "User":
            bubble = tk.Label(wrapper, text=text, font=("Segoe UI", 11), bg="#007ACC", fg="white", padx=15, pady=8, wraplength=280, justify="left")
            bubble.pack(side="right", anchor="e")
        elif sender == "Proton":
            bubble = tk.Label(wrapper, text=text, font=("Segoe UI", 11), bg="#333333", fg="white", padx=15, pady=8, wraplength=280, justify="left")
            bubble.pack(side="left", anchor="w")
        else:
            bubble = tk.Label(wrapper, text=text, font=("Segoe UI", 9, "italic"), bg="#1E1E1E", fg="#888888")
            bubble.pack(side="top", anchor="center")

        try:
            self.root.update_idletasks()
            self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
            self.chat_canvas.yview_moveto(1.0)
        except Exception:
            pass

    # --- LOGIC ---
    def clear_placeholder(self, event):
        try:
            if self.entry.get() == "Ask Proton...":
                self.entry.delete(0, tk.END)
                self.entry.config(fg="white")
        except Exception:
            pass

    def add_placeholder(self, event):
        try:
            if not self.entry.get():
                self.entry.insert(0, "Ask Proton...")
                self.entry.config(fg="#888888")
        except Exception:
            pass

    def close_window(self):
        self.stop_voice()
        try:
            self.root.destroy()
        except Exception:
            pass
        if self.on_close_callback:
            self.on_close_callback()

    def on_enter(self, event):
        try:
            text = self.entry_var.get()
            if text and text != "Ask Proton...":
                self.entry_var.set("")
                self.add_bubble("User", text)
                threading.Thread(target=self.respond, args=(text.lower(),), daemon=True).start()
        except Exception:
            pass

    def stop_voice(self):
        self.stop_speaking = True
        try:
            if self.engine:
                self.engine.stop()
        except Exception:
            pass

    def speak(self, text):
        clean_text = text.replace("*", "").replace("#", "")
        self.add_bubble("Proton", clean_text)
        self.stop_speaking = False
        self.safe_update_status("speaking")
        threading.Thread(target=self._speak, args=(clean_text,), daemon=True).start()

    def _speak(self, text):
        try:
            eng = None
            try:
                eng = pyttsx3.init("sapi5")
            except Exception:
                eng = self.engine
            if eng:
                eng.say(text)
                eng.runAndWait()
        except Exception:
            pass
        self.safe_update_status("idle")

    def wish(self):
        self.speak("Hello! I am Proton. How can I help?")

    def start_listening(self):
        self.safe_update_status("listening")
        # Start Animation
        self.is_listening_anim = True
        self.animate_mic_pulse()
        
        threading.Thread(target=self.process_voice, daemon=True).start()

    def process_voice(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, phrase_time_limit=5)
            
            # Stop Animation
            self.is_listening_anim = False
            self.safe_update_status("thinking")
            
            voice_data = r.recognize_google(audio).lower()
            self.add_bubble("User", voice_data)
            threading.Thread(target=self.respond, args=(voice_data,), daemon=True).start()
        except Exception:
            self.is_listening_anim = False
            self.safe_update_status("idle")

    def discover_model(self):
        self.active_model = "gemini-2.0-flash"

    def ask_gemini(self, prompt):
        self.safe_update_status("thinking")
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.active_model}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": f"{prompt}. Short answer."}]}]}
        try:
            res = requests.post(url, headers=headers, data=json.dumps(data))
            if res.status_code == 200:
                try:
                    return res.json()["candidates"][0]["content"]["parts"][0]["text"]
                except Exception:
                    return "Got an unexpected response from the server."
        except Exception:
            pass
        return "I couldn't reach the server."

    def toggle_smart_mode(self):
        self.smart_mode_enabled = not self.smart_mode_enabled
        self.smart_btn.config(text="Smart: ON" if self.smart_mode_enabled else "Smart: OFF")
        if self.smart_mode_enabled:
            self.speak("Smart Mode enabled.")
        else:
            self.speak("Smart Mode disabled.")
        self.awaiting_smart_confirmation = False
        self.last_unanswered_query = ""

    def enable_smart_mode_and_answer(self, question, permanent=False):
        self.smart_mode_enabled = True
        self.smart_btn.config(text="Smart: ON")
        if permanent:
            self.speak("Smart Mode enabled.")
        else:
            self.speak("Using Smart Mode to answer this question.")
        threading.Thread(target=lambda: self._ask_gemini_and_speak(question, leave_enabled=permanent), daemon=True).start()

    def disable_smart_mode(self):
        self.smart_mode_enabled = False
        self.smart_btn.config(text="Smart: OFF")
        self.speak("Smart Mode disabled.")
        self.awaiting_smart_confirmation = False
        self.last_unanswered_query = ""

    def ask_to_enable_smart_mode(self, text):
        self.awaiting_smart_confirmation = True
        self.last_unanswered_query = text
        self.speak("I don't recognize that command. Would you like me to enable Smart Mode to answer?")

    def _ask_gemini_and_speak(self, question, leave_enabled=False):
        try:
            ans = self.ask_gemini(question)
            self.speak(ans)
        except Exception:
            self.speak("I couldn't get an answer from Smart Mode.")
        if not leave_enabled:
            self.smart_mode_enabled = False
            try:
                self.smart_btn.config(text="Smart: OFF")
            except Exception:
                pass

    def respond(self, text):
        try:
            text = text.replace("proton", "").strip()
        except Exception:
            pass

        lowered = text.lower()
        if lowered in ["enable smart mode", "smart mode on", "smart mode enable", "enable smart"]:
            self.enable_smart_mode_and_answer("", permanent=True)
            return
        if lowered in ["disable smart mode", "smart mode off", "disable smart", "turn off smart mode"]:
            self.disable_smart_mode()
            return

        if self.awaiting_smart_confirmation:
            if any(w in lowered for w in ["yes", "yeah", "yep", "sure", "please", "ok", "enable"]):
                permanent = any(w in lowered for w in ["permanent", "enable", "turn on", "always"])
                q = self.last_unanswered_query or text
                self.awaiting_smart_confirmation = False
                self.last_unanswered_query = ""
                self.enable_smart_mode_and_answer(q, permanent=permanent)
                return
            elif any(w in lowered for w in ["no", "nope", "nah", "don't", "do not", "stop"]):
                self.awaiting_smart_confirmation = False
                self.last_unanswered_query = ""
                self.speak("Okay, Smart Mode not enabled.")
                return

        if "gesture mouse" in text or "launch gesture" in text:
            self.launch_mod(Gesture_Controller, "Gesture Mouse")
            return
        elif "virtual keyboard" in text or "launch keyboard" in text:
            self.launch_mod(vk_keyboard, "Keyboard")
            return
        elif "head tracker" in text or "launch head" in text:
            self.launch_mod(eye_move, "Head Tracker")
            return

        if "exit" in text or "bye" in text:
            self.speak("Goodbye.")
            self.root.after(1000, self.close_window)
            return

        if "time" in text:
            self.speak(datetime.datetime.now().strftime("%I:%M %p"))
            return
        if "date" in text:
            self.speak(datetime.date.today().strftime("%B %d, %Y"))
            return

        if "search" in text:
            q = text.split("search")[-1].strip()
            if q:
                self.speak(f"Searching for {q}")
                webbrowser.open(f"https://google.com/search?q={q}")
            else:
                self.speak("What should I search for?")
            return

        if "location" in text or "find" in text:
            q = ""
            if "location" in text:
                q = text.split("location")[-1].strip()
            elif "find" in text:
                q = text.split("find")[-1].strip()
            if q and q.lower() not in ["a location", "location", "place", ""]:
                self.speak(f"Locating {q}")
                webbrowser.open(f"https://www.google.com/maps/place/{q}/&")
            else:
                self.speak("What location should I find?")
            return

        if "wikipedia" in text:
            self.speak("Checking Wikipedia...")
            q = text.replace("wikipedia", "")
            try:
                self.speak(wikipedia.summary(q, sentences=2))
            except Exception:
                self.speak("No results found.")
            return

        if "list" in text:
            self.path = "C://"
            try:
                self.files = listdir(self.path)
                self.file_exp_status = True
                self.speak("Files listed.")
                self.add_bubble("Proton", "\n".join(self.files[:10]))
            except Exception:
                self.speak("Access Denied.")
            return
        if self.file_exp_status and "open" in text:
            try:
                import re
                nums = re.findall(r"\d+", text)
                if nums:
                    idx = int(nums[-1]) - 1
                    path = join(self.path, self.files[idx])
                    if isfile(path):
                        os.startfile(path)
                    else:
                        self.path = path + "//"
                        self.files = listdir(self.path)
                        self.speak("Opened.")
                        self.add_bubble("Proton", "\n".join(self.files[:10]))
            except Exception:
                self.speak("Error.")
            return
        if self.file_exp_status and "back" in text:
            try:
                if self.path != "C://":
                    self.path = os.path.dirname(os.path.dirname(self.path)) + "//"
                    self.files = listdir(self.path)
                    self.speak("Back.")
                    self.add_bubble("Proton", "\n".join(self.files[:10]))
            except Exception:
                self.speak("Error.")
            return

        if self.smart_mode_enabled:
            threading.Thread(target=lambda: self.speak(self.ask_gemini(text)), daemon=True).start()
            return

        self.ask_to_enable_smart_mode(text)

    def launch_mod(self, mod, name):
        if mod:
            self.speak(f"Launching {name}")
            try:
                if name == "Gesture Mouse":
                    threading.Thread(target=lambda: mod.GestureController().start(), daemon=True).start()
                elif name == "Keyboard":
                    threading.Thread(target=mod.vk_keyboard, daemon=True).start()
                elif name == "Head Tracker":
                    threading.Thread(target=mod.eye_move, daemon=True).start()
            except Exception:
                try:
                    threading.Thread(target=mod, daemon=True).start()
                except Exception:
                    self.speak("Could not launch module.")
        else:
            self.speak("Module missing.")


def proton_chat(on_close=None):
    ProtonChatWindow(on_close)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    proton_chat()
    root.mainloop()