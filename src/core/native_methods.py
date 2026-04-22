import ctypes
from ctypes import wintypes
from typing import final as sealed

@sealed
class NativeMethods:

    _dwmapi = ctypes.WinDLL("dwmapi")
    _kernel32 = ctypes.WinDLL("kernel32")
    _user32 = ctypes.WinDLL("user32")

    _DWMWA_WINDOW_CORNER_PREFERENCE = 33
    _DWMWCP_ROUND = 2

    _FILE_LIST_DIRECTORY = 0x0001
    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _OPEN_EXISTING = 3
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010

    WM_HOTKEY = 0x0312
    MOD_SHIFT = 0x0004
    MOD_CONTROL = 0x0002
    VK_F6 = 0x75
    VK_F10 = 0x79
    VK_ESCAPE = 0x1B

    _dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    _dwmapi.DwmSetWindowAttribute.restype = ctypes.HRESULT

    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    # UI related methods
    @staticmethod
    def apply_rounded_corners(hwnd):
        pref = ctypes.c_int(NativeMethods._DWMWCP_ROUND)

        NativeMethods._dwmapi.DwmSetWindowAttribute(
            hwnd,
            NativeMethods._DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(pref),
            ctypes.sizeof(pref)
        )

    # Directory monitoring related methods
    @staticmethod
    def open_directory_handle(path):
        return NativeMethods._kernel32.CreateFileW(
            path,
            NativeMethods._FILE_LIST_DIRECTORY,
            NativeMethods._FILE_SHARE_READ | NativeMethods._FILE_SHARE_WRITE,
            None,
            NativeMethods._OPEN_EXISTING,
            NativeMethods._FILE_FLAG_BACKUP_SEMANTICS,
            None
        )

    @staticmethod
    def read_directory_changes(handle, buffer, bytes_returned):
        return NativeMethods._kernel32.ReadDirectoryChangesW(
            handle,
            buffer,
            ctypes.sizeof(buffer),
            False,
            NativeMethods._FILE_NOTIFY_CHANGE_LAST_WRITE,
            ctypes.byref(bytes_returned),
            None,
            None
        )

    @staticmethod
    def close_handle(handle):
        NativeMethods._kernel32.CloseHandle(handle)

    # Hotkey related methods
    @staticmethod
    def register_hotkey(hwnd, id, modifiers, key):
        return NativeMethods._user32.RegisterHotKey(hwnd, id, modifiers, key)

    @staticmethod
    def unregister_hotkey(hwnd, id):
        return NativeMethods._user32.UnregisterHotKey(hwnd, id)

    @staticmethod
    def get_message(msg):
        return NativeMethods._user32.GetMessageW(ctypes.byref(msg), None, 0, 0)

    @staticmethod
    def translate_message(msg):
        NativeMethods._user32.TranslateMessage(ctypes.byref(msg))

    @staticmethod
    def dispatch_message(msg):
        NativeMethods._user32.DispatchMessageW(ctypes.byref(msg))