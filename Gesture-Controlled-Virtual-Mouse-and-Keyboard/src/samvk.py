import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
from time import time
import numpy as np
import math
from pynput.keyboard import Controller, Key

# --- GLOBAL VARIABLES ---
CLICK_COOLDOWN = 0.35

def draw_rounded_rectangle(img, pt1, pt2, color, thickness=-1, radius=12):
    """Draw a smooth rounded rectangle"""
    x1, y1 = pt1
    x2, y2 = pt2
    
    if thickness == -1:
        # Filled rounded rectangle
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1)
    else:
        # Border only
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)
        cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)

def add_glow(img, pt1, pt2, color, intensity=20):
    """Add subtle glow effect"""
    overlay = img.copy()
    x1, y1 = pt1
    x2, y2 = pt2
    
    for i in range(3):
        expand = (i + 1) * 4
        alpha = intensity / (i + 1) / 255.0
        cv2.rectangle(overlay, (x1 - expand, y1 - expand), (x2 + expand, y2 + expand), color, -1)
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    return img

def vk_keyboard():
    # State variables
    last_click_time = 0.0
    pinch_threshold = 40
    dwell_click_enabled = False
    paused = False
    current_layout = "letters"
    key_click_states = {}
    hover_start_time = {}
    final_text = ""
    
    # Animation variables
    cursor_blink = True
    last_blink_time = time()
    
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(3, 1280)
        cap.set(4, 720)

        if not cap.isOpened():
            print("Error: Could not open camera")
            return

        detector = HandDetector(detectionCon=0.5, maxHands=1)
        keyboard = Controller()
        
        # --- SLEEK BLACK THEME ---
        COLORS = {
            'bg': (10, 10, 10),
            'card_bg': (20, 20, 20),
            'key_inactive': (35, 35, 35),
            'key_hover': (55, 55, 55),
            'key_active': (80, 80, 80),
            'key_special': (45, 40, 50),
            'key_special_hover': (65, 60, 70),
            'border': (50, 50, 50),
            'border_hover': (80, 80, 80),
            'border_active': (120, 120, 120),
            'text': (220, 220, 220),
            'text_dim': (120, 120, 120),
            'input_bg': (15, 15, 15),
            'input_text': (230, 230, 230),
            'accent_green': (120, 255, 120),
            'accent_red': (120, 120, 255),
            'accent_blue': (255, 180, 100),
            'accent_yellow': (100, 220, 255),
            'dwell_progress': (255, 150, 100),
            'pause_active': (180, 100, 255),
            'pause_inactive': (100, 80, 120)
        }

        # --- KEYBOARD LAYOUT ---
        layouts = {
            "letters": [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
                ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]"],
                ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'"],
                ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "CLEAR"]
            ]
        }

        class Button():
            def __init__(self, pos, text, size=[80, 80], special=False):
                self.pos = pos
                self.size = size
                self.text = text
                self.id = text
                self.special = special

        def create_keyboard(layout_name):
            buttonList = []
            layout = layouts[layout_name]
            y_start = 210
            
            for k in range(len(layout)):
                for x, key in enumerate(layout[k]):
                    size = [80, 80]
                    offset_x = 0
                    
                    if k == 1: offset_x = 25
                    if k == 2: offset_x = 50
                    if k == 3: offset_x = 75
                    
                    is_special = key in ["CLEAR"]
                    if key == "CLEAR":
                        size = [100, 80]
                    
                    buttonList.append(Button([95 * x + 45 + offset_x, 95 * k + y_start], key, size, is_special))
            
            # Bottom row special buttons
            buttonList.append(Button([120, 595], "DWELL", [100, 80], True))
            buttonList.append(Button([235, 595], "PAUSE", [100, 80], True))
            buttonList.append(Button([350, 595], "SPACE", [450, 80], True))
            buttonList.append(Button([815, 595], "DEL", [100, 80], True))
            
            return buttonList

        buttonList = create_keyboard(current_layout)

        print("=" * 60)
        print("🎹 ENHANCED VIRTUAL KEYBOARD")
        print("=" * 60)
        print("CONTROLS:")
        print("  • Pinch index + middle finger to click")
        print("  • DWELL mode: Hover 1 second to click")
        print("HOTKEYS:")
        print("  • Q = Exit")
        print("  • P = Pause/Resume")
        print("  • D = Toggle Dwell Mode")
        print("  • +/- = Adjust Pinch Sensitivity")
        print("=" * 60)

        while True:
            success, img = cap.read()
            if not success: break
            
            img = cv2.flip(img, 1)
            current_time = time()
            
            # Cursor blink animation
            if current_time - last_blink_time > 0.5:
                cursor_blink = not cursor_blink
                last_blink_time = current_time
            
            # Detect hands
            hands, img = detector.findHands(img, flipType=False, draw=False)
            hand_detected = len(hands) > 0
            
            # Initialize hand data
            is_pinched = False
            x1, y1, x2, y2 = 0, 0, 0, 0
            pinch_distance = 999
            
            if hands:
                hand = hands[0]
                lmList = hand['lmList']
                x1, y1 = lmList[8][0], lmList[8][1]
                x2, y2 = lmList[12][0], lmList[12][1]
                pinch_distance = math.hypot(x2 - x1, y2 - y1)
                is_pinched = pinch_distance < pinch_threshold
            
            # --- DRAW BACKGROUND ---
            # Dark overlay on camera
            overlay = img.copy()
            overlay[:] = COLORS['bg']
            img = cv2.addWeighted(img, 0.3, overlay, 0.7, 0)
            
            # --- HEADER SECTION ---
            # Title bar
            cv2.rectangle(img, (0, 0), (1280, 60), COLORS['card_bg'], -1)
            cv2.line(img, (0, 60), (1280, 60), COLORS['border'], 1)
            
            # Title
            cv2.putText(img, "VIRTUAL KEYBOARD", (30, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLORS['text'], 2)
            
            # Hand status indicator
            status_color = COLORS['accent_green'] if hand_detected else COLORS['accent_red']
            cv2.circle(img, (280, 35), 8, status_color, -1)
            status_text = "HAND DETECTED" if hand_detected else "NO HAND"
            cv2.putText(img, status_text, (295, 42), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
            
            # Pinch distance indicator
            if hand_detected:
                dist_color = COLORS['accent_green'] if is_pinched else COLORS['text_dim']
                cv2.putText(img, f"PINCH: {int(pinch_distance)}px", (480, 42), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, dist_color, 1)
            
            # Mode indicators
            mode_x = 650
            
            # Dwell mode
            dwell_color = COLORS['accent_yellow'] if dwell_click_enabled else COLORS['text_dim']
            cv2.putText(img, f"DWELL: {'ON' if dwell_click_enabled else 'OFF'}", (mode_x, 42), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, dwell_color, 1)
            
            # Pause mode
            pause_color = COLORS['pause_active'] if paused else COLORS['text_dim']
            cv2.putText(img, f"PAUSED: {'YES' if paused else 'NO'}", (mode_x + 130, 42), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, pause_color, 1)
            
            # Sensitivity
            cv2.putText(img, f"SENS: {pinch_threshold}", (mode_x + 280, 42), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text_dim'], 1)
            
            # Exit button
            exit_x, exit_y = 1150, 15
            draw_rounded_rectangle(img, (exit_x, exit_y), (exit_x + 100, exit_y + 35), 
                                  COLORS['accent_red'], -1, 8)
            cv2.putText(img, "EXIT (Q)", (exit_x + 12, exit_y + 24), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['bg'], 2)
            
            # --- INPUT DISPLAY ---
            input_y = 80
            draw_rounded_rectangle(img, (30, input_y), (1250, input_y + 100), 
                                  COLORS['input_bg'], -1, 15)
            draw_rounded_rectangle(img, (30, input_y), (1250, input_y + 100), 
                                  COLORS['border'], 2, 15)
            
            # Input label
            cv2.putText(img, "INPUT", (50, input_y + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text_dim'], 1)
            
            # Input text with cursor
            display_text = final_text[-50:] if len(final_text) > 50 else final_text
            cursor = "|" if cursor_blink else " "
            cv2.putText(img, display_text + cursor, (50, input_y + 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.3, COLORS['input_text'], 2)
            
            # Character count
            cv2.putText(img, f"{len(final_text)} chars", (1150, input_y + 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text_dim'], 1)
            
            # --- KEYBOARD BACKGROUND ---
            kb_y = 195
            draw_rounded_rectangle(img, (25, kb_y), (1255, 695), 
                                  COLORS['card_bg'], -1, 20)
            draw_rounded_rectangle(img, (25, kb_y), (1255, 695), 
                                  COLORS['border'], 1, 20)
            
            # --- HAND VISUALIZATION ---
            if hands:
                # Finger tip circle
                cv2.circle(img, (x1, y1), 12, COLORS['accent_blue'], 2)
                cv2.circle(img, (x1, y1), 6, COLORS['accent_blue'], -1)
                
                # Pinch line
                line_color = COLORS['accent_green'] if is_pinched else COLORS['accent_blue']
                cv2.line(img, (x1, y1), (x2, y2), line_color, 3)
                cv2.circle(img, (x2, y2), 6, line_color, -1)
            
            # --- DRAW KEYS ---
            for button in buttonList:
                x, y = button.pos
                w, h = button.size
                key_id = button.id
                
                # Initialize state tracking
                if key_id not in key_click_states:
                    key_click_states[key_id] = {"last_click": 0.0, "was_pinched": False}
                if key_id not in hover_start_time:
                    hover_start_time[key_id] = 0.0
                
                # Determine colors based on button type
                if button.special:
                    base_color = COLORS['key_special']
                    hover_color = COLORS['key_special_hover']
                else:
                    base_color = COLORS['key_inactive']
                    hover_color = COLORS['key_hover']
                
                # Special button colors
                if button.text == "DWELL":
                    if dwell_click_enabled:
                        base_color = (60, 100, 60)
                        hover_color = (80, 130, 80)
                elif button.text == "PAUSE":
                    if paused:
                        base_color = (80, 60, 100)
                        hover_color = (100, 80, 130)
                    else:
                        base_color = (60, 50, 70)
                        hover_color = (80, 70, 90)
                
                current_color = base_color
                border_color = COLORS['border']
                is_hover = False
                click_triggered = False
                
                # Handle interaction
                if hands and not paused:
                    is_hover = x < x1 < x + w and y < y1 < y + h
                    
                    if is_hover:
                        current_color = hover_color
                        border_color = COLORS['border_hover']
                        
                        # Pinch click detection
                        can_click = (current_time - key_click_states[key_id]["last_click"]) > CLICK_COOLDOWN
                        just_pinched = is_pinched and not key_click_states[key_id]["was_pinched"]
                        key_click_states[key_id]["was_pinched"] = is_pinched
                        
                        if just_pinched and can_click:
                            click_triggered = True
                            hover_start_time[key_id] = 0.0
                        
                        # Dwell click detection
                        if dwell_click_enabled and not click_triggered:
                            if hover_start_time[key_id] == 0.0:
                                hover_start_time[key_id] = current_time
                            else:
                                dwell_duration = current_time - hover_start_time[key_id]
                                if dwell_duration > 1.0 and can_click:
                                    click_triggered = True
                                    hover_start_time[key_id] = 0.0
                        else:
                            hover_start_time[key_id] = 0.0
                    else:
                        hover_start_time[key_id] = 0.0
                        key_click_states[key_id]["was_pinched"] = False
                
                # Handle click action
                if click_triggered:
                    current_color = COLORS['key_active']
                    border_color = COLORS['border_active']
                    key_click_states[key_id]["last_click"] = current_time
                    
                    if button.text == "DEL":
                        final_text = final_text[:-1]
                    elif button.text == "SPACE":
                        final_text += " "
                    elif button.text == "DWELL":
                        dwell_click_enabled = not dwell_click_enabled
                    elif button.text == "PAUSE":
                        paused = not paused
                    elif button.text == "CLEAR":
                        final_text = ""
                    else:
                        final_text += button.text
                
                # Draw glow effect on hover
                if is_hover:
                    img = add_glow(img, (x, y), (x + w, y + h), border_color, 15)
                
                # Draw key
                draw_rounded_rectangle(img, (x, y), (x + w, y + h), current_color, -1, 12)
                draw_rounded_rectangle(img, (x, y), (x + w, y + h), border_color, 2, 12)
                
                # Dwell progress bar
                if is_hover and dwell_click_enabled and hover_start_time.get(key_id, 0.0) != 0.0:
                    dwell_duration = current_time - hover_start_time[key_id]
                    progress = min(dwell_duration / 1.0, 1.0)
                    progress_w = int((w - 10) * progress)
                    if progress_w > 0:
                        cv2.rectangle(img, (x + 5, y + 5), (x + 5 + progress_w, y + 10), 
                                     COLORS['dwell_progress'], -1)
                
                # Key text
                font_scale = 1.0 if len(button.text) <= 1 else (0.7 if len(button.text) <= 3 else 0.5)
                text_size = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
                text_x = x + (w - text_size[0]) // 2
                text_y = y + (h + text_size[1]) // 2
                cv2.putText(img, button.text, (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLORS['text'], 2)
            
            # --- FOOTER ---
            cv2.rectangle(img, (0, 700), (1280, 720), COLORS['card_bg'], -1)
            footer_text = "HOTKEYS: Q=Exit | P=Pause | D=Dwell | +/-=Sensitivity"
            cv2.putText(img, footer_text, (30, 715), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['text_dim'], 1)
            
            # Show window
            cv2.imshow("Virtual Keyboard", img)
            
            # Handle keyboard input
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('p'):
                paused = not paused
            elif key == ord('d'):
                dwell_click_enabled = not dwell_click_enabled
            elif key == ord('=') or key == ord('+'):
                pinch_threshold = min(60, pinch_threshold + 5)
            elif key == ord('-') or key == ord('_'):
                pinch_threshold = max(15, pinch_threshold - 5)
        
        cap.release()
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter...")

if __name__ == "__main__":
    vk_keyboard()