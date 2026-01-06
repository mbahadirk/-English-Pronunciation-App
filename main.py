import os
import sys

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.gui_tkinter import Application

def main():
    app = Application()
    app.mainloop()

if __name__ == "__main__":
    main()
