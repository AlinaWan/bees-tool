from typing import final as sealed

from core.constants import Constants

@sealed
class Config:

    # --- Slider Automation ---
    CONFIDENCE_THRESHOLD = 0.82                   # Confidence to track
    ROTATION_STEP = 45                            # Rotation steps
    DRAG_STEP = int(Constants.SCREEN_HEIGHT * (500 / 1080)) # Drag step to drag based on the screen height
    COOLDOWN_MS = 100                             # Cooldown
    LOCK_DURATION_MS = 10                         # How long the object must persist to lock
    DOWNSCALE_FACTOR = 0.5                        # 0.5 = 50% size (4x faster processing)
    BOUNDARY_MARGIN = 100                         # Px allowed outside ROI before failing
    MINIGAME_TIMEOUT_MS = 2000                    # Time a slider hasn't appeared to be considered not in minigame

    # --- Meter Automation ---
    AUTO_RELEASE_ENABLED = True                   # Enable the auto release module
    AUTO_RELEASE_TOLERANCE = 5                    # Tolerance for the optimized search
    AUTO_RELEASE_CONFIDENCE = 0.90                # Confidence for calibration
    AUTO_RELEASE_Y_OFFSET = 30                    # The offset to move the scan region down to account for delay
    SEARCH_DEPTH = 5                              # Define how deep the search range is for the top of the meter

    # --- Auto Routine ---
    AUTO_ROUTINE_ENABLED = False                   # Enable the subroutine module (forces Auto Release)
    AUTO_ROUTINE_PATTERN = (                      # Walk pattern
        ['w','w','w',
         'd','d','d',
         's','s','s',
         'a','a','a']
    )
    AUTO_ROUTINE_WALK_TIME_MS = 250               # Time to hold each walk key
    AUTO_ROUTINE_LMB_TIMEOUT_MS = 3000            # Time a minigame hasn't appeared to give up this cycle

    # Implicitly force AUTO_RELEASE if AUTO_ROUTINE
    if AUTO_ROUTINE_ENABLED:
        AUTO_RELEASE_ENABLED = True
