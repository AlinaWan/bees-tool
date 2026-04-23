import json
import os
import subprocess
import threading
import webbrowser
from datetime import datetime, timezone
from tkinter import filedialog
from typing import final as sealed

from core.config import Config
from core.constants import Constants
from services.file_watcher import FileWatcher
from utils.math_evaluator import MathEvaluator

current_config_path = None
config_data = None

evaluator = MathEvaluator({
    "SCREEN_WIDTH": Constants.SCREEN_WIDTH,
    "SCREEN_HEIGHT": Constants.SCREEN_HEIGHT
})

@sealed
class ConfigHandler:

    @staticmethod
    def apply_config(data):
        s = data["slider_settings"]
        Config.CONFIDENCE_THRESHOLD = evaluator.evaluate(s["confidence_threshold"])
        Config.ROTATION_STEP = evaluator.evaluate(s["rotation_step"])
        Config.DRAG_STEP = evaluator.evaluate(s["drag_step"])
        Config.COOLDOWN_MS = evaluator.evaluate(s["cooldown_ms"])
        Config.LOCK_DURATION_MS = evaluator.evaluate(s["lock_duration_ms"])
        Config.DOWNSCALE_FACTOR = evaluator.evaluate(s["downscale_factor"])
        Config.BOUNDARY_MARGIN = evaluator.evaluate(s["boundary_margin"])
        Config.MINIGAME_TIMEOUT_MS = evaluator.evaluate(s["minigame_timeout_ms"])

        m = data["meter_settings"]
        Config.AUTO_RELEASE_ENABLED = evaluator.evaluate(m["auto_release_enabled"])
        Config.AUTO_RELEASE_TOLERANCE = evaluator.evaluate(m["auto_release_tolerance"])
        Config.AUTO_RELEASE_CONFIDENCE = evaluator.evaluate(m["auto_release_confidence"])
        Config.AUTO_RELEASE_Y_OFFSET = evaluator.evaluate(m["auto_release_y_offset"])
        Config.SEARCH_DEPTH = evaluator.evaluate(m["search_depth"])

        r = data["routine_settings"]
        Config.AUTO_ROUTINE_ENABLED = evaluator.evaluate(r["auto_routine_enabled"])
        Config.AUTO_ROUTINE_PATTERN = tuple(r["pattern"])
        Config.AUTO_ROUTINE_WALK_TIME_MS = evaluator.evaluate(r["walk_time_ms"])
        Config.AUTO_ROUTINE_LMB_TIMEOUT_MS = evaluator.evaluate(r["lmb_timeout_ms"])

        if Config.AUTO_ROUTINE_ENABLED:
            Config.AUTO_RELEASE_ENABLED = True

    @staticmethod
    def _build_current_config():
        return {
            "metadata": {
                "custom_info": {
                    "author": "",
                    "net": "",
                    "flower": ""
                },
                "app_info": {
                    "version": "1.0.0",
                    "schema": 1,
                    "created": datetime.now(timezone.utc).isoformat(),
                    "description": [
                        "---------------------- Bees Tool Configuration ----------------------",
                        " Feel free to add your own notes in the 'custom_info' section above! ",
                        " You can write values as expressions based on screen dimensions with ",
                        " variables SCREEN_WIDTH and SCREEN_HEIGHT (e.g., SCREEN_HEIGHT / 2). ",
                        " Supported operators: +, -, *, /, //, %, **, +x, -x and parentheses. ",
                        "---------------------------------------------------------------------"
                ]
                }
            },
            "slider_settings": {
                "confidence_threshold": Config.CONFIDENCE_THRESHOLD,
                "rotation_step": Config.ROTATION_STEP,
                "drag_step": Config.DRAG_STEP,
                "cooldown_ms": Config.COOLDOWN_MS,
                "lock_duration_ms": Config.LOCK_DURATION_MS,
                "downscale_factor": Config.DOWNSCALE_FACTOR,
                "boundary_margin": Config.BOUNDARY_MARGIN,
                "minigame_timeout_ms": Config.MINIGAME_TIMEOUT_MS
            },
            "meter_settings": {
                "auto_release_enabled": Config.AUTO_RELEASE_ENABLED,
                "auto_release_tolerance": Config.AUTO_RELEASE_TOLERANCE,
                "auto_release_confidence": Config.AUTO_RELEASE_CONFIDENCE,
                "auto_release_y_offset": Config.AUTO_RELEASE_Y_OFFSET,
                "search_depth": Config.SEARCH_DEPTH
            },
            "routine_settings": {
                "auto_routine_enabled": Config.AUTO_ROUTINE_ENABLED,
                "pattern": list(Config.AUTO_ROUTINE_PATTERN),
                "walk_time_ms": Config.AUTO_ROUTINE_WALK_TIME_MS,
                "lmb_timeout_ms": Config.AUTO_ROUTINE_LMB_TIMEOUT_MS
            }
        }

    @staticmethod
    def _reload_from_disk(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            ConfigHandler.apply_config(data)
            print(f"[ConfigHandler::Reload] Live-reloaded: {os.path.basename(path)}")
        except Exception as e:
            print(f"[ConfigHandler::Reload] Reload error: {e}")

    @staticmethod
    def load_config():
        global current_config_path, config_data

        path = filedialog.askopenfilename(
            initialdir=Constants.SCRIPT_DIR,
            filetypes=[("JSON Config", "*.json")]
        )

        if not path:
            return

        # this prevents multiple threads from watching different files at once.
        FileWatcher.stop_active_watcher()

        # load once immediately
        ConfigHandler._reload_from_disk(path)
        current_config_path = path

        # this ensures that if the user edits the NEW file in Notepad, it updates live.
        FileWatcher._thread = threading.Thread(
            target=FileWatcher.watch_file_changes,
            args=(path, ConfigHandler._reload_from_disk),
            daemon=True
        )
        FileWatcher._thread.start()

    @staticmethod
    def edit_config():
        global current_config_path, config_data

        # 1. If no file is loaded, create one first
        if not current_config_path:
            timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
            default_name = f"Bees_Tool_Config_{timestamp}.json"

            path = filedialog.asksaveasfilename(
                initialdir=Constants.SCRIPT_DIR,
                initialfile=default_name,
                defaultextension=".json",
                filetypes=[("JSON Config", "*.json")]
            )

            if not path:
                return # User cancelled the dialog

            # 2. Write the current script settings to the new file
            config = ConfigHandler._build_current_config()
            with open(path, "w") as f:
                json.dump(config, f, indent=4)

            # 3. Point the script to this new file
            current_config_path = path
            print(f"[ConfigHandler::Edit] Created and loaded config: {path}")

        # 4. Open the file (either the existing one or the one just created) in Notepad
        subprocess.Popen(['notepad.exe', current_config_path])
        print(f"[ConfigHandler::Edit] Opened {current_config_path} in Notepad.")

        # 5. Ensure the watcher is running so edits are applied live
        if FileWatcher._thread is None or not FileWatcher._thread.is_alive():
            FileWatcher._cts.clear()
            FileWatcher._thread = threading.Thread(
                target=FileWatcher.watch_file_changes,
                args=(current_config_path, ConfigHandler._reload_from_disk),
                daemon=True
            )
            FileWatcher._thread.start()

    @staticmethod
    def open_help():
        github_url = "https://github.com/AlinaWan/bees-tool#readme"
        webbrowser.open(github_url)
