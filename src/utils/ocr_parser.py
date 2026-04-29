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
        clean = re.sub(r"\.\.+", ".", clean)
        clean = re.sub(r"(\d)\s+(\d)", r"\1\2", clean)
        clean = re.sub(r"(?<=\d)\s*[:;,]\s*(?=\d)", ".", clean)

        # --- Fix OCR unit corruption ---
        clean = re.sub(r"\bkq\b", "kg", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\bk g\b", "kg", clean, flags=re.IGNORECASE)

        # --- Bee detection & Name extraction (Same as before) ---
        has_bee_word = "bee" in clean.lower()
        name_match = re.search(r"([A-Za-z]+(?:\s?[A-Za-z]+)*\s?Bee)", clean)

        if name_match:
            raw_name = name_match.group(1)
            bee_name = raw_name if has_bee_word else re.sub(r"\s*Bee$", "", raw_name, flags=re.IGNORECASE)
        else:
            fallback_match = re.search(r"^([A-Za-z]+(?:\s[A-Za-z]+)*)", clean)
            bee_name = fallback_match.group(1) if fallback_match else "unknown Bee"
        
        bee_name = bee_name.title().strip()

        # --- Enhanced Weight Extraction ---
        # 1. Broad search: Look for numbers OR look-alike characters (S, I, l, O, Q) 
        # followed by the unit (kg/mg)
        weight_match = re.search(r"([0-9SlIOQ]+(?:\.[0-9SlIOQ]+)?\s*[kKmM][gG])", clean)
        
        if weight_match:
            raw_weight = weight_match.group(1).lower()
            
            # 2. Map look-alikes to numbers
            mapping = {
                's': '5',
                'i': '1',
                'l': '1',
                'o': '0',
                'q': '0'
            }
            
            # Apply mapping only to the numbers part
            for char, replacement in mapping.items():
                raw_weight = raw_weight.replace(char, replacement)
            
            bee_weight = raw_weight
        else:
            bee_weight = "unknown"

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