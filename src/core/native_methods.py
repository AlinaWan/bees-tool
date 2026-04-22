import ctypes
from ctypes import wintypes
from typing import final as sealed

@sealed
class NativeMethods:

    _dwmapi = ctypes.WinDLL("dwmapi")
    _kernel32 = ctypes.WinDLL("kernel32")

    _dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    _dwmapi.DwmSetWindowAttribute.restype = ctypes.HRESULT

    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL

    _DWMWA_WINDOW_CORNER_PREFERENCE = 33
    _DWMWCP_ROUND = 2

    _FILE_LIST_DIRECTORY = 0x0001
    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _OPEN_EXISTING = 3
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010

    @staticmethod
    def apply_rounded_corners(hwnd):
        pref = ctypes.c_int(NativeMethods._DWMWCP_ROUND)

        NativeMethods._dwmapi.DwmSetWindowAttribute(
            hwnd,
            NativeMethods._DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(pref),
            ctypes.sizeof(pref)
        )

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