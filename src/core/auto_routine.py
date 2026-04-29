import threading
import time

from core.config import Config

class AutoRoutineThread(threading.Thread):
    def __init__(self, program):
        super().__init__(daemon=True)
        self.program = program
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        while self.running and not self.program.should_exit:

            if not (Config.AUTO_ROUTINE_ENABLED and self.program.is_active):
                time.sleep(0.05)
                continue

            now = time.perf_counter()

            not_in_minigame = (
                (now - self.program.last_slider_time) * 1000
                > Config.MINIGAME_TIMEOUT_MS
            )

            if self.program.routine_state == "idle" and not_in_minigame:

                key = Config.AUTO_ROUTINE_PATTERN[self.program.routine_index]

                self.program.ahk.key_down(key)
                time.sleep(Config.AUTO_ROUTINE_WALK_TIME_MS / 1000)
                self.program.ahk.key_up(key)

                self.program.routine_index = (
                    self.program.routine_index + 1
                ) % len(Config.AUTO_ROUTINE_PATTERN)

                self.program.ahk.click(button='left', direction='down')
                self.program.routine_lmb_down_time = now

                self.program.routine_state = "holding"

            elif self.program.routine_state == "holding":

                if not not_in_minigame:
                    self.program.routine_state = "idle"

                elif (now - self.program.routine_lmb_down_time) * 1000 > Config.AUTO_ROUTINE_LMB_TIMEOUT_MS:
                    self.program.ahk.click(button='left', direction='up')
                    self.program.routine_state = "idle"

            time.sleep(0.005)