import tkinter as tk
import time
from typing import List, Callable, Optional
try:
    from ..Logging.logger import GameLogger
    from ..Logic.MainLogic import MainLogic
except ImportError:
    from Logging.logger import GameLogger
    from Logic.MainLogic import MainLogic


class GUIMain():
    """
    Simple GUI:
    - Initially shows 10 placeholders: "XX XX ..."
    - After 5 seconds, swaps to 10 input boxes where each box accepts 0-2 digits (0-99)
    """

    def __init__(self, Seriallist: Optional[List[int]] = None, on_submit: Optional[Callable[[List[int | None]], None]] = None):
        self.root = tk.Tk()
        self.root.title("Serial Recall")
        self.root.geometry("1000x260")
        self.root.resizable(False, False)

        self.Seriallist = Seriallist or []
        self.on_submit = on_submit

        # Internal logic + logger
        self.logic = MainLogic()
        self.logger = GameLogger()
        self.attempt = 0
        self.speed_rounds_done = 0
        self.recall_time_ms = 5000  # default reveal time
        self.speed_mode_active = False
        self.recall_start_time = None  # for speed mode adaptation
        self.input_start_time = None

        # Game mode dropdown
        self.gamemodes = ["Normal", "Speed", "MemoryPattern"]
        self.selected_gamemode = tk.StringVar(value=self.gamemodes[0])
        self.dropdown_frame = tk.Frame(self.root)
        self.dropdown_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        tk.Label(self.dropdown_frame, text="Game Mode:", font=("Segoe UI", 12)).pack(side=tk.LEFT)
        self.gamemode_menu = tk.OptionMenu(self.dropdown_frame, self.selected_gamemode, *self.gamemodes)
        self.gamemode_menu.config(font=("Segoe UI", 12))
        self.gamemode_menu.pack(side=tk.LEFT, padx=10)

        # Start button
        self.start_button = tk.Button(self.dropdown_frame, text="Start", font=("Segoe UI", 12, "bold"), command=self._on_start)
        self.start_button.pack(side=tk.LEFT, padx=20)

    # Track if game has started
        self.game_started = False

        # Container for content
        self.container = tk.Frame(self.root, padx=10, pady=20)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.placeholder_frame = None
        self.input_frame = None
        self.entries = []
        self.buttons_frame = None
        self.feedback_label = tk.Label(self.root, text="", font=("Segoe UI", 14))
        self.feedback_label.pack(pady=4)

        # Do not show placeholders or start timer until Start is clicked
    def _on_start(self):
        if self.game_started:
            return
        self.game_started = True
        # Disable dropdown
        self.gamemode_menu.config(state="disabled")
        self.start_button.config(state="disabled")
        # Determine mode specifics
        mode = self.selected_gamemode.get()
        self.speed_mode_active = mode == "Speed"
        if self.speed_mode_active:
            self.recall_time_ms = 5000
        else:
            self.recall_time_ms = 5000
        # Generate first serial (always regenerate at start)
        self.Seriallist = self.logic.generate_serial()
        # Show placeholders
        self._show_placeholders()
        self.recall_start_time = time.perf_counter()
        # After recall_time swap to inputs
        self.root.after(self.recall_time_ms, self._swap_to_inputs)

    def _show_placeholders(self) -> None:
        if self.input_frame is not None:
            self.input_frame.destroy()
            self.input_frame = None

        self.placeholder_frame = tk.Frame(self.container)
        self.placeholder_frame.pack()

        # Create 10 labels horizontally
        for i in range(10):
            lbl = tk.Label(
                self.placeholder_frame,
                text= self.Seriallist[i] if i < len(self.Seriallist) else "XX",
                font=("Segoe UI", 18, "bold"),
                width=3,
                anchor="center",
            )
            lbl.grid(row=0, column=i, padx=6)

    def _validate_two_digits(self, proposed: str) -> bool:
        """
        Tkinter validatecommand receives the proposed value via %P.
        Allow empty string, or 1-2 digits only.
        """
        if proposed == "":
            return True
        return proposed.isdigit() and len(proposed) <= 2

    def _swap_to_inputs(self) -> None:
        # Remove placeholders
        if self.placeholder_frame is not None:
            self.placeholder_frame.destroy()
            self.placeholder_frame = None

        # Create inputs
        self.input_frame = tk.Frame(self.container)
        self.input_frame.pack()

        vcmd = (self.root.register(self._validate_two_digits), "%P")
        self.entries = []
        for i in range(10):
            ent = tk.Entry(
                self.input_frame,
                width=3,  # shows up to 2 digits comfortably
                font=("Segoe UI", 18),
                justify="center",
                validate="key",
                validatecommand=vcmd,
            )
            ent.grid(row=0, column=i, padx=6)
            self.entries.append(ent)

        # Focus first input
        if self.entries:
            self.entries[0].focus_set()

        # Add Submit button below the inputs
        self.SubmitButton()
        # Start input timing
        self.input_start_time = time.perf_counter()

    def get_values(self) -> List[int | None]:
        """Return the 10 entered values as ints (0-99) or None if empty."""
        values: List[int | None] = []
        for ent in self.entries:
            s = ent.get().strip()
            if s == "":
                values.append(None)
            else:
                try:
                    values.append(int(s))
                except ValueError:
                    values.append(None)
        return values
    
    def SubmitButton(self):
        if self.buttons_frame is not None:
            self.buttons_frame.destroy()

        self.buttons_frame = tk.Frame(self.container)
        self.buttons_frame.pack(pady=10)

        submit_btn = tk.Button(self.buttons_frame, text="Submit", command=self._on_submit)
        submit_btn.pack()

    def _on_submit(self) -> None:
        values = self.get_values()
        # Compute results internally
        results = self.logic.check_serial(self.Seriallist, values)
        round_errors = results.count(False)
        first_wrong = not results[0] if len(results) > 0 else False
        last_wrong = not results[-1] if len(results) > 0 else False
        input_time = None
        if self.input_start_time is not None:
            input_time = time.perf_counter() - self.input_start_time
        # Feedback
        if round_errors == 0:
            self.feedback_label.config(text="Correct!", fg="green")
        else:
            self.feedback_label.config(text=f"Wrong ({round_errors} errors)", fg="red")
        # Attempt counter
        self.attempt += 1
        # Log
        self.logger.log_attempt(
            attempt=self.attempt,
            mode=self.selected_gamemode.get(),
            serial=self.Seriallist,
            user_input=values,
            round_errors=round_errors,
            first_wrong=first_wrong,
            last_wrong=last_wrong,
            recall_time_ms=self.recall_time_ms,
            input_time_s=input_time,
        )
        # Prepare next round after delay
        self.root.after(3000, self._next_round)

    def _next_round(self):
        # Cleanup existing input frame
        if self.input_frame is not None:
            self.input_frame.destroy()
            self.input_frame = None
        # Adjust speed mode timing
        if self.speed_mode_active and self.speed_rounds_done < 10:
            # Decrease recall time but keep a floor (e.g., 1000 ms)
            decrement = 400  # 0.4s faster each round
            self.recall_time_ms = max(1000, self.recall_time_ms - decrement)
            self.speed_rounds_done += 1
        # Generate new serial
        self.Seriallist = self.logic.generate_serial()
        # Show placeholders
        self._show_placeholders()
        self.recall_start_time = time.perf_counter()
        self.root.after(self.recall_time_ms, self._swap_to_inputs)


    def run(self) -> None:
        self.root.mainloop()
