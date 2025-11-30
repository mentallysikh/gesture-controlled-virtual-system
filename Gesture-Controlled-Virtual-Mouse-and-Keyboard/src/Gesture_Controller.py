import os
import sys
import subprocess
import time
import traceback
from threading import Thread

import cv2
import mediapipe as mp
import pyautogui
import math
import numpy as np
from enum import IntEnum
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from google.protobuf.json_format import MessageToDict
import screen_brightness_control as sbcontrol
import tkinter as tk

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

MAIN_PY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")


def draw_rounded_rectangle(img, pt1, pt2, color, thickness=-1, radius=12):
    """Draw a smooth rounded rectangle"""
    x1, y1 = pt1
    x2, y2 = pt2
    
    if thickness == -1:
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)
    else:
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)
        cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)


# --- COLORS ---
COLORS = {
    'bg': (10, 10, 10),
    'card_bg': (20, 20, 20),
    'border': (50, 50, 50),
    'text': (220, 220, 220),
    'text_dim': (120, 120, 120),
    'accent_green': (120, 255, 120),
    'accent_red': (120, 120, 255),
    'accent_blue': (255, 180, 100),
    'accent_yellow': (100, 220, 255),
    'accent_purple': (255, 100, 200),
    'accent_orange': (100, 165, 255)
}


# ---------------------------
# StatusBar UI (Enhanced)
# ---------------------------
class StatusBarUI:
    def __init__(self, stop_callback=None, width=280, height=70, margin=18):
        self.stop_callback = stop_callback
        self.width = width
        self.height = height
        self.margin = margin
        self.gesture_name = "Idle"

        try:
            self._root = tk.Tk()
            self._root.withdraw()
            self._root.overrideredirect(True)
            self._root.attributes("-topmost", True)
            self._root.attributes("-alpha", 0.95)
            self._root.configure(bg="#0A0A0A")

            frame = tk.Frame(self._root, bg="#0A0A0A", bd=0)
            frame.pack(fill="both", expand=True)

            # Title
            self._title = tk.Label(frame, text="GESTURE CONTROL", fg="#888888", bg="#0A0A0A",
                                   font=("Segoe UI", 8, "bold"))
            self._title.place(x=12, y=8)

            # Status indicator
            self._label = tk.Label(frame, text="● Idle", fg="#FF4D4D", bg="#0A0A0A",
                                   font=("Segoe UI", 12, "bold"))
            self._label.place(x=12, y=30)

            # Gesture label
            self._gesture = tk.Label(frame, text="", fg="#00AAFF", bg="#0A0A0A",
                                     font=("Segoe UI", 9))
            self._gesture.place(x=120, y=32)

            # Exit button
            self._btn = tk.Button(frame, text="✕", font=("Segoe UI", 11, "bold"),
                                  bg="#0A0A0A", fg="#FF5555", bd=0,
                                  activeforeground="#FF8888", activebackground="#1A1A1A",
                                  cursor="hand2", command=self._on_exit_click)
            self._btn.place(x=self.width - 40, y=18, width=30, height=30)

            # Drag support
            self._offset_x = 0
            self._offset_y = 0
            frame.bind("<ButtonPress-1>", self._start_move)
            frame.bind("<B1-Motion>", self._do_move)
            self._root.bind("<Escape>", lambda e: self._on_exit_click())

            # Calculate geometry
            self._root.update_idletasks()
            time.sleep(0.02)
            sw = self._root.winfo_screenwidth()
            px = max(0, sw - self.margin - self.width)
            py = max(0, self.margin)
            self._root.geometry(f"{self.width}x{self.height}+{px}+{py}")
            self._root.deiconify()
            self._root.lift()
            self._root.attributes("-topmost", True)
        except Exception:
            traceback.print_exc()
            self._root = None

    def _start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _do_move(self, event):
        try:
            x = self._root.winfo_x() + (event.x - self._offset_x)
            y = self._root.winfo_y() + (event.y - self._offset_y)
            self._root.geometry(f"+{max(0, x)}+{max(0, y)}")
        except:
            pass

    def set_active(self, active: bool, gesture_name: str = ""):
        if not self._root:
            return
        try:
            self._root.after(0, self._update_label, active, gesture_name)
        except:
            pass

    def _update_label(self, active: bool, gesture_name: str = ""):
        try:
            if active:
                self._label.config(text="● Active", fg="#00E676")
                if gesture_name:
                    self._gesture.config(text=gesture_name, fg="#00AAFF")
            else:
                self._label.config(text="● Idle", fg="#FF4D4D")
                self._gesture.config(text="")
        except:
            pass

    def _on_exit_click(self):
        try:
            if callable(self.stop_callback):
                self.stop_callback()
        except:
            pass
        try:
            self._root.quit()
            self._root.destroy()
        except:
            pass


