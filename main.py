import tkinter as tk
from GUI.main_GUI import App
from Core.Utilities.settings_manager import load_settings


if __name__ == "__main__":
    load_settings()
    root = tk.Tk()
    app = App(root)
    root.mainloop()
