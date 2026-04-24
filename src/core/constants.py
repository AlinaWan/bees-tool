from pathlib import Path
from typing import Final as ReadOnly, final as sealed

from core.native_methods import NativeMethods

@sealed
class Constants:

    SCRIPT_DIR: ReadOnly = Path(__file__).parent.parent.absolute()

    TARGET_PATH: ReadOnly = SCRIPT_DIR / "resources" / "target.png"
    METER_IMAGE_PATH: ReadOnly = SCRIPT_DIR / "resources" / "meter.png"

    SCREEN_WIDTH: ReadOnly = NativeMethods.get_screen_width()
    SCREEN_HEIGHT: ReadOnly = NativeMethods.get_screen_height()

    GUID: ReadOnly = "7793b168-1b31-404f-b094-38675b5b6728"
    GITHUB_URL: ReadOnly = "https://github.com/AlinaWan/bees-tool"