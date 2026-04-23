import os
import sys
from typing import Final as ReadOnly, final as sealed

from core.native_methods import NativeMethods

@sealed
class Constants:

    SCRIPT_DIR: ReadOnly = os.path.dirname(os.path.abspath(sys.argv[0]))

    TARGET_PATH: ReadOnly = os.path.join(SCRIPT_DIR, 'resources', 'target.png')
    METER_IMAGE_PATH: ReadOnly = os.path.join(SCRIPT_DIR, 'resources', 'meter.png')

    SCREEN_WIDTH: ReadOnly = NativeMethods.get_screen_width()
    SCREEN_HEIGHT: ReadOnly = NativeMethods.get_screen_height()
