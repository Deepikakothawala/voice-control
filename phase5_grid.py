import tkinter as tk
import pyautogui

class MouseGrid:
    def __init__(self):
        # 1. Setup the transparent, full-screen overlay
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True) # Keep it above all other apps
        
        # PRO-TRICK: Make all white pixels completely transparent
        self.root.attributes('-transparentcolor', 'white')
        self.root.config(bg='white')
        
        self.canvas = tk.Canvas(self.root, bg='white', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 2. Get the exact pixel dimensions of your specific monitor
        self.screen_w, self.screen_h = pyautogui.size()
        
        # Initialize starting coordinates (Full Screen)
        self.current_x = 0
        self.current_y = 0
        self.current_w = self.screen_w
        self.current_h = self.screen_h
        
        self.draw_grid()
        
        # 3. Temporary Keyboard Controls (For testing before voice integration)
        self.root.bind('<Key>', self.key_handler)
        print("\n>>> GRID ACTIVE <<<")
        print("- Press keys 1-9 to drill down into a sector.")
        print("- Press 'C' to execute a mouse click.")
        print("- Press 'Esc' to cancel and close.")
        
    def draw_grid(self):
        self.canvas.delete("all")
        w_third = self.current_w / 3
        h_third = self.current_h / 3
        
        # Draw the Red Grid Lines
        for i in range(1, 3):
            # Vertical lines
            x = self.current_x + (i * w_third)
            self.canvas.create_line(x, self.current_y, x, self.current_y + self.current_h, fill='red', width=3)
            # Horizontal lines
            y = self.current_y + (i * h_third)
            self.canvas.create_line(self.current_x, y, self.current_x + self.current_w, y, fill='red', width=3)
            
        # Draw the Blue Numbers in the center of each sector
        sector = 1
        for row in range(3):
            for col in range(3):
                center_x = self.current_x + (col * w_third) + (w_third / 2)
                center_y = self.current_y + (row * h_third) + (h_third / 2)
                self.canvas.create_text(center_x, center_y, text=str(sector), fill='blue', font=('Arial', 48, 'bold'))
                sector += 1
                
    def update_sector(self, sector):
        # Calculate the math to shrink the grid into the chosen sector
        row = (sector - 1) // 3
        col = (sector - 1) % 3
        
        w_third = self.current_w / 3
        h_third = self.current_h / 3
        
        self.current_x += col * w_third
        self.current_y += row * h_third
        self.current_w = w_third
        self.current_h = h_third
        
        self.draw_grid()
        
    def click_center(self):
        # Calculate the exact pixel center of the current box
        center_x = self.current_x + (self.current_w / 2)
        center_y = self.current_y + (self.current_h / 2)
        
        # Destroy the grid FIRST so the mouse doesn't accidentally click the transparent canvas
        self.root.destroy()
        
        # Fire the physical mouse click
        pyautogui.click(center_x, center_y)

    def key_handler(self, event):
        char = event.char.lower()
        if char in '123456789':
            self.update_sector(int(char))
        elif char == 'c':
            self.click_center()
        elif event.keysym == 'Escape':
            self.root.destroy()

if __name__ == "__main__":
    app = MouseGrid()
    app.root.mainloop()