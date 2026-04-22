import tkinter as tk
from typing import final as sealed

@sealed
class TooltipMarker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-transparentcolor", "black")
        
        self.canvas = tk.Canvas(self.root, width=1000, height=1000, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        self.circle = self.canvas.create_oval(10, 10, 70, 70, outline="lime", width=2)
        self.debug_text = self.canvas.create_text(10, 75, anchor="nw", fill="lime", font=("Consolas", 8))
        self.line = None 
        
    def show(self, x, y, scale, angle=0, confidence=0, locked=False, in_bounds=True, drag_to=None, winner_idx=None):
        if not in_bounds:
            color = "red"
        else:
            color = "cyan" if locked else "lime"
            
        self.canvas.itemconfig(self.circle, outline=color)
        self.canvas.itemconfig(self.debug_text, fill=color)

        logic_str = (
            f"VEC:  {angle:03}° [IDX: {winner_idx}]\n"
            f"CONF: {confidence*100:.1f}%\n"
            f"POS:  ({int(x/scale)}, {int(y/scale)})\n"
            f"BNDS: {'OK' if in_bounds else 'OUT'}"
        )
        self.canvas.itemconfig(self.debug_text, text=logic_str)

        if self.line:
            self.canvas.delete(self.line)
            self.line = None
        if drag_to:
            start_x, start_y = 40, 40 
            end_x = (drag_to[0] - x) / scale + start_x
            end_y = (drag_to[1] - y) / scale + start_y
            line_color = "red" if not in_bounds else "cyan"
            self.line = self.canvas.create_line(start_x, start_y, end_x, end_y, fill=line_color, width=2, dash=(4, 2))

        pos_x, pos_y = int((x / scale) - 40), int((y / scale) - 40)
        self.root.geometry(f"1000x1000+{pos_x}+{pos_y}")
        self.root.deiconify()
        self.root.update()

    def hide(self):
        self.root.withdraw()
        try: self.root.update()
        except: pass