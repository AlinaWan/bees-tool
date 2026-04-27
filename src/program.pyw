# -*- coding: utf-8 -*-
__version__ = "1.0.0"
__author__ = "Riri"
__license__ = "MIT"

import atexit
import threading
import time
from typing import final as sealed

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
from services.process_monitor import ProcessMonitor
from services.recache_manager import RecacheManager
from services.roblox_log_monitor import RobloxLogMonitor
from ui.menu_overlay import MenuOverlay
from ui.scan_area_overlay import ScanAreaOverlay
from ui.tooltip_marker import TooltipMarker
from utils.process_locator import ProcessLocator
from utils.safe_message_box import SafeMessageBox
from utils.system_controller import SystemController

@sealed
class Program:
    def __init__(self):
        self.ahk = AHK()
        self.menu = None
        self.process_monitor = ProcessMonitor()
        self.log_monitor = RobloxLogMonitor()
        self.system_controller = SystemController()
        self.hotkey_listener = None

        self.mutex_handle = None

        self.is_active = False
        self.should_exit = False

        self.meter_target_y = None
        self.meter_scan_plan = None
        self.meter_calibrated = False
        self.meter_pixels = []
        self.meter_colors = []
        self.last_slider_time = time.perf_counter()

        self.routine_index = 0
        self.routine_state = "idle"
        self.routine_lmb_down_time = 0

        self._hotkey_register_lock = threading.Lock()
        self._hotkey_registering = False
        self._cache_lock = threading.Lock()
        self.recache_manager = RecacheManager()
        ConfigHandler.set_recache_manager(self.recache_manager)

        # values that need recache
        self.last_drag_step = Config.DRAG_STEP
        self.last_rotation_step = Config.ROTATION_STEP
        self.last_downscale = Config.DOWNSCALE_FACTOR
        self.last_hotkey_config = {
            "toggle": (Config.TOGGLE_MOD, Config.TOGGLE_KEY),
            "exit": (Config.EXIT_MOD, Config.EXIT_KEY),
            "menu": (Config.MENU_MOD, Config.MENU_KEY),
            "cancel": (Config.CANCEL_SHUTDOWN_MOD, Config.CANCEL_SHUTDOWN_KEY)
        }

        # runtime cache
        self.template_cache = None
        self.hit_counts = None
        self.search_order = None

        # register recache hook
        self.recache_manager.register(self._recache)

    def toggle_logic(self):
        self.is_active = not self.is_active

        if self.is_active:
            self.routine_index = 0
            self.routine_state = "idle"

    def exit_logic(self):
        self.should_exit = True

    def _on_roblox_disconnect(self):
        if Config.EXIT_ON_ROBLOX_DISCONNECT:
            self.should_exit = True

        if Config.SHUTDOWN_ON_ROBLOX_DISCONNECT:
            self.system_controller.start_shutdown(
                15,
                "Shutting down.\n\nPress Ctrl+Shift+X to abort."
            )

    def _on_roblox_kill(self):
        if Config.EXIT_ON_ROBLOX_KILL:
            self.should_exit = True

        if Config.SHUTDOWN_ON_ROBLOX_KILL:
            self.system_controller.start_shutdown(
                15,
                "Shutting down.\n\nPress Ctrl+Shift+X to abort."
            )

    def cancel_shutdown(self):
        self.system_controller.cancel_shutdown()

    @staticmethod
    def pre_rotate_templates(template):
        t = cv2.resize(template, (0,0), fx=Config.DOWNSCALE_FACTOR, fy=Config.DOWNSCALE_FACTOR)
        rotated_cache = []
        for angle in range(0, 360, Config.ROTATION_STEP):
            (h, w) = t.shape[:2]
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            rotated = cv2.warpAffine(t, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
            rotated_cache.append({'img': rotated, 'angle': angle})
        return rotated_cache

    def _handle_process_monitor_retry(self):
        def on_result(result):
            if result == 4:  # Retry
                if not (Config.EXIT_ON_ROBLOX_KILL or Config.SHUTDOWN_ON_ROBLOX_KILL):
                    print("[Program::Process] Retry ignored (disabled in config).")
                    return

                print("[Program::Recache] Retrying process detection...")
                self._try_start_process_monitor()
            else:
                print("[Program::Recache] Monitoring skipped by user.")

        SafeMessageBox.show_message_box_async(
            "Failed to get Roblox process ID for process monitoring.\n\n"
            "Please open Roblox and click 'Retry' while the game is running, "
            "or 'Cancel' to skip process monitoring entirely.",
            "Process Monitoring Warning",
            NativeMethods.MB_RETRYCANCEL | NativeMethods.MB_ICONWARNING,
            on_result
        )

    def _try_start_process_monitor(self):
        if not (Config.EXIT_ON_ROBLOX_KILL or Config.SHUTDOWN_ON_ROBLOX_KILL):
            print("[Program::Process] Monitoring disabled via config.")
            return

        pid = ProcessLocator.get_process_pid("RobloxPlayerBeta.exe", True)

        if pid:
            self.process_monitor.start(pid, on_kill=self._on_roblox_kill)
        else:
            self._handle_process_monitor_retry()

    def _handle_hotkey_retry(self):
        def on_result(result):
            if result == 4:  # Retry
                print("[Program::Hotkey] Retrying hotkey registration...")
                self._update_hotkey_registration()
            else:
                print("[Program::Hotkey] User skipped hotkey retry.")

        SafeMessageBox.show_message_box_async(
            "Failed to register one or more hotkeys.\n\n"
            "This is usually because another program is already using them. "
            "Please close conflicting apps or change your hotkeys and click 'Retry', or 'Cancel' to continue with missing keys.",
            "Hotkey Warning",
            NativeMethods.MB_RETRYCANCEL | NativeMethods.MB_ICONWARNING,
            on_result
        )

    def _recache(self):
        # rebuild template cache
        with self._cache_lock:
            self.template_cache = self.pre_rotate_templates(self.raw_template)
            self.hit_counts = np.zeros(len(self.template_cache), dtype=int)
            self.search_order = list(range(len(self.template_cache)))

            self.meter_calibrated = False
            self.meter_target_y = None
            self.meter_scan_plan = None

            self.last_drag_step = Config.DRAG_STEP
            self.last_rotation_step = Config.ROTATION_STEP
            self.last_downscale = Config.DOWNSCALE_FACTOR

            self.half_step = Config.DRAG_STEP // 2

            self.search_area = {
                "top": self.center_y - self.half_step,
                "left": self.center_x - self.half_step,
                "width": Config.DRAG_STEP,
                "height": Config.DRAG_STEP
            }

            self.search_left = self.search_area["left"]
            self.search_top = self.search_area["top"]

            if hasattr(self, "area_visual"):
                self.area_visual.update_dimensions(self.search_area, self.scale)

            log_needed = Config.EXIT_ON_ROBLOX_DISCONNECT or Config.SHUTDOWN_ON_ROBLOX_DISCONNECT

            if log_needed:
                if not self.log_monitor.is_running:
                    self.log_monitor.start({
                        r"\[FLog::Network\] Time to disconnect replication data: ([\d\.]+)":
                        lambda _: self._on_roblox_disconnect()
                    })
            else:
                if self.log_monitor.is_running:
                    self.log_monitor.stop()

            proc_needed = Config.EXIT_ON_ROBLOX_KILL or Config.SHUTDOWN_ON_ROBLOX_KILL

            if proc_needed:
                if not self.process_monitor.is_running:
                    self._try_start_process_monitor()
            else:
                if self.process_monitor.is_running:
                    self.process_monitor.stop()

            self._update_hotkey_registration()

            print("[Program::Recache] Cache rebuilt")

    def _update_hotkey_registration(self):
        if self._hotkey_registering:
            print("[Program::Hotkey] Registration already in progress, skipping...")
            return

        with self._hotkey_register_lock:
            self._hotkey_registering = True

            try:
                current_config = {
                    "toggle": (Config.TOGGLE_MOD, Config.TOGGLE_KEY),
                    "exit": (Config.EXIT_MOD, Config.EXIT_KEY),
                    "menu": (Config.MENU_MOD, Config.MENU_KEY),
                    "cancel": (Config.CANCEL_SHUTDOWN_MOD, Config.CANCEL_SHUTDOWN_KEY)
                }

                if current_config == self.last_hotkey_config and self.hotkey_listener is not None:
                    return

                print("[Program::Hotkey] Re-registering hotkeys...")

                # stop old listener safely
                if self.hotkey_listener:
                    self.hotkey_listener.stop()
                    if self.hotkey_listener.is_alive():
                        self.hotkey_listener.join(timeout=1.0)

                # attempt registration
                self.hotkey_listener = HotkeyListener(
                    self.toggle_logic,
                    self.exit_logic,
                    self.menu.toggle,
                    self.cancel_shutdown
                )
                self.hotkey_listener.start()

                # wait briefly for result
                self.hotkey_listener.status_event.wait(timeout=1.0)

                if self.hotkey_listener.success:
                    self.last_hotkey_config = current_config
                    return

                # failure → async retry (NON-BLOCKING)
                self._handle_hotkey_retry()

            finally:
                self._hotkey_registering = False

    def run(self):
        marker = TooltipMarker()
        self.menu = MenuOverlay(ConfigHandler.load_config, ConfigHandler.edit_config, ConfigHandler.open_help)

        self.raw_template = cv2.imread(Constants.TARGET_PATH, cv2.IMREAD_GRAYSCALE)
        if self.raw_template is None:
            raise Exception(f"Can't open/read file: {Constants.TARGET_PATH}\n\nCheck file path/integrity.")

        meter_template = cv2.imread(Constants.METER_IMAGE_PATH)
        if meter_template is None:
            raise Exception(f"Can't open/read file: {Constants.METER_IMAGE_PATH}\n\nCheck file path/integrity.")
        else:
            meter_template_gray = cv2.cvtColor(meter_template, cv2.COLOR_BGR2GRAY)

        self.ahk.run_script("CoordMode, Mouse, Screen")
    
        last_drag_time = 0
        target_start_time = None
    
        with mss() as sct:
            full_mon = sct.monitors[1]

            self.full_w = full_mon['width']
            self.full_h = full_mon['height']

            self.center_x = full_mon['left'] + (self.full_w // 2)
            self.center_y = full_mon['top'] + (self.full_h // 2)
            self.scale = (self.full_w / Constants.SCREEN_WIDTH)

            self._recache()

            self.area_visual = ScanAreaOverlay(self.search_area, self.scale)
        
            while not self.should_exit:
                self.recache_manager.flush()
                self.area_visual.update(self.is_active)
                if self.menu.alive:
                    self.menu.update()

                now = time.perf_counter()

                # Auto Release Calibration
                if Config.AUTO_RELEASE_ENABLED and not self.meter_calibrated and meter_template_gray is not None:
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
                            top_y = max_loc[1] + Config.AUTO_RELEASE_Y_OFFSET
                            center_x = max_loc[0] + w//2
                            start_x = center_x - 2
                
                            scan_plan = [] # (x_offset, color_bgr)
                        
                            for i in range(4):
                                px = start_x + i
                                py = top_y

                                screen_x = right_half["left"] + px
                                b, g, r = meter_template[py - max_loc[1], px - max_loc[0]][:3]

                                scan_plan.append((
                                    screen_x,
                                    (int(b), int(g), int(r))
                                ))
                            
                            self.meter_target_y = top_y 
                            self.meter_scan_plan = scan_plan
                            self.meter_calibrated = True

                # Auto Release Check
                time_since_last_slider = (now - self.last_slider_time) * 1000

                if (
                    Config.AUTO_RELEASE_ENABLED
                    and self.meter_calibrated
                    and time_since_last_slider > Config.MINIGAME_TIMEOUT_MS
                ):

                    check_region = {
                        "top": self.meter_target_y,
                        "left": min(x for x, _ in self.meter_scan_plan),
                        "width": (max(x for x, _ in self.meter_scan_plan) - min(x for x, _ in self.meter_scan_plan)) + 1,
                        "height": Config.SEARCH_DEPTH
                    }

                    roi = sct.grab(check_region)

                    buf = roi.raw
                    width = roi.width
                    height = roi.height
                    stride = width * 4

                    matches_found = 0

                    tol = Config.AUTO_RELEASE_TOLERANCE
                    buf_local = buf

                    scan_plan = self.meter_scan_plan
                    if not scan_plan:
                        continue

                    for x_global, (tb, tg, tr) in scan_plan:

                        x = x_global - check_region["left"]
                        if x < 0 or x >= width:
                            continue

                        found = False

                        for y in range(height):
                            offset = y * stride + x * 4

                            b = buf_local[offset]
                            g = buf_local[offset + 1]
                            r = buf_local[offset + 2]

                            if (
                                -tol <= (b - tb) <= tol and
                                -tol <= (g - tg) <= tol and
                                -tol <= (r - tr) <= tol
                            ):
                                found = True
                                break

                        if found:
                            matches_found += 1

                    if matches_found == 4 and self.is_active:
                        self.ahk.click(button='left', direction='up')
                        time.sleep(0.05)

                    # UI debug overlay
                    cx = self.meter_scan_plan[0][0]
                    cy = self.meter_target_y

                    local_x = cx - self.search_left
                    local_y = cy - self.search_top
                    vis_x = int(local_x / self.scale)
                    vis_y = int(local_y / self.scale)

                    if (
                        0 <= vis_x <= self.area_visual.canvas.winfo_width()
                        and 0 <= vis_y <= self.area_visual.canvas.winfo_height()
                    ):
                        self.area_visual.draw_release_bars(vis_x, vis_y)

                # Auto Routine
                if Config.AUTO_ROUTINE_ENABLED and self.is_active:

                    not_in_minigame = time_since_last_slider > Config.MINIGAME_TIMEOUT_MS

                    if self.routine_state == "idle" and not_in_minigame:

                        key = Config.AUTO_ROUTINE_PATTERN[self.routine_index]
                        self.ahk.key_down(key)
                        time.sleep(Config.AUTO_ROUTINE_WALK_TIME_MS / 1000)
                        self.ahk.key_up(key)

                        self.routine_index = (self.routine_index + 1) % len(Config.AUTO_ROUTINE_PATTERN)

                        self.ahk.click(button='left', direction='down')
                        self.routine_lmb_down_time = now

                        self.routine_state = "holding"

                    elif self.routine_state == "holding":

                        if not not_in_minigame:
                            self.routine_state = "idle"

                        elif (now - self.routine_lmb_down_time) * 1000 > Config.AUTO_ROUTINE_LMB_TIMEOUT_MS:
                            self.ahk.click(button='left', direction='up')
                            self.routine_state = "idle"

                if not self.is_active:
                    marker.hide()
                    target_start_time = None
                    time.sleep(0.1)
                    continue

                sct_img = sct.grab(self.search_area)
                img = np.array(sct_img)
                gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
                small_gray = cv2.resize(gray, (0,0), fx=Config.DOWNSCALE_FACTOR, fy=Config.DOWNSCALE_FACTOR)

                best_val = -1
                best_info = None
                winner_idx = None

                with self._cache_lock:
                    template_cache = self.template_cache
                    search_order = self.search_order
                    hit_counts = self.hit_counts

                if not template_cache or not search_order:
                    continue

                for i in search_order:
                    item = template_cache[i]
                    res = cv2.matchTemplate(small_gray, item['img'], cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(res)
                    if max_val > best_val:
                        best_val = max_val
                        best_info = (max_loc, item['angle'], item['img'].shape)
                        winner_idx = i
                        if best_val > 0.95: break

                if best_val > Config.CONFIDENCE_THRESHOLD:
                    self.last_slider_time = now

                    with self._cache_lock:
                        if self.hit_counts is hit_counts:
                            hit_counts[winner_idx] += 1
                            self.search_order = sorted(
                                range(len(hit_counts)),
                                key=lambda k: hit_counts[k],
                                reverse=True
                            )

                    if target_start_time is None:
                        target_start_time = now
                
                    locked_duration = (now - target_start_time) * 1000
                    is_locked = locked_duration >= Config.LOCK_DURATION_MS
                
                    (max_loc, angle, (h, w)) = best_info
                
                    local_cx = (max_loc[0] + w // 2) / Config.DOWNSCALE_FACTOR
                    local_cy = (max_loc[1] + h // 2) / Config.DOWNSCALE_FACTOR
                
                    global_cx = local_cx + self.search_left
                    global_cy = local_cy + self.search_top

                    rad = np.deg2rad(-angle % 360)
                    dest_x = global_cx - (np.cos(rad) * Config.DRAG_STEP)
                    dest_y = global_cy - (np.sin(rad) * Config.DRAG_STEP)
                
                    in_bounds = (
                        (self.search_left - Config.BOUNDARY_MARGIN) <= dest_x <= (self.search_left + self.search_area["width"] + Config.BOUNDARY_MARGIN) and
                        (self.search_top - Config.BOUNDARY_MARGIN) <= dest_y <= (self.search_top + self.search_area["height"] + Config.BOUNDARY_MARGIN)
                    )
                
                    marker.show(global_cx, global_cy, self.scale, angle=angle, confidence=best_val, locked=is_locked, in_bounds=in_bounds, drag_to=(dest_x, dest_y), winner_idx=winner_idx)

                    if in_bounds and is_locked and (now - last_drag_time) * 1000 > Config.COOLDOWN_MS:
                        x = int(global_cx / self.scale)
                        y = int(global_cy / self.scale)
                    
                        self.ahk.click(button='right', direction='up')
                        self.ahk.mouse_move(x, y, speed=1)
                        self.ahk.mouse_move(1, 0, relative=True)
                        self.ahk.click(button='left', direction='down')

                        self.ahk.mouse_move(int(-np.cos(rad)*Config.DRAG_STEP), int(-np.sin(rad)*Config.DRAG_STEP), relative=True, speed=1)
                        self.ahk.mouse_move(1, 0, relative=True)
                        self.ahk.click(button='left', direction='up')

                        last_drag_time = time.perf_counter()
                        target_start_time = None
                else:
                    target_start_time = None
                    marker.hide()

        self.area_visual.root.destroy()
        marker.root.destroy()

    def cleanup(self):
        if self.hotkey_listener and self.hotkey_listener.is_alive():
            self.hotkey_listener.stop()

        if hasattr(self, "log_monitor") and self.log_monitor:
            self.log_monitor.stop()

        from core.config_handler import config_watcher
        if config_watcher:
            config_watcher.stop()

        if hasattr(self, "process_monitor") and self.process_monitor:
            self.process_monitor.stop()

        if self.mutex_handle:
            NativeMethods.release_mutex(self.mutex_handle)
            NativeMethods.close_handle(self.mutex_handle)

    @staticmethod
    def main():
        # This should be called BEFORE ANYTHING ELSE
        try:
            NativeMethods.set_process_dpi_awareness_context(-4)
        except Exception:
            pass

        mutex, is_first_instance = NativeMethods.create_single_instance_mutex(f"Global\\{Constants.GUID}")
        if not is_first_instance:
            SafeMessageBox.show_message_box_sync(
                "Another instance of Bees Tool is already running.",
                "Already Running",
                NativeMethods.MB_OK | NativeMethods.MB_ICONINFORMATION
            )
            raise SystemExit(0)

        app = Program()
        app.mutex_handle = mutex
        atexit.register(app.cleanup)

        try:
            app.run()
        except cv2.error as e:
            if "error: (-215:Assertion failed)" in str(e):
                SafeMessageBox.show_message_box_sync(
                    "OpenCV raised Error -215 (Assertion failed) during runtime.\n\n" +
                    "This is usually because DRAG_STEP resulted in a search area " +
                    "that is smaller than the template size. Try increasing DRAG_STEP, " + 
                    "decreasing DOWNSCALE_FACTOR, or using a smaller template image.\n\n" +
                    "The program will now close.",
                    "Fatal Error",
                    NativeMethods.MB_OK | NativeMethods.MB_ICONERROR
                )
                raise # raise directly so we get a nicely colored traceback instead of plain text
            else:
                SafeMessageBox.show_message_box_sync(
                    "An OpenCV error occurred during runtime:\n\n" +
                    f"{e}\n\n" +
                    "The program will now close.",
                    "Fatal Error",
                    NativeMethods.MB_OK | NativeMethods.MB_ICONERROR
                )
                raise

        except Exception as e:
            SafeMessageBox.show_message_box_sync(
                "An unexpected error occurred during runtime:\n\n" +
                f"{e}\n\n" +
                "The program will now close.",
                "Fatal Error",
                NativeMethods.MB_OK | NativeMethods.MB_ICONERROR
            )
            raise

if __name__ == "__main__":
    Program.main()