# -*- coding: utf-8 -*-
__version__ = "1.0.0"
__author__ = "Riri"
__license__ = "MIT"

import atexit
import time

import cv2 # type: ignore
import numpy as np # type: ignore
from ahk import AHK # type: ignore
from mss import mss # type: ignore

from core.config import Config
from core.config_handler import ConfigHandler
from core.constants import Constants
from core.native_methods import NativeMethods
from services.file_watcher import FileWatcher
from services.hotkey_listener import HotkeyListener
from ui.menu_overlay import MenuOverlay
from ui.scan_area_overlay import ScanAreaOverlay
from ui.tooltip_marker import TooltipMarker

ahk = AHK()

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

def pre_rotate_templates(template):
    t = cv2.resize(template, (0,0), fx=Config.DOWNSCALE_FACTOR, fy=Config.DOWNSCALE_FACTOR)
    rotated_cache = []
    for angle in range(0, 360, Config.ROTATION_STEP):
        (h, w) = t.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        rotated = cv2.warpAffine(t, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        rotated_cache.append({'img': rotated, 'angle': angle})
    return rotated_cache

def run_app():
    global meter_calibrated, meter_pixels, meter_colors, last_slider_time
    global routine_index, routine_state, routine_lmb_down_time

    # Track changes to these config values specifically
    # because we need to recreate the cache for them
    last_drag_step = Config.DRAG_STEP
    last_rotation_step = Config.ROTATION_STEP
    last_downscale = Config.DOWNSCALE_FACTOR

    marker = TooltipMarker()
    menu = MenuOverlay(ConfigHandler.load_config, ConfigHandler.edit_config, ConfigHandler.open_help)

    listener = HotkeyListener(toggle_logic, exit_logic, menu.toggle)
    listener.start()

    raw_template = cv2.imread(Constants.TARGET_PATH, cv2.IMREAD_GRAYSCALE)
    if raw_template is None: return
    
    template_cache = pre_rotate_templates(raw_template)

    meter_template = cv2.imread(Constants.METER_IMAGE_PATH)
    if meter_template is not None:
        meter_template_gray = cv2.cvtColor(meter_template, cv2.COLOR_BGR2GRAY)
    else:
        meter_template_gray = None

    ahk.run_script("CoordMode, Mouse, Screen")

    hit_counts = np.zeros(len(template_cache), dtype=int)
    search_order = list(range(len(template_cache)))
    
    last_drag_time = 0
    target_start_time = None
    
    with mss() as sct:
        full_mon = sct.monitors[1]
        full_w = full_mon['width']
        full_h = full_mon['height']
        scale = (full_w / Constants.SCREEN_WIDTH)

        center_x = full_mon['left'] + (full_w // 2)
        center_y = full_mon['top'] + (full_h // 2)

        half_step = Config.DRAG_STEP // 2
        
        search_area = {
            "top": center_y - half_step,
            "left": center_x - half_step,
            "width": Config.DRAG_STEP,
            "height": Config.DRAG_STEP
        }

        search_left = search_area["left"]
        search_top = search_area["top"]

        area_visual = ScanAreaOverlay(search_area, scale)
        
        while not should_exit:
            # Recache only when changed
            # search_area is dependent on DRAG_STEP
            if Config.DRAG_STEP != last_drag_step:
                half_step = Config.DRAG_STEP // 2
                search_area = {
                    "top": center_y - half_step,
                    "left": center_x - half_step,
                    "width": Config.DRAG_STEP,
                    "height": Config.DRAG_STEP
                }
                search_left, search_top = search_area["left"], search_area["top"]
                area_visual.update_dimensions(search_area, scale)
                last_drag_step = Config.DRAG_STEP
                print(f"[App::Cache] Search area resized to {Config.DRAG_STEP}")

            # template cache is dependent on ROTATION_STEP and DOWNSCALE_FACTOR
            if Config.ROTATION_STEP != last_rotation_step or Config.DOWNSCALE_FACTOR != last_downscale:
                template_cache = pre_rotate_templates(raw_template)
                # Reset search order/counts because the list size might have changed
                hit_counts = np.zeros(len(template_cache), dtype=int)
                search_order = list(range(len(template_cache)))
                
                last_rotation_step = Config.ROTATION_STEP
                last_downscale = Config.DOWNSCALE_FACTOR
                print(f"[App::Cache] Template cache rebuilt (Step: {Config.ROTATION_STEP}, Scale: {Config.DOWNSCALE_FACTOR})")

            area_visual.update(is_active)
            if menu.alive:
                menu.update()

            now = time.perf_counter()

            # Auto Release Calibration
            if Config.AUTO_RELEASE_ENABLED and not meter_calibrated and meter_template_gray is not None:
                right_half = {
                    "top": 0,
                    "left": Constants.SCREEN_WIDTH//2,
                    "width": Constants.SCREEN_WIDTH//2,
                    "height": Constants.SCREEN_HEIGHT
                }

                frame = np.array(sct.grab(right_half))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)

                res = cv2.matchTemplate(gray, meter_template_gray, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)

                if max_val >= Config.AUTO_RELEASE_CONFIDENCE:
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

            # Auto Release Check
            time_since_last_slider = (now - last_slider_time) * 1000

            if (
                Config.AUTO_RELEASE_ENABLED
                and meter_calibrated
                and time_since_last_slider > Config.MINIGAME_TIMEOUT_MS
                and len(meter_pixels) == 4
            ):
                
                check_region = {
                    "top": meter_target_y,
                    "left": min(meter_pixels),
                    "width": (max(meter_pixels) - min(meter_pixels)) + 1,
                    "height": Config.SEARCH_DEPTH
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
                        if np.any(np.all(diff <= Config.AUTO_RELEASE_TOLERANCE, axis=1)):
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

            # Auto Routine
            if Config.AUTO_ROUTINE_ENABLED and is_active:

                not_in_minigame = time_since_last_slider > Config.MINIGAME_TIMEOUT_MS

                if routine_state == "idle" and not_in_minigame:

                    key = Config.AUTO_ROUTINE_PATTERN[routine_index]
                    ahk.key_down(key)
                    time.sleep(Config.AUTO_ROUTINE_WALK_TIME_MS / 1000)
                    ahk.key_up(key)

                    routine_index = (routine_index + 1) % len(Config.AUTO_ROUTINE_PATTERN)

                    ahk.click(button='left', direction='down')
                    routine_lmb_down_time = now

                    routine_state = "holding"

                elif routine_state == "holding":

                    if not not_in_minigame:
                        routine_state = "idle"

                    elif (now - routine_lmb_down_time) * 1000 > Config.AUTO_ROUTINE_LMB_TIMEOUT_MS:
                        ahk.click(button='left', direction='up')
                        routine_state = "idle"

            if not is_active:
                marker.hide()
                target_start_time = None
                time.sleep(0.1)
                continue

            sct_img = sct.grab(search_area)
            img = np.array(sct_img)
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            small_gray = cv2.resize(gray, (0,0), fx=Config.DOWNSCALE_FACTOR, fy=Config.DOWNSCALE_FACTOR)

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
            if best_val > Config.CONFIDENCE_THRESHOLD:
                last_slider_time = now

                hit_counts[winner_idx] += 1
                search_order = sorted(range(len(template_cache)), key=lambda k: hit_counts[k], reverse=True)

                if target_start_time is None:
                    target_start_time = now
                
                locked_duration = (now - target_start_time) * 1000
                is_locked = locked_duration >= Config.LOCK_DURATION_MS
                
                (max_loc, angle, (h, w)) = best_info
                
                local_cx = (max_loc[0] + w // 2) / Config.DOWNSCALE_FACTOR
                local_cy = (max_loc[1] + h // 2) / Config.DOWNSCALE_FACTOR
                
                global_cx = local_cx + search_left
                global_cy = local_cy + search_top

                rad = np.deg2rad(-angle % 360)
                dest_x = global_cx - (np.cos(rad) * Config.DRAG_STEP)
                dest_y = global_cy - (np.sin(rad) * Config.DRAG_STEP)
                
                in_bounds = (
                    (search_left - Config.BOUNDARY_MARGIN) <= dest_x <= (search_left + search_area["width"] + Config.BOUNDARY_MARGIN) and
                    (search_top - Config.BOUNDARY_MARGIN) <= dest_y <= (search_top + search_area["height"] + Config.BOUNDARY_MARGIN)
                )
                
                marker.show(global_cx, global_cy, scale, angle=angle, confidence=best_val, locked=is_locked, in_bounds=in_bounds, drag_to=(dest_x, dest_y), winner_idx=winner_idx)

                if in_bounds and is_locked and (now - last_drag_time) * 1000 > Config.COOLDOWN_MS:
                    x = int(global_cx / scale)
                    y = int(global_cy / scale)
                    
                    ahk.click(button='right', direction='up')
                    ahk.mouse_move(x, y, speed=1)
                    ahk.mouse_move(1, 0, relative=True)
                    ahk.click(button='left', direction='down')

                    ahk.mouse_move(int(-np.cos(rad)*Config.DRAG_STEP), int(-np.sin(rad)*Config.DRAG_STEP), relative=True, speed=1)
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
    FileWatcher.stop_active_watcher()

atexit.register(cleanup)

if __name__ == "__main__":
    try:
        NativeMethods.set_process_dpi_awareness_context(-4)
    except Exception:
        pass

    try:
        run_app()
    except cv2.error as e:
        if "error: (-215:Assertion failed)" in str(e):
            NativeMethods.message_box(
                "OpenCV raised Error -215 (Assertion failed) during runtime.\n\n" +
                "This is usually because DRAG_STEP resulted in a search area " +
                "that is smaller than the template size. Try increasing DRAG_STEP, " + 
                "decreasing DOWNSCALE_FACTOR, or using a smaller template image.",
                "Fatal Error",
                NativeMethods.MB_OK | NativeMethods.MB_ICONERROR
            )
            raise # raise directly so we get a nicely colored traceback instead of plain text
        else:
            NativeMethods.message_box(
                f"An OpenCV error occurred: {e}",
                "Fatal Error",
                NativeMethods.MB_OK | NativeMethods.MB_ICONERROR
            )
            raise

    except Exception as e:
        NativeMethods.message_box(
            f"An unexpected error occurred: {e}",
            "Fatal Error",
            NativeMethods.MB_OK | NativeMethods.MB_ICONERROR
        )
        raise

    finally:
        cleanup()
