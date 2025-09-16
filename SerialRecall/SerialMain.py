try:
    from .GUI.GUIMain import GUIMain
    from .Logic.MainLogic import MainLogic
except ImportError:
    from GUI.GUIMain import GUIMain
    from Logic.MainLogic import MainLogic


def main():
    # GUI now internally manages serial generation, checking, and logging
    gui = GUIMain()
    gui.run()

if __name__ == "__main__":
    main()