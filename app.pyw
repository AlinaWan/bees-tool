import atexit
import ctypes
import os
import time
import tkinter as tk

import cv2
import keyboard
import numpy as np
from ahk import AHK
from mss import mss

ahk = AHK()
user32 = ctypes.windll.user32
SCREEN_WIDTH = user32.GetSystemMetrics(0)
SCREEN_HEIGHT = user32.GetSystemMetrics(1)

##### CONFIGURATION #####
# --- Minigame Automation ---
CONFIDENCE_THRESHOLD = 0.82                   # Confidence to track
ROTATION_STEP = 45                            # Rotation steps
DRAG_STEP = int(SCREEN_HEIGHT * (500 / 1080)) # Drag step to drag based on the screen height
COOLDOWN_MS = 100                             # Cooldown
LOCK_DURATION_MS = 20                         # How long the object must persist to lock
DOWNSCALE_FACTOR = 0.5                        # 0.5 = 50% size (4x faster processing)
BOUNDARY_MARGIN = 100                         # Px allowed outside ROI before failing
MINIGAME_TIMEOUT_MS = 2000                    # Time a slider hasn't appeared to be considered not in minigame

# --- Meter Automation ---
AUTO_RELEASE_ENABLED = True                   # Enable the auto release module
AUTO_RELEASE_TOLERANCE = 5                    # Tolerance for the optimized search
AUTO_RELEASE_CONFIDENCE = 0.90                # Confidence for calibration
SEARCH_DEPTH = 20                             # Define how deep the search range is for the top of the meter

# --- Auto Routine ---
AUTO_ROUTINE_ENABLED = False                   # Enable the subroutine module (forces Auto Release)
AUTO_ROUTINE_PATTERN = (                      # Walk pattern
    ['w','w','w',
     'd','d','d',
     's','s','s',
     'a','a','a']
)
AUTO_ROUTINE_WALK_TIME_MS = 250               # Time to hold each walk key
AUTO_ROUTINE_LMB_TIMEOUT_MS = 3000            # Time a minigame hasn't appeared to give up this cycle

# Hotkeys
TOGGLE_KEY = 'f6'
EXIT_KEY = 'shift+esc'

# Template
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_PATH = os.path.join(SCRIPT_DIR, 'target.png')
METER_IMAGE_PATH = os.path.join(SCRIPT_DIR, 'meter.png')

#########################

# Global State
is_active = False
should_exit = False
last_slider_time = 0

meter_calibrated = False
meter_pixels = []
meter_colors = []
last_slider_time = time.perf_counter()

routine_index = 0
routine_state = "idle"
routine_lmb_down_time = 0

# Implicitly force AUTO_RELEASE if AUTO_ROUTINE
if AUTO_ROUTINE_ENABLED:
    AUTO_RELEASE_ENABLED = True

def toggle_logic():
    global is_active
    global routine_index, routine_state
    is_active = not is_active

    if is_active:
        routine_index = 0
        routine_state = "idle"

def exit_logic():
    global should_exit
    should_exit = True

# Register Hotkeys
keyboard.add_hotkey(TOGGLE_KEY, toggle_logic, suppress=True)
keyboard.add_hotkey(EXIT_KEY, exit_logic, suppress=True)

