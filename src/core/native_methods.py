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

    _FILE_FLAG_OVERLAPPED = 0x40000000
    _WAIT_OBJECT_0 = 0x00000000
    _INFINITE = 0xFFFFFFFF

    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    MB_ICONERROR = 0x10
    MB_ICONWARNING = 0x30
    MB_ICONINFORMATION = 0x40
    MB_ICONQUESTION = 0x20

    MB_OK = 0x00000000
    MB_OKCANCEL = 0x00000001
    MB_YESNO = 0x00000004
    MB_YESNOCANCEL = 0x00000003

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

    _kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    _kernel32.CreateEventW.restype = wintypes.HANDLE

    _kernel32.SetEvent.argtypes = [wintypes.HANDLE]
    _kernel32.SetEvent.restype = wintypes.BOOL

    _kernel32.ResetEvent.argtypes = [wintypes.HANDLE]
    _kernel32.ResetEvent.restype = wintypes.BOOL

    _kernel32.WaitForMultipleObjects.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE), wintypes.BOOL, wintypes.DWORD]
    _kernel32.WaitForMultipleObjects.restype = wintypes.DWORD

    _kernel32.CancelIo.argtypes = [wintypes.HANDLE]
    _kernel32.CancelIo.restype = wintypes.BOOL

    _user32.GetParent.argtypes = [wintypes.HWND]
    _user32.GetParent.restype = wintypes.HWND

    _user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    _user32.GetSystemMetrics.restype = ctypes.c_int

    _user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
    _user32.MessageBoxW.restype = ctypes.c_int

    # Memory management related methods
    @staticmethod
    def create_buffer(size=1024):
        return ctypes.create_string_buffer(size)

    @staticmethod
    def byref(obj):
        return ctypes.byref(obj)

    # Overlapped IO related methods
    @staticmethod
    def create_overlapped(event):
        ov = OVERLAPPED()
        ov.hEvent = event
        return ov

    @staticmethod
    def create_event(manual_reset=True, initial_state=False):
        return NativeMethods._kernel32.CreateEventW(None, manual_reset, initial_state, None)

    @staticmethod
    def set_event(hEvent):
        return NativeMethods._kernel32.SetEvent(hEvent)

    @staticmethod
    def reset_event(hEvent):
        return NativeMethods._kernel32.ResetEvent(hEvent)

    @staticmethod
    def wait_for_multiple_objects(handles, wait_all=False, timeout=0xFFFFFFFF):
        handle_array = (wintypes.HANDLE * len(handles))(*handles)
        return NativeMethods._kernel32.WaitForMultipleObjects(len(handles), handle_array, wait_all, timeout)

    @staticmethod
    def cancel_io(handle):
        return NativeMethods._kernel32.CancelIo(handle)

    # UI & window related methods
    @staticmethod
    def message_box(text, title, flags=MB_OK):
        return NativeMethods._user32.MessageBoxW(
            None,
            text,
            title,
            flags
        )

    @staticmethod
    def get_parent(hwnd):
        return NativeMethods._user32.GetParent(hwnd)

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
    def get_filename_from_notify_buffer(buffer):
        # Offset 12 starts the filename in the struct FILE_NOTIFY_INFORMATION
        file_name_len = int.from_bytes(buffer[8:12], "little")
        return buffer[12:12+file_name_len].decode("utf-16")

    @staticmethod
    def open_directory_handle(path):
        return NativeMethods._kernel32.CreateFileW(
            path,
            NativeMethods._FILE_LIST_DIRECTORY,
            NativeMethods._FILE_SHARE_READ | NativeMethods._FILE_SHARE_WRITE,
            None,
            NativeMethods._OPEN_EXISTING,
            NativeMethods._FILE_FLAG_BACKUP_SEMANTICS | NativeMethods._FILE_FLAG_OVERLAPPED,
            None
        )

    @staticmethod
    def read_directory_changes(handle, buffer, overlapped_ptr):
        return NativeMethods._kernel32.ReadDirectoryChangesW(
            handle,
            buffer,
            ctypes.sizeof(buffer),
            False,
            NativeMethods._FILE_NOTIFY_CHANGE_LAST_WRITE,
            None,
            overlapped_ptr,
            None
        )

    @staticmethod
    def close_handle(handle):
        NativeMethods._kernel32.CloseHandle(handle)

    # Hotkey related methods
    @staticmethod
    def create_msg():
        return wintypes.MSG()

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

    # Screen metrics related methods
    @staticmethod
    def get_system_metrics(index):
        return NativeMethods._user32.GetSystemMetrics(index)


    @staticmethod
    def get_screen_width():
        return NativeMethods.get_system_metrics(0)


    @staticmethod
    def get_screen_height():
        return NativeMethods.get_system_metrics(1)

class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ("Internal", wintypes.LPVOID),
        ("InternalHigh", wintypes.LPVOID),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE),
    ]