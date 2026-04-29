import numpy as np
import re
from typing import final as sealed

from core.constants import Constants

@sealed
class OCRParser:
    @staticmethod
    def _find_color_hit(img_bgr, target_bgr, tolerance=25, strip=5):
        target = np.array(target_bgr, dtype=np.int16)
        img = img_bgr.astype(np.int16)

        h, w, _ = img.shape

        for x in range(w):
            run = 0

            for y in range(h):
                pixel = img[y, x]

                diff = np.abs(pixel - target)
                if np.sum(diff) <= tolerance:
                    run += 1
                    if run >= strip:
                        return True
                else:
                    run = 0  # reset strip if broken

        return False

    def parse_bee_text(text: str):
        clean = text.replace("\n", " ").strip()

        # --- Normalize OCR noise ---
        clean = re.sub(r"\.\.+", ".", clean)                 # 37..16 -> 37.16
        clean = re.sub(r"(\d)\s+(\d)", r"\1\2", clean)       # 37. 16 -> 37.16

        clean = re.sub(r"(?<=\d)\s*[:;,]\s*(?=\d)", ".", clean) # handles: 81:7kg, 81;7kg, 81,7kg

        # --- Fix OCR unit corruption ---
        clean = re.sub(r"\bkq\b", "kg", clean, flags=re.IGNORECASE) # explicitly fix kq
        clean = re.sub(r"\bk g\b", "kg", clean, flags=re.IGNORECASE)

        # --- Bee detection context ---
        has_bee_word = "bee" in clean.lower()

        # --- Bee name extraction ---
        name_match = re.search(r"([A-Za-z]+(?:\s?[A-Za-z]+)*\s?Bee)", clean)

        if name_match:
            raw_name = name_match.group(1)

            # If OCR attached "Bee" but it's not actually a confirmed word contextually, strip it
            if not has_bee_word:
                bee_name = re.sub(r"\s*Bee$", "", raw_name, flags=re.IGNORECASE)
            else:
                bee_name = raw_name
        else:
            # fallback: try grabbing first word cluster before weight
            fallback_match = re.search(r"^([A-Za-z]+(?:\s[A-Za-z]+)*)", clean)
            bee_name = fallback_match.group(1) if fallback_match else "unknown Bee"

        bee_name = bee_name.title().strip()

        # --- Weight extraction ---
        weight_match = re.search(r"(\d+(?:\.\d+)?\s*[kKmM][gG])", clean)
        bee_weight = weight_match.group(1).lower() if weight_match else "unknown"

        return bee_name, bee_weight

    @staticmethod
    def detect_rarity_by_color(img_bgr):

        h = img_bgr.shape[0]

        # take bottom half of OCR ROI
        img_bgr = img_bgr[h // 2:, :]

        best_match = "Common"

        for name, data in Constants.RARITY_DATA.items():
            if OCRParser._find_color_hit(img_bgr, data["color_bgr"]):
                return name

        return best_match