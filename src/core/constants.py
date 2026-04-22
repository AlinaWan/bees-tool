import os
import sys
from typing import final as sealed

from core.native_methods import NativeMethods

@sealed
class Constants:

    SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

    TARGET_PATH = os.path.join(SCRIPT_DIR, 'resources', 'target.png')
    METER_IMAGE_PATH = os.path.join(SCRIPT_DIR, 'resources', 'meter.png')

    SCREEN_WIDTH = NativeMethods.get_screen_width()
    SCREEN_HEIGHT = NativeMethods.get_screen_height()