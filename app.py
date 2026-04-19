import cv2
import numpy as np
from ahk import AHK
from mss import mss
import tkinter as tk
import ctypes
import time

# --- CONFIGURATION ---
CONFIDENCE_THRESHOLD = 0.82 # Confidence to track
ROTATION_STEP = 45 # Rotation steps
DRAG_STEP = 500 # Drag step to drag
COOLDOWN_MS = 200 # Cooldown
LOCK_DURATION_MS = 10 # How long the object must persist to lock
DOWNSCALE_FACTOR = 0.5  # 0.5 = 50% size (5x faster processing)
# ---------------------

ahk = AHK()
user32 = ctypes.windll.user32
SCREEN_WIDTH = user32.GetSystemMetrics(0)

class ScanAreaOverlay:
    """Creates a persistent overlay showing the scan boundaries and 8 markers."""
    def __init__(self, area, scale):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-transparentcolor", "black")
        
        # Geometry matches the search_area exactly
        # We divide by scale because Tkinter uses screen logical coordinates
        w = int(area['width'] / scale)
        h = int(area['height'] / scale)
        x = int(area['left'] / scale)
        y = int(area['top'] / scale)
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="black", highlightthickness=0)
        self.canvas.pack()

        
        # Dashed bounding box
        # self.canvas.create_rectangle(0, 0, w-1, h-1, outline="red", width=1, dash=(4, 4))

        # 8 Points: [x, y] relative to the canvas
        points = [
            (0, 0), (w//2, 0), (w, 0),      # Top row
            (0, h//2), (w, h//2),           # Middle row
            (0, h), (w//2, h), (w, h)       # Bottom row
        ]

        for px, py in points:
            size = 2
            self.canvas.create_rectangle(px-size, py-size, px+size, py+size, fill="red")

    def update(self):
        self.root.update()

class TooltipMarker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-transparentcolor", "black")
        self.canvas = tk.Canvas(self.root, width=80, height=80, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.circle = self.canvas.create_oval(10, 10, 70, 70, outline="lime", width=2)
        
    def show(self, x, y, scale, locked=False):
        color = "cyan" if locked else "lime"
        self.canvas.itemconfig(self.circle, outline=color)
        pos_x, pos_y = int((x / scale) - 40), int((y / scale) - 40)
        self.root.geometry(f"80x80+{pos_x}+{pos_y}")
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()
        try: self.root.update()
        except: pass

def pre_rotate_templates(template):
    # Downscale the template to match the downscaled screen
    t = cv2.resize(template, (0,0), fx=DOWNSCALE_FACTOR, fy=DOWNSCALE_FACTOR)
    rotated_cache = []
    for angle in range(0, 360, ROTATION_STEP):
        (h, w) = t.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(t, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        rotated_cache.append({'img': rotated, 'angle': angle})
    return rotated_cache

def run_app():
    marker = TooltipMarker()
    raw_template = cv2.imread('target.png', cv2.IMREAD_GRAYSCALE)
    if raw_template is None: return
    
    template_cache = pre_rotate_templates(raw_template)
    ahk.run_script("CoordMode, Mouse, Screen")

    # Store counts of how many times each rotation index was the winner
    hit_counts = np.zeros(len(template_cache), dtype=int)
    # Initial search order is just 0 to N
    search_order = list(range(len(template_cache)))
    
    last_drag_time = 0
    target_start_time = None
    
    with mss() as sct:
        full_mon = sct.monitors[1]
        full_w = full_mon['width']
        full_h = full_mon['height']
        scale = (full_w / SCREEN_WIDTH)

        # 1. Calculate the center of the screen
        center_x = full_mon['left'] + (full_w // 2)
        center_y = full_mon['top'] + (full_h // 2)

        # 2. Define area: Center +/- half of DRAG_STEP
        # We use DRAG_STEP directly here as the total width/height
        half_step = DRAG_STEP // 2
        
        search_area = {
            "top": center_y - half_step,
            "left": center_x - half_step,
            "width": DRAG_STEP,
            "height": DRAG_STEP
        }

        # We need this for the marker logic later
        # Since we are no longer using left_offset, we set it to the area's left
        search_left = search_area["left"]
        search_top = search_area["top"]

        # Initialize the scan area visualizer (from previous step)
        area_visual = ScanAreaOverlay(search_area, scale)
        
        while True:
            area_visual.update()
            # Capture only the square
            sct_img = sct.grab(search_area)
            img = np.array(sct_img)
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            small_gray = cv2.resize(gray, (0,0), fx=DOWNSCALE_FACTOR, fy=DOWNSCALE_FACTOR)

            best_val = -1
            best_info = None
            winner_idx = None
            
            # Check templates using the distribution-based search order
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
                # Update distribution: Increment hits and re-sort search order for next frame
                hit_counts[winner_idx] += 1
                search_order = sorted(range(len(template_cache)), key=lambda k: hit_counts[k], reverse=True)

                if target_start_time is None:
                    target_start_time = now
                
                locked_duration = (now - target_start_time) * 1000
                is_locked = locked_duration >= LOCK_DURATION_MS
                
                (max_loc, angle, (h, w)) = best_info
                
                # Logic: Find center in the small image -> upscale to full capture -> add offset -> scale for AHK
                # Coordinates within the square capture
                local_cx = (max_loc[0] + w // 2) / DOWNSCALE_FACTOR
                local_cy = (max_loc[1] + h // 2) / DOWNSCALE_FACTOR
                
                # Global coordinates (important: Add the search box offsets back)
                global_cx = local_cx + search_left
                global_cy = local_cy + search_top
                
                # Show marker and move mouse
                marker.show(global_cx, global_cy, scale, locked=is_locked)

                if is_locked and (now - last_drag_time) * 1000 > COOLDOWN_MS:
                    # Final screen coordinates for AHK
                    ahk_x = int(global_cx / scale)
                    ahk_y = int(global_cy / scale)
                    
                    ahk.mouse_move(ahk_x, ahk_y, speed=1)
                    ahk.mouse_move(1, 0, relative=True) # relative nudge is required to register new
                    ahk.click(button='right', direction='up') # force rmb up if it's down
                    ahk.click(button='left', direction='down')

                    rad = np.deg2rad(-angle % 360)
                    ahk.mouse_move(int(-np.cos(rad)*DRAG_STEP), int(-np.sin(rad)*DRAG_STEP), relative=True, speed=1)
                    ahk.mouse_move(1, 0, relative=True)
                    ahk.click(button='left', direction='up')

                    last_drag_time = time.perf_counter()
                    target_start_time = None
            else:
                target_start_time = None
                marker.hide()

if __name__ == "__main__":
    run_app()