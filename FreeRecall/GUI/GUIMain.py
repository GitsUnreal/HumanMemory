import tkinter as tk
import time
from typing import List, Callable, Optional
try:
    from ..Logging.logger import GameLogger
    from ..Logic.MainLogic import MainLogic
    from ..MemoryTask.Pattern import PatternGame
except ImportError:
    from Logging.logger import GameLogger
    from Logic.MainLogic import MainLogic
    from MemoryTask.Pattern import PatternGame


class GUIMain():
    """
    Simple GUI:
    - Initially shows 10 placeholders: "XX XX ..."
    - After 5 seconds, swaps to 10 input boxes where each box accepts 0-2 digits (0-99)
    """

    def __init__(self, Seriallist: Optional[List[int]] = None, on_submit: Optional[Callable[[List[int | None]], None]] = None):
        self.root = tk.Tk()
        self.root.title("Serial Recall")
        self.root.geometry("1600x900")
        self.root.resizable(False, False)

        self.Seriallist = Seriallist or []
        self.on_submit = on_submit

        # Internal logic + logger
        self.logic = MainLogic()
        self.logger = GameLogger()
        self.attempt = 0
        # Normal mode rounds
        self.normal_rounds_done = 0
        self.normal_rounds_target = 10
        # Speed mode schedule: 10s x5, 5s x5, 2.5s x5
        self.speed_schedule_ms = []
        self.speed_round_index = 0
        # Legacy counter removed: self.speed_rounds_done
        self.recall_time_ms = 5000  # default reveal time
        self.speed_mode_active = False
        self.memorypattern_active = False
        self.recall_start_time = None  # for speed mode adaptation
        self.input_start_time = None
        # MemoryPattern state
        self.pattern_game = None  # type: ignore[assignment]
        self.pattern_frame = None
        self.pattern_buttons = []
        self.pattern_click_enabled = False
        self.pattern_reveal_delay_ms = 600  # time each cell is lit
        self.pattern_gap_ms = 200           # gap between lights
        self.pattern_entered = []

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
        self.memorypattern_active = mode == "MemoryPattern"
        # reset per-start counters
        self.normal_rounds_done = 0
        self.speed_round_index = 0
        if self.memorypattern_active:
            # MemoryPattern flow: show serial first, then pattern, then input
            self.recall_time_ms = 5000
            self.Seriallist = self.logic.generate_serial()
            self._show_placeholders()
            self.recall_start_time = time.perf_counter()
            self.root.after(self.recall_time_ms, self._start_memorypattern)
        else:
            if self.speed_mode_active:
                self.speed_schedule_ms = [10000]*5 + [5000]*5 + [2500]*5
                self.recall_time_ms = self.speed_schedule_ms[0]
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
        self._show_input_fields()

    def _show_input_fields(self) -> None:
        # Destroy pattern grid if present
        if self.pattern_frame is not None:
            self.pattern_frame.destroy()
            self.pattern_frame = None
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

        if self.entries:
            self.entries[0].focus_set()

        self.SubmitButton()
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
        # Only check first and last positions
        first_val = values[0] if len(values) > 0 else None
        last_val = values[-1] if len(values) > 0 else None
        first_wrong = (first_val is None) or (len(self.Seriallist) > 0 and first_val != self.Seriallist[0])
        last_wrong = (last_val is None) or (len(self.Seriallist) > 0 and last_val != self.Seriallist[-1])
        input_time = None
        if self.input_start_time is not None:
            input_time = time.perf_counter() - self.input_start_time
        # Feedback (only report first/last status)
        msg = []
        msg.append("First OK" if not first_wrong else "First Wrong")
        msg.append("Last OK" if not last_wrong else "Last Wrong")
        color = "green" if not first_wrong and not last_wrong else "orange" if (first_wrong != last_wrong) else "red"
        self.feedback_label.config(text=" | ".join(msg), fg=color)
        # Attempt counter
        self.attempt += 1
        # Compute how many numbers are wrong in total (ignoring empty cells)
        round_wrong_total = 0
        for i, s in enumerate(self.Seriallist):
            if i < len(values) and values[i] is not None and s != values[i]:
                round_wrong_total += 1
        # Log (per-mode files)
        self.logger.log_attempt(
            attempt=self.attempt,
            mode=self.selected_gamemode.get(),
            serial=self.Seriallist,
            user_input=values,
            first_wrong=first_wrong,
            last_wrong=last_wrong,
            round_wrong_total=round_wrong_total,
        )
        # Update round counters and decide next action
        if self.memorypattern_active:
            self.memorypattern_rounds_done = getattr(self, 'memorypattern_rounds_done', 0) + 1
            setattr(self, 'memorypattern_rounds_done', self.memorypattern_rounds_done)
            if self.memorypattern_rounds_done >= 10:
                self._finish_mode()
                return
        elif self.speed_mode_active:
            self.speed_round_index += 1
            if self.speed_round_index >= len(self.speed_schedule_ms):
                self._finish_mode()
                return
        else:
            self.normal_rounds_done += 1
            if self.normal_rounds_done >= self.normal_rounds_target:
                self._finish_mode()
                return
        # Prepare next round after delay
        self.root.after(3000, self._next_round)

    def _next_round(self):
        # Cleanup existing input frame
        if self.input_frame is not None:
            self.input_frame.destroy()
            self.input_frame = None
        if self.memorypattern_active:
            # Start another MemoryPattern round: show serial, then pattern
            if getattr(self, 'memorypattern_rounds_done', 0) >= 10:
                self._finish_mode()
                return
            self.recall_time_ms = 5000
            self.Seriallist = self.logic.generate_serial()
            self._show_placeholders()
            self.recall_start_time = time.perf_counter()
            self.root.after(self.recall_time_ms, self._start_memorypattern)
        else:
            # Adjust speed mode timing using schedule
            if self.speed_mode_active:
                if self.speed_round_index >= len(self.speed_schedule_ms):
                    self._finish_mode()
                    return
                self.recall_time_ms = self.speed_schedule_ms[self.speed_round_index]
            else:
                self.recall_time_ms = 5000
            # Generate new serial
            self.Seriallist = self.logic.generate_serial()
            # Show placeholders
            self._show_placeholders()
            self.recall_start_time = time.perf_counter()
            self.root.after(self.recall_time_ms, self._swap_to_inputs)

    def _finish_mode(self):
        # Clean up UI
        if self.placeholder_frame is not None:
            self.placeholder_frame.destroy()
            self.placeholder_frame = None
        if self.input_frame is not None:
            self.input_frame.destroy()
            self.input_frame = None
        if self.pattern_frame is not None:
            self.pattern_frame.destroy()
            self.pattern_frame = None
        # Feedback and reset controls
        mode = "MemoryPattern" if self.memorypattern_active else ("Speed" if self.speed_mode_active else "Normal")
        self.feedback_label.config(text=f"{mode} completed.", fg="purple")
        self.gamemode_menu.config(state="normal")
        self.start_button.config(state="normal")
        self.game_started = False

    # ---------- MemoryPattern mode ----------
    def _build_pattern_grid(self):
        # Destroy numeric UI frames if present
        if self.placeholder_frame is not None:
            self.placeholder_frame.destroy()
            self.placeholder_frame = None
        if self.input_frame is not None:
            self.input_frame.destroy()
            self.input_frame = None
        if self.buttons_frame is not None:
            self.buttons_frame.destroy()
            self.buttons_frame = None

        if self.pattern_frame is None:
            self.pattern_frame = tk.Frame(self.container)
            self.pattern_frame.pack(pady=10)

            self.pattern_buttons = []
            for r in range(3):
                for c in range(3):
                    idx = r * 3 + c
                    btn = tk.Button(
                        self.pattern_frame,
                        width=6,
                        height=3,
                        bg="#d9d9d9",
                        activebackground="#cccccc",
                        relief=tk.RAISED,
                        command=lambda i=idx: self._on_pattern_click(i),
                    )
                    btn.grid(row=r, column=c, padx=6, pady=6)
                    self.pattern_buttons.append(btn)

    def _start_memorypattern(self):
        if self.pattern_game is None:
            self.pattern_game = PatternGame()
        self._build_pattern_grid()
        # Generate a new sequence of length 6
        seq = self.pattern_game.new_round(sequence_len=6)
        self.pattern_entered = []
        self.pattern_click_enabled = False
        # Reveal the sequence
        self._reveal_sequence(seq, step=0)

    def _reveal_sequence(self, seq: List[int], step: int):
        # Clear all to default
        for btn in self.pattern_buttons:
            btn.configure(bg="#d9d9d9")
        if step >= len(seq):
            # Reveal done, enable clicking
            self.pattern_click_enabled = True
            return
        idx = seq[step]
        # Highlight this cell
        self.pattern_buttons[idx].configure(bg="#ffd54f")  # amber
        # Schedule to unhighlight and move to next
        self.root.after(self.pattern_reveal_delay_ms, lambda: self._after_reveal_gap(seq, step))

    def _after_reveal_gap(self, seq: List[int], step: int):
        # Turn all off again for the gap
        for btn in self.pattern_buttons:
            btn.configure(bg="#d9d9d9")
        self.root.after(self.pattern_gap_ms, lambda: self._reveal_sequence(seq, step + 1))

    def _on_pattern_click(self, idx: int):
        if not self.pattern_click_enabled or self.pattern_game is None:
            return
        correct, done = self.pattern_game.submit_click(idx)
        self.pattern_entered.append(idx)
        if correct:
            # Flash green briefly
            self.pattern_buttons[idx].configure(bg="#a5d6a7")
            self.root.after(150, lambda b=self.pattern_buttons[idx]: b.configure(bg="#d9d9d9"))
        else:
            # Flash red and keep waiting for correct one
            self.pattern_buttons[idx].configure(bg="#ef9a9a")
            self.root.after(200, lambda b=self.pattern_buttons[idx]: b.configure(bg="#d9d9d9"))

        if done:
            self.pattern_click_enabled = False
            # Prompt to enter the serial now
            self.feedback_label.config(text=f"Pattern complete (mistakes: {self.pattern_game.mistakes}). Enter the serial.", fg="blue")
            # Switch to input stage after a brief pause
            self.root.after(500, self._show_input_fields)


    def run(self) -> None:
        self.root.mainloop()
