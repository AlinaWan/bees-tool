import ctypes
import threading
from typing import final as sealed
from ctypes import wintypes

user32 = ctypes.windll.user32

# Win32 Constants
WM_HOTKEY = 0x0312
MOD_SHIFT = 0x0004
MOD_CONTROL = 0x0002
VK_F6 = 0x75
VK_F10 = 0x79
VK_ESCAPE = 0x1B

@sealed
class HotkeyListener(threading.Thread):
    def __init__(self, toggle_cb, exit_cb, menu_cb):
        super().__init__(daemon=True)
        self.toggle_cb = toggle_cb
        self.exit_cb = exit_cb
        self.menu_cb = menu_cb

    def run(self):
        # ID 1: F6 (Toggle Logic)
        # ID 2: Shift + Escape (Exit Logic)
        # ID 3: Ctrl + F10 (Menu Toggle)
        user32.RegisterHotKey(None, 1, 0, VK_F6)
        user32.RegisterHotKey(None, 2, MOD_SHIFT, VK_ESCAPE)
        user32.RegisterHotKey(None, 3, MOD_CONTROL, VK_F10)

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                if msg.wParam == 1: self.toggle_cb()
                elif msg.wParam == 2: self.exit_cb()
                elif msg.wParam == 3: self.menu_cb()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        
        user32.UnregisterHotKey(None, 1)
        user32.UnregisterHotKey(None, 2)
        user32.UnregisterHotKey(None, 3)