from pathlib import Path
from typing import Final as ReadOnly, final as sealed

from core.native_methods import NativeMethods

@sealed
class Constants:

    SCRIPT_DIR: ReadOnly = Path(__file__).resolve().parent.parent # src\ dir
    WINDOWS_DIR: ReadOnly = Path(NativeMethods.get_windows_directory())

    TARGET_PATH: ReadOnly = SCRIPT_DIR / "resources" / "target.png"
    METER_IMAGE_PATH: ReadOnly = SCRIPT_DIR / "resources" / "meter.png"
    TEXT_EDITOR_PATH: ReadOnly = WINDOWS_DIR / "System32" / "notepad.exe"

    SCREEN_WIDTH: ReadOnly = NativeMethods.get_screen_width()
    SCREEN_HEIGHT: ReadOnly = NativeMethods.get_screen_height()

    GUID: ReadOnly = "7793b168-1b31-404f-b094-38675b5b6728"
    GITHUB_URL: ReadOnly = "https://github.com/AlinaWan/bees-tool"

    RARITY_DATA = { # rarity data for bees for discord webhooks; colors compiled by Riri
        "Common":    {"color_bgr": (154, 154, 154), "embed_color": 0x9a9a9a, "rank": 0},
        "Uncommon":  {"color_bgr": (94, 196, 34),   "embed_color": 0x22c45e, "rank": 1},
        "Rare":      {"color_bgr": (245, 129, 59),  "embed_color": 0x3b81f5, "rank": 2}, 
        "Epic":      {"color_bgr": (247, 85, 168),  "embed_color": 0xa855f7, "rank": 3},
        "Legendary": {"color_bgr": (36, 191, 251),   "embed_color": 0xfbbf24, "rank": 4},
        "Mythic":    {"color_bgr": (109, 51, 255),   "embed_color": 0xff336d, "rank": 5},
        "Secret":    {"color_bgr": (238, 211, 34), "embed_color": 0x22d3ee, "rank": 6},
    }