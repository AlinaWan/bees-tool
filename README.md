<div align="center">
<h1>Bees Tool</h1>
</div>

> *“In motu continuo, certitudo reperta est.”* — Riri, circa 2026

**Bees Tool** is a high-frequency, computer-vision-driven stabilization and execution utility architected for the [Bees](https://www.roblox.com/games/92528179587394) environment. It leverages a multi-stage template matching pipeline—optimized via downscaled bitmap interrogation and rotational caching—to achieve persistent locking on target entities.

By maintaining a rigorous state of *interrogatio visualis*, the framework ensures that interaction occurs only upon the attainment of a defined temporal confidence threshold (*LOCK\_DURATION\_MS*), thereby mitigating the entropy of rapid visual noise. Once a target is validated, the tool executes a precise kinematic sequence: a sub-pixel focus nudge followed by a relative vector drag, calculated *ex post facto* based on the target’s detected orientation.

<div align="center">
  <video src="https://github.com/user-attachments/assets/70f4e61e-56ca-420c-87bf-c544eda25523" width="200" controls>
  </video>
</div>

-----

## 📦 Requirements

Execution of this binary requires a Python 3.10+ runtime environment equipped with the following libraries:

  * **OpenCV (`cv2`)** – For bitmap analysis and template matching.
  * **NumPy** – For matrix manipulation and trigonometric vector calculation.
  * **PyAHK (`ahk`)** – To interface with the AutoHotkey v1.1 execution engine.
  * **python-mss** – For ultra-fast, non-blocking screen capture.
  * **Tkinter** – For the overlay-based telemetry system.

-----

## 🛠️ Configuration & Setup

Adjust the constants within the header of the script to align with your hardware's performance profile:

| Constant | Function |
| :--- | :--- |
| `CONFIDENCE_THRESHOLD` | The minimum normalized correlation coefficient (`0.0` to `1.0`) required for a match. |
| `LOCK_DURATION_MS` | The required temporal persistence (in milliseconds) before the tool engages the target. |
| `DOWNSCALE_FACTOR` | Scaling ratio for the search domain; reduces CPU overhead by `O(n^2)`. |
| `DRAG_STEP` | The scalar magnitude of the post-click mouse displacement. |
| `ROTATION_STEP` | The angular increment for pre-generated template rotations. |
| `BOUNDARY_MARGIN` | The pixel-buffer allowed for the drag destination to exist outside the ROI before the action is invalidated. |

### Installation

1.  Ensure `target.png` (the visual signature of your entity) is present in the root directory.
2.  Initialize the script via terminal:
    ```bash
    python app.py
    ```

-----

## ⌨️ Controls

| Keybind | Action |
| :--- | :--- |
| <kbd>F6</kbd> | **Toggle State**: Switches the tool between Active (Green) and Standby (Red). |
| <kbd>Shift</kbd> + <kbd>Esc</kbd> | **Termination**: Immediately closes the script and destroys all overlay windows. |

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

-----

## 🧭 Advanced Mechanics

### Rotational Memory

To maintain a high framerate, the tool utilizes a **Frequency-Based Distribution Heuristic**. It maintains a historical record of the most frequently detected orientations and re-sorts the search order in real-time. By prioritizing "high-hit" rotations, the engine achieves a statistical reduction in search time—effectively checking the most probable angles first—ensuring high performance even if the target's orientation changes intermittently.

### The Focus Nudge

Prior to the primary interaction, the tool performs a 1-pixel relative displacement. This maneuver is designed to force the host application to update its "hover" state, ensuring the subsequent click-down event is registered *intra* the intended object's hit-box.

-----

## ⚠️ Notes & Warnings

  * **Template Fidelity**: The accuracy of `target.png` is paramount. It should be cropped tightly to the entity’s core features with minimal background interference.
  * **Resolution Sensitivity**: The script calculates coordinates based on absolute screen metrics. Discrepancies between monitor scaling and game resolution must be accounted for in the `DOWNSCALE_FACTOR`.
  * **CPU Load**: High `ROTATION_STEP` values (e.g., < 15°) combined with high resolutions may induce processing latency, potentially exceeding the `LOCK_DURATION_MS` window.

-----

## 📄 License

Bees Tool is provided as-is under the [MIT License](LICENSE).