# ---------------------------
# Gesture Controller
# ---------------------------
def gest_control():
    class Gest(IntEnum):
        FIST = 0
        PINKY = 1
        RING = 2
        MID = 4
        LAST3 = 7
        INDEX = 8
        FIRST2 = 12
        LAST4 = 15
        THUMB = 16
        PALM = 31
        V_GEST = 33
        TWO_FINGER_CLOSED = 34
        PINCH_MAJOR = 35
        PINCH_MINOR = 36

    # Gesture display names
    GESTURE_NAMES = {
        Gest.FIST: "DRAG",
        Gest.PALM: "PALM",
        Gest.V_GEST: "MOVE",
        Gest.MID: "LEFT CLICK",
        Gest.INDEX: "RIGHT CLICK",
        Gest.TWO_FINGER_CLOSED: "DOUBLE CLICK",
        Gest.PINCH_MAJOR: "VOLUME/BRIGHTNESS",
        Gest.PINCH_MINOR: "SCROLL"
    }

    class HLabel(IntEnum):
        MINOR = 0
        MAJOR = 1

    class HandRecog:
        def __init__(self, hand_label):
            self.finger = 0
            self.ori_gesture = Gest.PALM
            self.prev_gesture = Gest.PALM
            self.frame_count = 0
            self.hand_result = None
            self.hand_label = hand_label

        def update_hand_result(self, hand_result):
            self.hand_result = hand_result

        def get_signed_dist(self, point):
            sign = -1
            if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
                sign = 1
            dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
            dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
            return math.sqrt(dist) * sign

        def get_dist(self, point):
            dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x) ** 2
            dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y) ** 2
            return math.sqrt(dist)

        def get_dz(self, point):
            return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)

        def set_finger_state(self):
            if not self.hand_result:
                return
            points = [[8, 5, 0], [12, 9, 0], [16, 13, 0], [20, 17, 0]]
            self.finger = 0
            for idx, point in enumerate(points):
                try:
                    dist = self.get_signed_dist(point[:2])
                    dist2 = self.get_signed_dist(point[1:])
                    ratio = round(dist / dist2, 1)
                except:
                    ratio = 0
                self.finger = self.finger << 1
                if ratio > 0.5:
                    self.finger |= 1

        def get_gesture(self):
            if not self.hand_result:
                return Gest.PALM
            current_gesture = Gest.PALM
            try:
                if self.finger in [Gest.LAST3, Gest.LAST4] and self.get_dist([8, 4]) < 0.05:
                    current_gesture = Gest.PINCH_MINOR if self.hand_label == HLabel.MINOR else Gest.PINCH_MAJOR
                elif self.finger == Gest.FIRST2:
                    dist1 = self.get_dist([8, 12])
                    dist2 = self.get_dist([5, 9])
                    ratio = dist1 / dist2
                    if ratio > 1.7:
                        current_gesture = Gest.V_GEST
                    else:
                        if self.get_dz([8, 12]) < 0.1:
                            current_gesture = Gest.TWO_FINGER_CLOSED
                        else:
                            current_gesture = Gest.MID
                else:
                    current_gesture = self.finger
            except:
                current_gesture = self.finger
            
            if current_gesture == self.prev_gesture:
                self.frame_count += 1
            else:
                self.frame_count = 0
            self.prev_gesture = current_gesture
            if self.frame_count > 4:
                self.ori_gesture = current_gesture
            return self.ori_gesture

    class Controller:
        tx_old = 0
        ty_old = 0
        flag = False
        grabflag = False
        pinchmajorflag = False
        pinchminorflag = False
        pinchstartxcoord = None
        pinchstartycoord = None
        pinchdirectionflag = None
        prevpinchlv = 0
        pinchlv = 0
        framecount = 0
        prev_hand = None
        pinch_threshold = 0.3

        @staticmethod
        def getpinchylv(hand_result):
            return round((Controller.pinchstartycoord - hand_result.landmark[8].y) * 10, 1)

        @staticmethod
        def getpinchxlv(hand_result):
            return round((hand_result.landmark[8].x - Controller.pinchstartxcoord) * 10, 1)

        @staticmethod
        def changesystembrightness():
            lv = sbcontrol.get_brightness(display=0)[-1] / 100.0 + Controller.pinchlv / 50.0
            lv = max(0, min(1, lv))
            sbcontrol.fade_brightness(int(100 * lv), start=sbcontrol.get_brightness(display=0))

        @staticmethod
        def changesystemvolume():
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            lv = volume.GetMasterVolumeLevelScalar() + Controller.pinchlv / 50.0
            lv = max(0, min(1, lv))
            volume.SetMasterVolumeLevelScalar(lv, None)

        @staticmethod
        def scrollVertical():
            pyautogui.scroll(120 if Controller.pinchlv > 0 else -120)

        @staticmethod
        def scrollHorizontal():
            pyautogui.keyDown("shift")
            pyautogui.keyDown("ctrl")
            pyautogui.scroll(-120 if Controller.pinchlv > 0 else 120)
            pyautogui.keyUp("ctrl")
            pyautogui.keyUp("shift")

        @staticmethod
        def get_position(hand_result):
            x = int(hand_result.landmark[9].x * pyautogui.size()[0])
            y = int(hand_result.landmark[9].y * pyautogui.size()[1])
            if Controller.prev_hand is None:
                Controller.prev_hand = [x, y]
            delta_x = x - Controller.prev_hand[0]
            delta_y = y - Controller.prev_hand[1]
            Controller.prev_hand = [x, y]
            distsq = delta_x ** 2 + delta_y ** 2
            ratio = 1
            if distsq <= 25:
                ratio = 0
            elif distsq <= 900:
                ratio = 0.07 * math.sqrt(distsq)
            else:
                ratio = 2.1
            x_old, y_old = pyautogui.position()
            return int(x_old + delta_x * ratio), int(y_old + delta_y * ratio)

        @staticmethod
        def pinch_control_init(hand_result):
            Controller.pinchstartxcoord = hand_result.landmark[8].x
            Controller.pinchstartycoord = hand_result.landmark[8].y
            Controller.pinchlv = 0
            Controller.prevpinchlv = 0
            Controller.framecount = 0

        @staticmethod
        def pinch_control(hand_result, controlHorizontal, controlVertical):
            lvx = Controller.getpinchxlv(hand_result)
            lvy = Controller.getpinchylv(hand_result)
            if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
                Controller.pinchdirectionflag = False
                if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
                    Controller.framecount += 1
                else:
                    Controller.prevpinchlv = lvy
                    Controller.framecount = 0
            elif abs(lvx) > Controller.pinch_threshold:
                Controller.pinchdirectionflag = True
                if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
                    Controller.framecount += 1
                else:
                    Controller.prevpinchlv = lvx
                    Controller.framecount = 0
            if Controller.framecount >= 5:
                Controller.framecount = 0
                Controller.pinchlv = Controller.prevpinchlv
                if Controller.pinchdirectionflag:
                    controlHorizontal()
                elif Controller.pinchdirectionflag is False:
                    controlVertical()

        @staticmethod
        def handle_controls(gesture, hand_result):
            x, y = None, None
            if gesture != Gest.PALM:
                x, y = Controller.get_position(hand_result)

            if gesture != Gest.FIST and Controller.grabflag:
                Controller.grabflag = False
                pyautogui.mouseUp(button="left")
            if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
                Controller.pinchmajorflag = False
            if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
                Controller.pinchminorflag = False

            if gesture == Gest.V_GEST:
                Controller.flag = True
                pyautogui.moveTo(x, y, duration=0.1)
            elif gesture == Gest.FIST:
                if not Controller.grabflag:
                    Controller.grabflag = True
                    pyautogui.mouseDown(button="left")
                pyautogui.moveTo(x, y, duration=0.1)
            elif gesture == Gest.MID and Controller.flag:
                pyautogui.click()
                Controller.flag = False
            elif gesture == Gest.INDEX and Controller.flag:
                pyautogui.click(button="right")
                Controller.flag = False
            elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
                pyautogui.doubleClick()
                Controller.flag = False
            elif gesture == Gest.PINCH_MINOR:
                if not Controller.pinchminorflag:
                    Controller.pinch_control_init(hand_result)
                    Controller.pinchminorflag = True
                Controller.pinch_control(hand_result, Controller.scrollHorizontal, Controller.scrollVertical)
            elif gesture == Gest.PINCH_MAJOR:
                if not Controller.pinchmajorflag:
                    Controller.pinch_control_init(hand_result)
                    Controller.pinchmajorflag = True
                Controller.pinch_control(hand_result, Controller.changesystembrightness, Controller.changesystemvolume)

    class GestureController:
        gc_mode = 0
        cap = None
        hr_major = None
        hr_minor = None
        dom_hand = True

        def __init__(self):
            GestureController.gc_mode = 1
            GestureController.cap = cv2.VideoCapture(0)
            GestureController.cap.set(3, 1280)
            GestureController.cap.set(4, 720)

        @staticmethod
        def classify_hands(results):
            left, right = None, None
            try:
                handedness_dict = MessageToDict(results.multi_handedness[0])
                if handedness_dict["classification"][0]["label"] == "Right":
                    right = results.multi_hand_landmarks[0]
                else:
                    left = results.multi_hand_landmarks[0]
            except:
                pass
            try:
                handedness_dict = MessageToDict(results.multi_handedness[1])
                if handedness_dict["classification"][0]["label"] == "Right":
                    right = results.multi_hand_landmarks[1]
                else:
                    left = results.multi_hand_landmarks[1]
            except:
                pass
            if GestureController.dom_hand:
                GestureController.hr_major = right
                GestureController.hr_minor = left
            else:
                GestureController.hr_major = left
                GestureController.hr_minor = right

        def start(self):
            def stop_and_launch_main():
                setattr(GestureController, "gc_mode", 0)
                try:
                    if os.path.exists(MAIN_PY_PATH):
                        subprocess.Popen([sys.executable, MAIN_PY_PATH], cwd=os.path.dirname(MAIN_PY_PATH))
                except Exception as e:
                    print("Failed to launch main.py:", e)

            status_ui = None
            try:
                status_ui = StatusBarUI(stop_callback=stop_and_launch_main)
            except:
                traceback.print_exc()

            handmajor = HandRecog(HLabel.MAJOR)
            handminor = HandRecog(HLabel.MINOR)
            
            current_gesture_name = "Idle"
            start_time = time.time()
            gesture_count = 0

            with mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
                while GestureController.cap.isOpened() and GestureController.gc_mode:
                    success, image = GestureController.cap.read()
                    if not success:
                        continue
                    
                    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                    image.flags.writeable = False
                    results = hands.process(image)
                    image.flags.writeable = True
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                    
                    current_time = time.time()
                    hand_detected = results.multi_hand_landmarks is not None
                    
                    # Dark overlay
                    overlay = image.copy()
                    overlay[:] = COLORS['bg']
                    image = cv2.addWeighted(image, 0.4, overlay, 0.6, 0)
                    
                    # --- HEADER BAR ---
                    cv2.rectangle(image, (0, 0), (1280, 65), COLORS['card_bg'], -1)
                    cv2.line(image, (0, 65), (1280, 65), COLORS['border'], 1)
                    
                    # Title
                    cv2.putText(image, "GESTURE CONTROLLER", (30, 42), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLORS['text'], 2)
                    
                    # Hand detection status
                    status_color = COLORS['accent_green'] if hand_detected else COLORS['accent_red']
                    cv2.circle(image, (300, 35), 8, status_color, -1)
                    status_text = "HAND DETECTED" if hand_detected else "NO HAND"
                    cv2.putText(image, status_text, (315, 42), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
                    
                    # Current gesture
                    cv2.putText(image, f"GESTURE: {current_gesture_name}", (520, 42), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_blue'], 1)
                    
                    # Gesture count
                    cv2.putText(image, f"ACTIONS: {gesture_count}", (750, 42), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_yellow'], 1)
                    
                    # Session time
                    elapsed = int(current_time - start_time)
                    mins, secs = divmod(elapsed, 60)
                    cv2.putText(image, f"TIME: {mins:02d}:{secs:02d}", (900, 42), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text_dim'], 1)
                    
                    # Exit button
                    draw_rounded_rectangle(image, (1140, 15), (1260, 55), COLORS['accent_red'], -1, 8)
                    cv2.putText(image, "EXIT (ESC)", (1152, 42), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['bg'], 2)
                    
                    # --- SIDE PANELS ---
                    # Left panel - Gesture Guide
                    panel_x, panel_y = 30, 85
                    draw_rounded_rectangle(image, (panel_x, panel_y), (panel_x + 220, panel_y + 220), 
                                          COLORS['card_bg'], -1, 12)
                    draw_rounded_rectangle(image, (panel_x, panel_y), (panel_x + 220, panel_y + 220), 
                                          COLORS['border'], 1, 12)
                    
                    cv2.putText(image, "GESTURE GUIDE", (panel_x + 15, panel_y + 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_blue'], 1)
                    cv2.line(image, (panel_x + 10, panel_y + 35), (panel_x + 210, panel_y + 35), 
                            COLORS['border'], 1)
                    
                    gestures = [
                        ("V Sign", "Move Cursor"),
                        ("Fist", "Drag"),
                        ("Middle Up", "Left Click"),
                        ("Index Up", "Right Click"),
                        ("Two Closed", "Double Click"),
                        ("Pinch Minor", "Scroll"),
                        ("Pinch Major", "Vol/Bright")
                    ]
                    for i, (gesture, action) in enumerate(gestures):
                        y_pos = panel_y + 55 + i * 24
                        cv2.putText(image, gesture, (panel_x + 15, y_pos), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, COLORS['text'], 1)
                        cv2.putText(image, action, (panel_x + 115, y_pos), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, COLORS['text_dim'], 1)
                    
                    # Right panel - Current Action
                    panel_x2 = 1030
                    draw_rounded_rectangle(image, (panel_x2, panel_y), (panel_x2 + 220, panel_y + 160), 
                                          COLORS['card_bg'], -1, 12)
                    draw_rounded_rectangle(image, (panel_x2, panel_y), (panel_x2 + 220, panel_y + 160), 
                                          COLORS['border'], 1, 12)
                    
                    cv2.putText(image, "CURRENT ACTION", (panel_x2 + 15, panel_y + 25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_purple'], 1)
                    cv2.line(image, (panel_x2 + 10, panel_y + 35), (panel_x2 + 210, panel_y + 35), 
                            COLORS['border'], 1)
                    
                    # Large gesture display
                    cv2.putText(image, current_gesture_name, (panel_x2 + 20, panel_y + 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLORS['accent_green'] if hand_detected else COLORS['text_dim'], 2)
                    
                    # Mouse position
                    mx, my = pyautogui.position()
                    cv2.putText(image, f"Cursor: ({mx}, {my})", (panel_x2 + 15, panel_y + 130), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text_dim'], 1)
                    
                    # Process gestures
                    if results.multi_hand_landmarks:
                        if status_ui:
                            status_ui.set_active(True, current_gesture_name)
                        
                        GestureController.classify_hands(results)
                        handmajor.update_hand_result(GestureController.hr_major)
                        handminor.update_hand_result(GestureController.hr_minor)
                        handmajor.set_finger_state()
                        handminor.set_finger_state()
                        
                        gest_name = handminor.get_gesture()
                        if gest_name == Gest.PINCH_MINOR:
                            Controller.handle_controls(gest_name, handminor.hand_result)
                            current_gesture_name = GESTURE_NAMES.get(gest_name, "Unknown")
                        else:
                            gest_name = handmajor.get_gesture()
                            Controller.handle_controls(gest_name, handmajor.hand_result)
                            current_gesture_name = GESTURE_NAMES.get(gest_name, "Unknown")
                        
                        # Count actions
                        if gest_name in [Gest.MID, Gest.INDEX, Gest.TWO_FINGER_CLOSED]:
                            gesture_count += 1
                        
                        # Draw hand landmarks with custom style
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Draw connections
                            for connection in mp_hands.HAND_CONNECTIONS:
                                start_idx = connection[0]
                                end_idx = connection[1]
                                start = hand_landmarks.landmark[start_idx]
                                end = hand_landmarks.landmark[end_idx]
                                
                                start_point = (int(start.x * 1280), int(start.y * 720))
                                end_point = (int(end.x * 1280), int(end.y * 720))
                                
                                cv2.line(image, start_point, end_point, COLORS['accent_blue'], 2)
                            
                            # Draw landmarks
                            for idx, landmark in enumerate(hand_landmarks.landmark):
                                x = int(landmark.x * 1280)
                                y = int(landmark.y * 720)
                                
                                # Fingertips get larger circles
                                if idx in [4, 8, 12, 16, 20]:
                                    cv2.circle(image, (x, y), 10, COLORS['accent_green'], -1)
                                    cv2.circle(image, (x, y), 12, COLORS['accent_green'], 2)
                                else:
                                    cv2.circle(image, (x, y), 5, COLORS['accent_blue'], -1)
                    else:
                        if status_ui:
                            status_ui.set_active(False, "")
                        Controller.prev_hand = None
                        current_gesture_name = "Idle"
                    
                    # --- FOOTER ---
                    cv2.rectangle(image, (0, 695), (1280, 720), COLORS['card_bg'], -1)
                    footer_text = "CONTROLS: ESC=Exit | V-Sign=Move | Fist=Drag | Middle=Click | Index=Right Click"
                    cv2.putText(image, footer_text, (30, 712), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['text_dim'], 1)
                    
                    # Update Tk UI
                    if status_ui and status_ui._root:
                        try:
                            status_ui._root.update()
                        except tk.TclError:
                            status_ui = None

                    cv2.imshow("Gesture Controller", image)
                    if cv2.waitKey(5) & 0xFF == 27:  # ESC
                        break

            try:
                GestureController.cap.release()
                cv2.destroyAllWindows()
            except:
                pass

            if status_ui:
                status_ui._on_exit_click()

    # Run
    gc1 = GestureController()
    gc1.start()


if __name__ == "__main__":
    gest_control()