try:
    from .GUI.GUIMain import GUIMain
    from .Logic.MainLogic import MainLogic
except ImportError:
    from GUI.GUIMain import GUIMain
    from Logic.MainLogic import MainLogic


def main():
    logic = MainLogic()
    serialList = logic.generate_serial()
    print("Generated Serial:", serialList)
    gui = GUIMain(serialList)
    gui.run()

if __name__ == "__main__":
    main()