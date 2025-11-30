import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math

# Global flag to stop the loop
should_exit = False

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

def mouse_click_handler(event, x, y, flags, param):
    global should_exit
    # Check if click is inside EXIT button area
    if event == cv2.EVENT_LBUTTONDOWN:
        if 1140 < x < 1260 and 15 < y < 55:
            should_exit = True

def eye_move():
    global should_exit
    should_exit = False
    
    # --- SETTINGS ---
    DEAD_ZONE = 15
    SPEED_MULTIPLIER = 15
    MOUTH_THRESH = 15
    BLINK_THRESH = 0.004
    RIGHT_CLICK_TIME = 2.0
    
    # --- COLORS (BGR) ---
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
        'dead_zone': (60, 60, 60),
        'joystick_idle': (200, 200, 200),
        'joystick_active': (100, 255, 100),
        'progress_bg': (40, 40, 40),
        'progress_fill': (255, 150, 100)
    }
    
    pyautogui.FAILSAFE = False
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 1280)
    cam.set(4, 720)
    
    cv2.namedWindow('Head Tracker')
    cv2.setMouseCallback('Head Tracker', mouse_click_handler)
    
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    cam_w = int(cam.get(3))
    cam_h = int(cam.get(4))
    center_x, center_y = cam_w // 2, cam_h // 2
    
    eyes_closed_start = 0
    face_detected = False
    click_count = 0
    start_time = time.time()
    
    print("=" * 60)
    print("👁️  ENHANCED HEAD TRACKER")
    print("=" * 60)
    print("CONTROLS:")
    print("  • Move head to control cursor")
    print("  • Open mouth = Left Click")
    print("  • Close eyes 2 seconds = Right Click")
    print("HOTKEYS:")
    print("  • Q = Exit")
    print("  • +/- = Adjust Speed")
    print("  • D = Adjust Dead Zone")
    print("=" * 60)

    while True:
        if should_exit:
            break

        success, frame = cam.read()
        if not success:
            break
        
        frame = cv2.flip(frame, 1)
        current_time = time.time()
        
        # Dark overlay on camera
        overlay = frame.copy()
        overlay[:] = COLORS['bg']
        frame = cv2.addWeighted(frame, 0.4, overlay, 0.6, 0)
        
        # Process face
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = face_mesh.process(rgb_frame)
        face_detected = output.multi_face_landmarks is not None
        
        # --- HEADER BAR ---
        cv2.rectangle(frame, (0, 0), (1280, 65), COLORS['card_bg'], -1)
        cv2.line(frame, (0, 65), (1280, 65), COLORS['border'], 1)
        
        # Title
        cv2.putText(frame, "HEAD TRACKER", (30, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLORS['text'], 2)
        
        # Face detection status
        status_color = COLORS['accent_green'] if face_detected else COLORS['accent_red']
        cv2.circle(frame, (230, 35), 8, status_color, -1)
        status_text = "FACE DETECTED" if face_detected else "NO FACE"
        cv2.putText(frame, status_text, (245, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        # Settings display
        cv2.putText(frame, f"SPEED: {SPEED_MULTIPLIER}", (450, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text_dim'], 1)
        cv2.putText(frame, f"DEAD ZONE: {DEAD_ZONE}", (600, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text_dim'], 1)
        
        # Click counter
        cv2.putText(frame, f"CLICKS: {click_count}", (780, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_blue'], 1)
        
        # Session time
        elapsed = int(current_time - start_time)
        mins, secs = divmod(elapsed, 60)
        cv2.putText(frame, f"TIME: {mins:02d}:{secs:02d}", (920, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['text_dim'], 1)
        
        # Exit button
        draw_rounded_rectangle(frame, (1140, 15), (1260, 55), COLORS['accent_red'], -1, 8)
        cv2.putText(frame, "EXIT (Q)", (1160, 42), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLORS['bg'], 2)
        
        # --- JOYSTICK VISUALIZATION ---
        joystick_x, joystick_y = center_x, center_y
        joystick_radius = 80
        
        # Joystick background circle
        cv2.circle(frame, (joystick_x, joystick_y), joystick_radius + 20, COLORS['card_bg'], -1)
        cv2.circle(frame, (joystick_x, joystick_y), joystick_radius + 20, COLORS['border'], 2)
        
        # Dead zone indicator
        cv2.circle(frame, (joystick_x, joystick_y), DEAD_ZONE, COLORS['dead_zone'], 2)
        cv2.circle(frame, (joystick_x, joystick_y), 3, COLORS['dead_zone'], -1)
        
        # Direction indicators
        for angle, label in [(0, "R"), (90, "D"), (180, "L"), (270, "U")]:
            rad = math.radians(angle)
            lx = int(joystick_x + (joystick_radius + 10) * math.cos(rad))
            ly = int(joystick_y + (joystick_radius + 10) * math.sin(rad))
            cv2.putText(frame, label, (lx - 5, ly + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text_dim'], 1)
        
        # --- CONTROL PANELS ---
        # Left panel - Controls guide
        panel_x, panel_y = 30, 85
        draw_rounded_rectangle(frame, (panel_x, panel_y), (panel_x + 200, panel_y + 180), 
                              COLORS['card_bg'], -1, 12)
        draw_rounded_rectangle(frame, (panel_x, panel_y), (panel_x + 200, panel_y + 180), 
                              COLORS['border'], 1, 12)
        
        cv2.putText(frame, "CONTROLS", (panel_x + 15, panel_y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_blue'], 1)
        cv2.line(frame, (panel_x + 10, panel_y + 35), (panel_x + 190, panel_y + 35), 
                COLORS['border'], 1)
        
        controls = [
            ("Move Head", "Cursor"),
            ("Open Mouth", "Left Click"),
            ("Close Eyes", "Right Click"),
            ("Hold 2 sec", "to confirm")
        ]
        for i, (action, result) in enumerate(controls):
            y_pos = panel_y + 60 + i * 30
            cv2.putText(frame, action, (panel_x + 15, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text'], 1)
            cv2.putText(frame, result, (panel_x + 110, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text_dim'], 1)
        
        # Right panel - Status
        panel_x2 = 1050
        draw_rounded_rectangle(frame, (panel_x2, panel_y), (panel_x2 + 200, panel_y + 180), 
                              COLORS['card_bg'], -1, 12)
        draw_rounded_rectangle(frame, (panel_x2, panel_y), (panel_x2 + 200, panel_y + 180), 
                              COLORS['border'], 1, 12)
        
        cv2.putText(frame, "STATUS", (panel_x2 + 15, panel_y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_purple'], 1)
        cv2.line(frame, (panel_x2 + 10, panel_y + 35), (panel_x2 + 190, panel_y + 35), 
                COLORS['border'], 1)
        
        # Status indicators
        statuses = [
            ("Face", face_detected),
            ("Eyes Open", eyes_closed_start == 0),
            ("Moving", False),
            ("Clicking", False)
        ]
        
        is_moving = False
        is_clicking = False
        
        if output.multi_face_landmarks:
            landmarks = output.multi_face_landmarks[0].landmark
            
            # --- MOVEMENT (Nose Joystick) ---
            nose = landmarks[4]
            nose_x = int(nose.x * cam_w)
            nose_y = int(nose.y * cam_h)
            
            offset_x = nose_x - center_x
            offset_y = nose_y - center_y
            
            move_x = 0
            move_y = 0
            
            if abs(offset_x) > DEAD_ZONE:
                move_x = (offset_x - (DEAD_ZONE if offset_x > 0 else -DEAD_ZONE))
                is_moving = True
            if abs(offset_y) > DEAD_ZONE:
                move_y = (offset_y - (DEAD_ZONE if offset_y > 0 else -DEAD_ZONE))
                is_moving = True

            if move_x != 0 or move_y != 0:
                curr_x, curr_y = pyautogui.position()
                new_x = curr_x + (move_x // 2) * (SPEED_MULTIPLIER / 10)
                new_y = curr_y + (move_y // 2) * (SPEED_MULTIPLIER / 10)
                pyautogui.moveTo(new_x, new_y)

            # Draw nose position on joystick
            joystick_color = COLORS['joystick_active'] if is_moving else COLORS['joystick_idle']
            cv2.circle(frame, (nose_x, nose_y), 8, joystick_color, -1)
            cv2.circle(frame, (nose_x, nose_y), 12, joystick_color, 2)
            cv2.line(frame, (center_x, center_y), (nose_x, nose_y), joystick_color, 2)

            # --- EYE TRACKING (Right Click) ---
            left_dist = abs(landmarks[159].y - landmarks[145].y)
            right_dist = abs(landmarks[386].y - landmarks[374].y)
            
            if left_dist < BLINK_THRESH and right_dist < BLINK_THRESH:
                if eyes_closed_start == 0:
                    eyes_closed_start = current_time
                
                elapsed_blink = current_time - eyes_closed_start
                progress = min(elapsed_blink / RIGHT_CLICK_TIME, 1.0)
                
                # Progress bar
                bar_x = center_x - 120
                bar_y = center_y + joystick_radius + 50
                bar_w = 240
                bar_h = 25
                
                draw_rounded_rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), 
                                       COLORS['progress_bg'], -1, 8)
                
                progress_w = int(bar_w * progress)
                if progress_w > 0:
                    draw_rounded_rectangle(frame, (bar_x, bar_y), (bar_x + progress_w, bar_y + bar_h), 
                                          COLORS['progress_fill'], -1, 8)
                
                cv2.putText(frame, "RIGHT CLICK", (bar_x + 70, bar_y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS['accent_yellow'], 1)

                if elapsed_blink >= RIGHT_CLICK_TIME:
                    pyautogui.click(button='right')
                    click_count += 1
                    eyes_closed_start = current_time + 1.0
                    is_clicking = True
                    time.sleep(0.2)
            else:
                eyes_closed_start = 0

            # --- MOUTH TRACKING (Left Click) ---
            upper_lip = landmarks[13].y * cam_h
            lower_lip = landmarks[14].y * cam_h
            mouth_dist = abs(upper_lip - lower_lip)
            
            if eyes_closed_start == 0 and mouth_dist > MOUTH_THRESH:
                # Click indicator
                click_y = center_y - joystick_radius - 50
                draw_rounded_rectangle(frame, (center_x - 60, click_y - 15), 
                                       (center_x + 60, click_y + 15), 
                                       COLORS['accent_green'], -1, 8)
                cv2.putText(frame, "CLICK!", (center_x - 35, click_y + 6), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLORS['bg'], 2)
                
                pyautogui.click()
                click_count += 1
                is_clicking = True
                time.sleep(0.3)
            
            # Update status
            statuses[2] = ("Moving", is_moving)
            statuses[3] = ("Clicking", is_clicking)
        
        # Draw status indicators
        for i, (name, active) in enumerate(statuses):
            y_pos = panel_y + 60 + i * 30
            color = COLORS['accent_green'] if active else COLORS['accent_red']
            cv2.circle(frame, (panel_x2 + 20, y_pos - 5), 5, color, -1)
            cv2.putText(frame, name, (panel_x2 + 35, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLORS['text'], 1)
            status_txt = "Active" if active else "Idle"
            cv2.putText(frame, status_txt, (panel_x2 + 120, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # --- FOOTER ---
        cv2.rectangle(frame, (0, 695), (1280, 720), COLORS['card_bg'], -1)
        footer_text = "HOTKEYS: Q=Exit | +/-=Speed | D=Dead Zone | Move EXIT button to quit"
        cv2.putText(frame, footer_text, (30, 712), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['text_dim'], 1)
        
        # Mouse position display
        mx, my = pyautogui.position()
        cv2.putText(frame, f"CURSOR: ({mx}, {my})", (1050, 712), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLORS['accent_blue'], 1)
        
        cv2.imshow('Head Tracker', frame)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('=') or key == ord('+'):
            SPEED_MULTIPLIER = min(30, SPEED_MULTIPLIER + 2)
        elif key == ord('-') or key == ord('_'):
            SPEED_MULTIPLIER = max(5, SPEED_MULTIPLIER - 2)
        elif key == ord('d'):
            DEAD_ZONE = (DEAD_ZONE + 5) % 35
            if DEAD_ZONE < 5:
                DEAD_ZONE = 5
            
    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    eye_move()