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
    def on_submit(values):
        # Do not implement checker here; just call the existing logic method.
        try:
            results = logic.check_serial(serialList, values)
            print("Results:", results)
        except Exception as e:
            print("Submit error:", e)

    gui = GUIMain(serialList, on_submit=on_submit)
    gui.run()

if __name__ == "__main__":
    main()