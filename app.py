import cv2
import numpy as np
from ahk import AHK
from mss import mss
import mss.tools
import tkinter as tk
import time
import ctypes

# --- CONFIGURATION ---
CONFIDENCE_THRESHOLD = 0.82
ROTATION_STEP = 45
DRAG_STEP = 450   # Higher = larger steps (faster drag)
MAX_STEPS = 2
DRAG_FREQUENCY = 0.02      # Faster scan interval
# ---------------------

ahk = AHK()

# DPI FIX
user32 = ctypes.windll.user32
SCREEN_WIDTH = user32.GetSystemMetrics(0)
# We calculate scale factor inside the loop to ensure it's fresh
SCALE_FACTOR = 1.0 

class TooltipMarker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.frame = tk.Frame(self.root, width=60, height=25, highlightbackground="lime", highlightthickness=2, bg="black")
        self.frame.pack()
        self.label = tk.Label(self.frame, text="TARGET", fg="lime", bg="black", font=("Arial", 7, "bold"))
        self.label.place(relx=0.5, rely=0.5, anchor="center")

    def show(self, x, y, img_h, scale):
        pos_x = int((x / scale) - 30)
        pos_y = int((y / scale) - (img_h / scale / 2) - 40)
        self.root.geometry(f"60x25+{pos_x}+{pos_y}")
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()
        try: self.root.update()
        except: pass

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

def get_screen_data():
    """Captures screen and returns (image, scale_factor)."""
    # Use mss.mss() instead of just mss()
    with mss.mss() as sct: 
        monitor = sct.monitors[1]
        try:
            sct_img = sct.grab(monitor)
            raw_width = monitor['width']
            scale = raw_width / SCREEN_WIDTH
            img = np.array(sct_img)
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            return gray, scale
        except Exception as e:
            # This catches the gdi32 error and prevents a crash
            return None, 1.0

def find_logic(template_gray, screen_gray):
    best_val = -1
    best_info = None
    for angle in range(0, 360, ROTATION_STEP):
        rotated = rotate_image(template_gray, angle)
        res = cv2.matchTemplate(screen_gray, rotated, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_val:
            best_val = max_val
            best_info = (max_loc, angle, rotated.shape)
            if best_val > 0.95: break 
    return best_val, best_info

def run_app():
    marker = TooltipMarker()
    template = cv2.imread('target.png', cv2.IMREAD_GRAYSCALE)

    if template is None:
        print("Error: target.png not found.")
        return

    ahk.run_script("CoordMode, Mouse, Screen")
    print("[*] Bees tool running.")

    BASE_DRAG_X = -1   # ALWAYS drag left-to-right base direction
    BASE_DRAG_Y = 0

    while True:
        screen_gray, scale = get_screen_data()
        if screen_gray is None:
            continue

        val, info = find_logic(template, screen_gray)

        if val > CONFIDENCE_THRESHOLD:
            (max_loc, angle, (h, w)) = info
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2

            ahk.mouse_move(int(cx / scale), int(cy / scale), speed=3)
            ahk.click(button='left', direction='down')

            marker.show(cx, cy, h, scale)

            base_dx = -1
            base_dy = 0

            angle = (-angle) % 360 # must use negative for vertical
            rad = np.deg2rad(angle)

            # rotate base vector by detected angle
            step_x = int((base_dx * np.cos(rad) - base_dy * np.sin(rad)) * DRAG_STEP)
            step_y = int((base_dx * np.sin(rad) + base_dy * np.cos(rad)) * DRAG_STEP)

            start_x, start_y = cx, cy
            moved = False
            still_frames = 0
            steps_taken = 0

            while True:
                ahk.mouse_move(step_x, step_y, relative=True, speed=1)
                steps_taken += 1

                # Check if we reached the limit
                if steps_taken >= MAX_STEPS:
                    ahk.click(button='left', direction='up')
                    marker.hide()
                    break # Exit the drag loop

                screen_gray, _ = get_screen_data()
                if screen_gray is None:
                    break

                val2, info2 = find_logic(template, screen_gray)

                if val2 < (CONFIDENCE_THRESHOLD - 0.15):
                    ahk.click(button='left', direction='up')
                    marker.hide()
                    break

                loc, _, (nh, nw) = info2
                tx = loc[0] + nw // 2
                ty = loc[1] + nh // 2

                marker.show(tx, ty, nh, scale)

                movement = np.hypot(tx - start_x, ty - start_y)

                # confirm movement
                if not moved:
                    if movement > 25:
                        moved = True
                    else:
                        still_frames += 1

                    if still_frames > 6:
                        ahk.click(button='left', direction='up')
                        marker.hide()
                        break

                time.sleep(DRAG_FREQUENCY)

        else:
            marker.hide()
            time.sleep(0.01)

if __name__ == "__main__":
    run_app()