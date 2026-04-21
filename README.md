<div align="center">
<h1>Bees Tool</h1>
</div>

> *“In motu continuo, certitudo reperta est.”* — Riri, circa 2026

**Bees Tool** is a high-frequency, computer-vision-driven stabilization and execution utility architected for the [Bees](https://www.roblox.com/games/92528179587394) environment. It leverages a multi-stage template matching pipeline—optimized via downscaled bitmap interrogation and rotational caching—to achieve persistent locking on target entities.

By maintaining a rigorous state of *interrogatio visualis*, the framework ensures that interaction occurs only upon the attainment of a defined temporal confidence threshold (*LOCK\_DURATION\_MS*), thereby mitigating the entropy of rapid visual noise. Once a target is validated, the tool executes a precise kinematic sequence: a sub-pixel focus nudge followed by a relative vector drag, calculated *ex post facto* based on the target’s detected orientation.

<div align="center">
  <video src="https://github.com/user-attachments/assets/8bbe6eb9-72fd-4d4d-9d34-9d73fb156ae2" width="100%" controls>
  </video>
</div>

-----

## 📦 Requirements

Execution of this binary requires a Python 3.10+ runtime environment equipped with the necessary dependencies:

```bash
pip install -r requirements.txt
```

-----

## 🛠️ Configuration & Setup

Adjust the constants within the header of the script to align with your hardware's performance profile:

### Slider Automation (Main Interaction)
<details open>
  <summary>Click to view</summary>

| Constant | Function |
| :--- | :--- |
| `CONFIDENCE_THRESHOLD` | The minimum normalized correlation coefficient (`0.0` to `1.0`) required for a match. |
| `ROTATION_STEP` | The angular increment used to generate the rotated template cache. |
| `DRAG_STEP` | The scalar magnitude of the corrective mouse displacement applied after engagement. |
| `COOLDOWN_MS` | The minimum delay between successive corrective drag actions. |
| `LOCK_DURATION_MS` | The required temporal persistence (in milliseconds) before the tool engages the target. |
| `DOWNSCALE_FACTOR` | Scaling ratio applied to the search domain to reduce computational load (`O(n²)` reduction). |
| `BOUNDARY_MARGIN` | Pixel buffer allowing the drag destination to exist outside the ROI before invalidation. |
| `MINIGAME_TIMEOUT_MS` | Duration a slider has not been detected before the system infers the minigame has ended. |

</details>

### Meter Automation (Swing Release)
<details>
  <summary>Click to view</summary>
| Constant | Function |
| :--- | :--- |
| `AUTO_RELEASE_ENABLED` | Toggles the calibration and execution of the automated meter-release system. |
| `AUTO_RELEASE_TOLERANCE` | The allowable RGB variance when identifying the green bar signature. |
| `AUTO_RELEASE_CONFIDENCE` | The normalized correlation threshold required for meter template calibration. |
| `SEARCH_DEPTH` | The vertical pixel search range used to detect the rising meter. |

</details>

### Routine Automation (Traversal & Swing Execution)
<details>
  <summary>Click to view</summary>
| Constant | Function |
| :--- | :--- |
| `AUTO_ROUTINE_ENABLED` | Enables the autonomous walk-and-swing routine (implicitly forces `AUTO_RELEASE_ENABLED`). |
| `AUTO_ROUTINE_PATTERN` | The ordered movement sequence executed between swing attempts. |
| `AUTO_ROUTINE_WALK_TIME_MS` | Duration each movement key is held during routine traversal. |
| `AUTO_ROUTINE_LMB_TIMEOUT_MS` | Maximum duration the routine will hold LMB awaiting a minigame before aborting the current cycle. |

</details>

### Installation

1.  Ensure `target.png` (the visual signature of your entity) is present in the root directory.
2.  Initialize the script via terminal:
    ```bash
    python app.pyw
    ```

-----

## ⌨️ Controls

| Keybind                           | Action                                                                                               |
| :-------------------------------- | :--------------------------------------------------------------------------------------------------- |
| <kbd>F6</kbd>                     | **Toggle State**: Switches the tool between Active (Green) and Standby (Red).                        |
| <kbd>Ctrl</kbd> + <kbd>F10</kbd>  | **Menu Toggle**: Shows or hides the menu for loading, editing, and saving (exporting) configurations |
| <kbd>Shift</kbd> + <kbd>Esc</kbd> | **Termination**: Immediately closes the script and destroys all overlay windows.                     |

-----

## 🖥️ Operational Logic

### The "Lock" Mechanism

Unlike primitive pixel-searchers, Bees Tool requires a **Stable Identification State**. Interaction occurs only when two conditions are met: **Temporal Stability** (the target persists for `LOCK_DURATION_MS`) and **Spatial Validity** (the target's orientation does not project a drag path outside the allowed `BOUNDARY_MARGIN`). This ensures that the tool does not "flick" to transient artifacts or UI debris.

### Telemetry Overlay

The script provides real-time visual feedback via a transparent Tkinter canvas. The **Region of Interest (ROI)** indicators communicate the current state:

* **Green ROI Points**: Tool is **Active/ON**. The system is actively interrogating the search domain.
* **Red ROI Points**: Tool is **Inactive/OFF**. Logic is suspended, though the overlay remains initialized.
* **Lime Circle**: Target identified; currently accumulating confidence.
* **Cyan Circle**: Target locked; lock duration threshold exceeded, interaction imminent.
* **Red Circle**: Target identified, but the calculated vector would exceed the Boundary Margin. Action suppressed.
* **Yellow Horizontal Bars**: Rendered only after successful calibration. These indicate the precise Y-axis and width where the tool is monitoring the peak of the meter.

-----

## ⚖️ Meter Automation & Observational Calibration

The **Auto Release** module is a specialized sub-system designed for the terminal phase of the interaction—the net release. Unlike conventional region-lock approaches where coordinate data is predefined, this system utilizes **Observationally Inferred Calibration**.

### The Calibration Phase

Upon initialization, the tool remains in a searching state for the meter interface (defined by `meter.png`). Rather than requiring static coordinates, the script performs a one-time, high-fidelity template match across the right hemisphere of the display.
Once the signature is identified, the system silently extracts the **spatial geometry and chromatic profile** of the interaction bar. It captures the exact Y-coordinate and a 4-pixel horizontal color sample to serve as a persistent reference.

### Optimized Execution Logic

The moment the rising green bar's color signature enters the performance-optimized interception zone, the tool issues an immediate `button='left', direction='up'` command, executing the swing at the apex of the meter.

-----

## 🗺️ Auto Routine & Autonomous Traversal

The **Auto Routine** module extends the system beyond reactive execution into **structured environmental traversal**. Rather than remaining stationary between interactions, the tool performs a controlled movement cycle designed to periodically reposition the player and initiate new swing attempts.

### The Traversal Pattern

When enabled, the routine follows a deterministic **movement sequence** defined by `AUTO_ROUTINE_PATTERN`. Each vector in the pattern is applied sequentially, with the corresponding key held for `AUTO_ROUTINE_WALK_TIME_MS` before advancing to the next step. The pattern loops indefinitely, forming a continuous traversal circuit.

### Autonomous Swinging Cycle

After completing each movement step, the routine initiates a new swing attempt by issuing a sustained `button='left', direction='down'` command. This action hands control to the **Auto Release** subsystem, which performs calibration if necessary and manages the release timing during the swing.

If no minigame is detected within the interval defined by `AUTO_ROUTINE_LMB_TIMEOUT_MS`, the routine concludes the attempt and resumes traversal with the next movement vector. This cyclical process creates a fully autonomous loop of **movement, swinging, and execution**, allowing the system to operate continuously without manual repositioning.

-----

## 🛰️ Nomenclature & Phonetics

To maintain alignment with the architectural vision of the framework, the designation **Bees Tool** is to be phonetically rendered as **/biːs/** (*rhyming with "fleece" or "geese"*).

The voiced alveolar fricative **/biːz/** (as in the Hymenoptera insect) is considered a lexical deviation and will not be tolerated in formal interrogation or community discourse. Proper sibilance is a prerequisite for tool competency.

-----

## 🧭 Advanced Mechanics

### Rotational Memory

To maintain a high framerate, the tool utilizes a **Frequency-Based Distribution Heuristic**. It maintains a historical record of the most frequently detected orientations and re-sorts the search order in real-time. By prioritizing "high-hit" rotations, the engine achieves a statistical reduction in search time—effectively checking the most probable angles first—ensuring high performance even if the target's orientation changes intermittently.

### The Focus Nudge

Prior to the primary interaction, the tool performs a 1-pixel relative displacement. This maneuver is designed to force the host application to update its "hover" state, ensuring the subsequent click-down event is registered *intra* the intended object's hit-box.

### Configuration Portability

All adjustable parameters can be stored in a human-readable `.json` file. This allows users to easily export, share, and import configurations without needing to modify the source code. These configuration files can be managed through the in-app menu, providing a user-friendly interface for customization and optimization based on individual hardware capabilities and display setups.

-----

## ⚠️ Notes & Warnings

  * **Template Fidelity**: Templates based on a 1920x1080 resolution are provided as a baseline, but users may need to capture custom templates if their display configuration differs significantly. Although manual pixel coordinate entry is not required, the tool's performance is highly dependent on the quality of the template matches.

-----

## 📄 License

Bees Tool is provided as-is under the [MIT License](LICENSE).

Copyright (c) 2026 Riri