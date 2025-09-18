# Entry point for running all experiment blocks
import tkinter as tk
from tasks import SerialRecallApp

def main():
    root = tk.Tk()
    app = SerialRecallApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
