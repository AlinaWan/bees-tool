import threading
from typing import final as sealed

from core.config import Config
from core.native_methods import NativeMethods

@sealed
class HotkeyListener(threading.Thread):
    def __init__(self, toggle_cb, exit_cb, menu_cb, cancel_shutdown_cb):
        super().__init__(daemon=True)
        self.toggle_cb = toggle_cb
        self.exit_cb = exit_cb
        self.menu_cb = menu_cb
        self.cancel_shutdown_cb = cancel_shutdown_cb
        
        self.status_event = threading.Event()
        self.success = False

    def run(self):
        # ID 1: F6 (Toggle Logic)
        # ID 2: Shift + Escape (Exit Logic)
        # ID 3: Ctrl + F10 (Menu Toggle)
        # ID 4: Escape (Cancel Shutdown)
        results = [
            NativeMethods.register_hotkey(None, 1, Config.TOGGLE_MOD, Config.TOGGLE_KEY),
            NativeMethods.register_hotkey(None, 2, Config.EXIT_MOD, Config.EXIT_KEY),
            NativeMethods.register_hotkey(None, 3, Config.MENU_MOD, Config.MENU_KEY),
            NativeMethods.register_hotkey(None, 4, Config.CANCEL_SHUTDOWN_MOD, Config.CANCEL_SHUTDOWN_KEY)
        ]

        if not all(results):
            self.success = False
            self.status_event.set()
            return

        self.success = True
        self.status_event.set()

        msg = NativeMethods.create_msg()
        while NativeMethods.get_message(msg) != 0:
            if msg.message == NativeMethods.WM_HOTKEY:
                if msg.wParam == 1:
                    self.toggle_cb()
                elif msg.wParam == 2:
                    self.exit_cb()
                elif msg.wParam == 3:
                    self.menu_cb()
                elif msg.wParam == 4:
                    self.cancel_shutdown_cb()
            NativeMethods.translate_message(msg)
            NativeMethods.dispatch_message(msg)
        
        for i in range(1, 5):
            NativeMethods.unregister_hotkey(None, i)
