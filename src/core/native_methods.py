import ctypes
from ctypes import wintypes
from typing import Final as ReadOnly, final as sealed

if ctypes.sizeof(ctypes.c_void_p) == 8:
    ULONG_PTR = ctypes.c_ulonglong
else:
    ULONG_PTR = ctypes.c_ulong

@sealed
class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ("Internal", ULONG_PTR),
        ("InternalHigh", ULONG_PTR),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE),
    ]

@sealed
class NativeMethods:

    _dwmapi: ReadOnly = ctypes.WinDLL("dwmapi")
    _kernel32: ReadOnly = ctypes.WinDLL("kernel32")
    _user32: ReadOnly = ctypes.WinDLL("user32")

    _DWMWA_WINDOW_CORNER_PREFERENCE: ReadOnly = 33
    _DWMWCP_ROUND: ReadOnly = 2

    _DPI_AWARENESS_CONTEXT_UNAWARE = ctypes.c_void_p(-1)
    _DPI_AWARENESS_CONTEXT_SYSTEM_AWARE = ctypes.c_void_p(-2)
    _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = ctypes.c_void_p(-3)
    _DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

    _FILE_LIST_DIRECTORY: ReadOnly = 0x0001
    _FILE_SHARE_READ: ReadOnly = 0x00000001
    _FILE_SHARE_WRITE: ReadOnly = 0x00000002
    _OPEN_EXISTING: ReadOnly = 3
    _FILE_FLAG_BACKUP_SEMANTICS: ReadOnly = 0x02000000
    _FILE_NOTIFY_CHANGE_LAST_WRITE: ReadOnly = 0x00000010

    _FILE_FLAG_OVERLAPPED: ReadOnly = 0x40000000
    _WAIT_OBJECT_0: ReadOnly = 0x00000000
    _INFINITE: ReadOnly = 0xFFFFFFFF

    ERROR_ALREADY_EXISTS: ReadOnly = 183

    INVALID_HANDLE_VALUE: ReadOnly = wintypes.HANDLE(-1).value
    
    MB_ICONERROR: ReadOnly = 0x10
    MB_ICONWARNING: ReadOnly = 0x30
    MB_ICONINFORMATION: ReadOnly = 0x40
    MB_ICONQUESTION: ReadOnly = 0x20

    MB_OK: ReadOnly = 0x00000000
    MB_OKCANCEL: ReadOnly = 0x00000001
    MB_YESNO: ReadOnly = 0x00000004
    MB_YESNOCANCEL: ReadOnly = 0x00000003

    WM_HOTKEY: ReadOnly = 0x0312
    MOD_SHIFT: ReadOnly = 0x0004
    MOD_CONTROL: ReadOnly = 0x0002
    VK_F6: ReadOnly = 0x75
    VK_F10: ReadOnly = 0x79
    VK_ESCAPE: ReadOnly = 0x1B

    _dwmapi.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    _dwmapi.DwmSetWindowAttribute.restype = ctypes.HRESULT

    _kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    _kernel32.CreateMutexW.restype = wintypes.HANDLE

    _kernel32.ReleaseMutex.argtypes = [wintypes.HANDLE]
    _kernel32.ReleaseMutex.restype = wintypes.BOOL

    _kernel32.GetLastError.argtypes = []
    _kernel32.GetLastError.restype = wintypes.DWORD

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

    _kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    _kernel32.CreateFileW.restype = wintypes.HANDLE

    _kernel32.ReadDirectoryChangesW.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(OVERLAPPED), wintypes.LPVOID]
    _kernel32.ReadDirectoryChangesW.restype = wintypes.BOOL

    _user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    _user32.RegisterHotKey.restype = wintypes.BOOL

    _user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.UnregisterHotKey.restype = wintypes.BOOL

    _user32.GetParent.argtypes = [wintypes.HWND]
    _user32.GetParent.restype = wintypes.HWND

    _user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    _user32.GetSystemMetrics.restype = ctypes.c_int

    _user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
    _user32.MessageBoxW.restype = ctypes.c_int

    _user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
    _user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL

    # Memory management related methods
    @staticmethod
    def create_buffer(size=1024):
        return ctypes.create_string_buffer(size)

    @staticmethod
    def byref(obj):
        return ctypes.byref(obj)

    # Mutex related methods
    @staticmethod
    def create_mutex(name: str, initial_owner: bool = True):
        return NativeMethods._kernel32.CreateMutexW(None, initial_owner, name)

    @staticmethod
    def release_mutex(handle):
        return NativeMethods._kernel32.ReleaseMutex(handle)

    @staticmethod
    def get_last_error():
        return NativeMethods._kernel32.GetLastError()

    @staticmethod
    def create_single_instance_mutex(name: str):
        handle = NativeMethods.create_mutex(name, True)

        if not handle:
            return None, False

        already_exists = (NativeMethods.get_last_error() == NativeMethods.ERROR_ALREADY_EXISTS)
        return handle, not already_exists

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

    @staticmethod
    def set_process_dpi_awareness_context(context=-4):
        ctx_map = {
            -1: NativeMethods._DPI_AWARENESS_CONTEXT_UNAWARE,
            -2: NativeMethods._DPI_AWARENESS_CONTEXT_SYSTEM_AWARE,
            -3: NativeMethods._DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE,
            -4: NativeMethods._DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2,
        }

        return NativeMethods._user32.SetProcessDpiAwarenessContext(
            ctx_map.get(context, NativeMethods._DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
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
            wintypes.HANDLE(None)
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
