# main.py
import tkinter as tk
from ui import ModernNutritionTracker
from db import connect_to_db, create_user

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernNutritionTracker(root)
    root.mainloop()