class ScanAreaOverlay:
    """Creates a persistent overlay showing the scan boundaries and 8 markers."""
    def __init__(self, area, scale):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-transparentcolor", "black")
        
        w = int(area['width'] / scale)
        h = int(area['height'] / scale)
        x = int(area['left'] / scale)
        y = int(area['top'] / scale)
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="black", highlightthickness=0)
        self.canvas.pack()

        self.points = [
            (0, 0), (w//2, 0), (w, 0),
            (0, h//2), (w, h//2),
            (0, h), (w//2, h), (w, h)
        ]
        self.dots = []
        for px, py in self.points:
            size = 2
            dot = self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill="red", outline="")
            self.dots.append(dot)

        # --- AUTO RELEASE VISUAL ---
        self.release_left_bar = None
        self.release_right_bar = None
        # ------------------------

    def update(self, active):
        color = "green" if active else "red"
        for dot in self.dots:
            self.canvas.itemconfig(dot, fill=color)
        self.root.update()

    # --- AUTO RELEASE VISUAL ---
    def draw_release_bars(self, x, y):
        if self.release_left_bar:
            self.canvas.delete(self.release_left_bar)
            self.canvas.delete(self.release_right_bar)
        size = 10
        gap = 10

        self.release_left_bar = self.canvas.create_rectangle(
            x-gap-size, y-1,
            x-gap, y+1,
            fill="yellow", outline=""
        )

        self.release_right_bar = self.canvas.create_rectangle(
            x+gap, y-1,
            x+gap+size, y+1,
            fill="yellow", outline=""
        )
    # ------------------------

class TooltipMarker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-transparentcolor", "black")
        
        self.canvas = tk.Canvas(self.root, width=1000, height=1000, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        self.circle = self.canvas.create_oval(10, 10, 70, 70, outline="lime", width=2)
        self.debug_text = self.canvas.create_text(10, 75, anchor="nw", fill="lime", font=("Consolas", 8))
        self.line = None 
        
    def show(self, x, y, scale, angle=0, confidence=0, locked=False, in_bounds=True, drag_to=None, winner_idx=None):
        if not in_bounds:
            color = "red"
        else:
            color = "cyan" if locked else "lime"
            
        self.canvas.itemconfig(self.circle, outline=color)
        self.canvas.itemconfig(self.debug_text, fill=color)

        logic_str = (
            f"VEC:  {angle:03}° [IDX: {winner_idx}]\n"
            f"CONF: {confidence*100:.1f}%\n"
            f"POS:  ({int(x/scale)}, {int(y/scale)})\n"
            f"BNDS: {'OK' if in_bounds else 'OUT'}"
        )
        self.canvas.itemconfig(self.debug_text, text=logic_str)

        if self.line:
            self.canvas.delete(self.line)
            self.line = None
        if drag_to:
            start_x, start_y = 40, 40 
            end_x = (drag_to[0] - x) / scale + start_x
            end_y = (drag_to[1] - y) / scale + start_y
            line_color = "red" if not in_bounds else "cyan"
            self.line = self.canvas.create_line(start_x, start_y, end_x, end_y, fill=line_color, width=2, dash=(4, 2))

        pos_x, pos_y = int((x / scale) - 40), int((y / scale) - 40)
        self.root.geometry(f"1000x1000+{pos_x}+{pos_y}")
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()
        try: self.root.update()
        except: pass

def pre_rotate_templates(template):
    t = cv2.resize(template, (0,0), fx=DOWNSCALE_FACTOR, fy=DOWNSCALE_FACTOR)
    rotated_cache = []
    for angle in range(0, 360, ROTATION_STEP):
        (h, w) = t.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(t, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        rotated_cache.append({'img': rotated, 'angle': angle})
    return rotated_cache

def run_app():
    global meter_calibrated, meter_pixels, meter_colors, last_slider_time
    global routine_index, routine_state, routine_lmb_down_time

    marker = TooltipMarker()

    raw_template = cv2.imread(TARGET_PATH, cv2.IMREAD_GRAYSCALE)
    if raw_template is None: return
    
    template_cache = pre_rotate_templates(raw_template)

    # --- AUTO RELEASE ---
    meter_template = cv2.imread(METER_IMAGE_PATH)
    if meter_template is not None:
        meter_template_gray = cv2.cvtColor(meter_template, cv2.COLOR_BGR2GRAY)
    else:
        meter_template_gray = None
    # -----------------

    ahk.run_script("CoordMode, Mouse, Screen")

    hit_counts = np.zeros(len(template_cache), dtype=int)
    search_order = list(range(len(template_cache)))
    
    last_drag_time = 0
    target_start_time = None
    
    with mss() as sct:
        full_mon = sct.monitors[1]
        full_w = full_mon['width']
        full_h = full_mon['height']
        scale = (full_w / SCREEN_WIDTH)

        center_x = full_mon['left'] + (full_w // 2)
        center_y = full_mon['top'] + (full_h // 2)

        half_step = DRAG_STEP // 2
        
        search_area = {
            "top": center_y - half_step,
            "left": center_x - half_step,
            "width": DRAG_STEP,
            "height": DRAG_STEP
        }

        search_left = search_area["left"]
        search_top = search_area["top"]

        area_visual = ScanAreaOverlay(search_area, scale)
        
        while not should_exit:
            area_visual.update(is_active)

            now = time.perf_counter()

            # --- AUTO RELEASE CALIBRATION ---
            if AUTO_RELEASE_ENABLED and not meter_calibrated and meter_template_gray is not None:
                right_half = {
                    "top": 0,
                    "left": SCREEN_WIDTH//2,
                    "width": SCREEN_WIDTH//2,
                    "height": SCREEN_HEIGHT
                }

                frame = np.array(sct.grab(right_half))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                res = cv2.matchTemplate(gray, meter_template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val >= AUTO_RELEASE_CONFIDENCE:
                        h, w = meter_template_gray.shape
                        top_y = max_loc[1]
                        center_x = max_loc[0] + w//2
                        start_x = center_x - 2
                
                        meter_pixels = []
                        meter_colors = []
                        
                        for i in range(4):
                            px = start_x + i
                            py = top_y
                            
                            screen_x = right_half["left"] + px
                            b, g, r = meter_template[py - max_loc[1], px - max_loc[0]][:3]
                            
                            meter_pixels.append(screen_x)
                            meter_colors.append((int(b), int(g), int(r)))
                            
                        meter_target_y = top_y 
                        meter_calibrated = True
            # -------------------------------

            # --- AUTO RELEASE CHECK ---
            time_since_last_slider = (now - last_slider_time) * 1000

            if (
                AUTO_RELEASE_ENABLED
                and meter_calibrated
                and time_since_last_slider > MINIGAME_TIMEOUT_MS
                and len(meter_pixels) == 4
            ):
                
                check_region = {
                    "top": meter_target_y,
                    "left": min(meter_pixels),
                    "width": (max(meter_pixels) - min(meter_pixels)) + 1,
                    "height": SEARCH_DEPTH
                }
                
                roi_capture = sct.grab(check_region)
                roi_img = np.array(roi_capture)[:, :, :3]
                
                matches_found = 0
                for i in range(4):
                    target_color = np.array(meter_colors[i], dtype=np.int16)
                    column_idx = meter_pixels[i] - check_region["left"]
                    
                    if 0 <= column_idx < roi_img.shape[1]:
                        vertical_strip = roi_img[:, column_idx].astype(np.int16)
                        diff = np.abs(vertical_strip - target_color)
                        if np.any(np.all(diff <= AUTO_RELEASE_TOLERANCE, axis=1)):
                            matches_found += 1

                if matches_found == 4 and is_active:
                    ahk.click(button='left', direction='up')
                    time.sleep(0.05)

                cx = meter_pixels[0]
                cy = meter_target_y
                local_x = cx - search_left
                local_y = cy - search_top
                vis_x = int(local_x / scale)
                vis_y = int(local_y / scale)
                
                if 0 <= vis_x <= area_visual.canvas.winfo_width() and 0 <= vis_y <= area_visual.canvas.winfo_height():
                    area_visual.draw_release_bars(vis_x, vis_y)
            # -----------------------

            # --- AUTO_ROUTINE ---
            if AUTO_ROUTINE_ENABLED and is_active:

                not_in_minigame = time_since_last_slider > MINIGAME_TIMEOUT_MS

                if routine_state == "idle" and not_in_minigame:

                    key = AUTO_ROUTINE_PATTERN[routine_index]

                    ahk.key_down(key)
                    time.sleep(AUTO_ROUTINE_WALK_TIME_MS / 1000)
                    ahk.key_up(key)

                    routine_index = (routine_index + 1) % len(AUTO_ROUTINE_PATTERN)

                    ahk.click(button='left', direction='down')
                    routine_lmb_down_time = now

                    routine_state = "holding"

                elif routine_state == "holding":

                    if not not_in_minigame:
                        routine_state = "idle"

                    elif (now - routine_lmb_down_time) * 1000 > AUTO_ROUTINE_LMB_TIMEOUT_MS:
                        ahk.click(button='left', direction='up')
                        routine_state = "idle"
            # --------------------

            if not is_active:
                marker.hide()
                target_start_time = None
                time.sleep(0.1)
                continue

            sct_img = sct.grab(search_area)
            img = np.array(sct_img)
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            small_gray = cv2.resize(gray, (0,0), fx=DOWNSCALE_FACTOR, fy=DOWNSCALE_FACTOR)

            best_val = -1
            best_info = None
            winner_idx = None
            
            for i in search_order:
                item = template_cache[i]
                res = cv2.matchTemplate(small_gray, item['img'], cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                if max_val > best_val:
                    best_val = max_val
                    best_info = (max_loc, item['angle'], item['img'].shape)
                    winner_idx = i
                    if best_val > 0.95: break

            now = time.perf_counter()
            if best_val > CONFIDENCE_THRESHOLD:
                last_slider_time = now

                hit_counts[winner_idx] += 1
                search_order = sorted(range(len(template_cache)), key=lambda k: hit_counts[k], reverse=True)

                if target_start_time is None:
                    target_start_time = now
                
                locked_duration = (now - target_start_time) * 1000
                is_locked = locked_duration >= LOCK_DURATION_MS
                
                (max_loc, angle, (h, w)) = best_info
                
                local_cx = (max_loc[0] + w // 2) / DOWNSCALE_FACTOR
                local_cy = (max_loc[1] + h // 2) / DOWNSCALE_FACTOR
                
                global_cx = local_cx + search_left
                global_cy = local_cy + search_top

                rad = np.deg2rad(-angle % 360)
                dest_x = global_cx - (np.cos(rad) * DRAG_STEP)
                dest_y = global_cy - (np.sin(rad) * DRAG_STEP)
                
                in_bounds = (
                    (search_left - BOUNDARY_MARGIN) <= dest_x <= (search_left + search_area["width"] + BOUNDARY_MARGIN) and
                    (search_top - BOUNDARY_MARGIN) <= dest_y <= (search_top + search_area["height"] + BOUNDARY_MARGIN)
                )
                
                marker.show(global_cx, global_cy, scale, angle=angle, confidence=best_val, locked=is_locked, in_bounds=in_bounds, drag_to=(dest_x, dest_y), winner_idx=winner_idx)

                if in_bounds and is_locked and (now - last_drag_time) * 1000 > COOLDOWN_MS:
                    ahk_x = int(global_cx / scale)
                    ahk_y = int(global_cy / scale)
                    
                    ahk.click(button='right', direction='up')
                    ahk.mouse_move(ahk_x, ahk_y, speed=1)
                    ahk.mouse_move(1, 0, relative=True)
                    ahk.click(button='left', direction='down')

                    ahk.mouse_move(int(-np.cos(rad)*DRAG_STEP), int(-np.sin(rad)*DRAG_STEP), relative=True, speed=1)
                    ahk.mouse_move(1, 0, relative=True)
                    ahk.click(button='left', direction='up')

                    last_drag_time = time.perf_counter()
                    target_start_time = None
            else:
                target_start_time = None
                marker.hide()

    area_visual.root.destroy()
    marker.root.destroy()

def cleanup():
    keyboard.unhook_all()

atexit.register(cleanup)

if __name__ == "__main__":
    run_app()