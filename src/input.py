import ctypes

user32 = ctypes.windll.user32
SCREEN_WIDTH = user32.GetSystemMetrics(0)
SCREEN_HEIGHT = user32.GetSystemMetrics(1)

# Input Types
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

# Mouse Flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_ABSOLUTE = 0x8000

# Keyboard Flags
KEYEVENTF_KEYUP = 0x0002

# Key Codes (Virtual Keys)
VK_MAP = {
    'w': 0x57, 'a': 0x41, 's': 0x53, 'd': 0x44
}

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput), ("ki", KeyBdInput), ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

def send_input(input_obj):
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_obj), ctypes.sizeof(input_obj))

def mouse_move(x, y, relative=False):
    if relative:
        # Move relative to current position
        mi = MouseInput(int(x), int(y), 0, MOUSEEVENTF_MOVE, 0, None)
    else:
        # Move to absolute screen coordinates (mapped to 0-65535)
        nx = int(x * 65535 / SCREEN_WIDTH)
        ny = int(y * 65535 / SCREEN_HEIGHT)
        mi = MouseInput(nx, ny, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, None)
    send_input(Input(INPUT_MOUSE, Input_I(mi=mi)))

def mouse_click(button='left', mode='down'):
    flags = 0
    if button == 'left':
        flags = MOUSEEVENTF_LEFTDOWN if mode == 'down' else MOUSEEVENTF_LEFTUP
    else:
        flags = MOUSEEVENTF_RIGHTDOWN if mode == 'down' else MOUSEEVENTF_RIGHTUP
    
    mi = MouseInput(0, 0, 0, flags, 0, None)
    send_input(Input(INPUT_MOUSE, Input_I(mi=mi)))

def key_event(key, mode='down'):
    vk = VK_MAP.get(key.lower(), 0)
    if not vk: return
    flags = 0 if mode == 'down' else KEYEVENTF_KEYUP
    ki = KeyBdInput(vk, 0, flags, 0, None)
    send_input(Input(INPUT_KEYBOARD, Input_I(ki=ki)))