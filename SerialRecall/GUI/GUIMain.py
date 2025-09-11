import tkinter as tk
from typing import List, Callable, Optional


class GUIMain():
    """
    Simple GUI:
    - Initially shows 10 placeholders: "XX XX ..."
    - After 5 seconds, swaps to 10 input boxes where each box accepts 0-2 digits (0-99)
    """

    def __init__(self, Seriallist: Optional[List[int]] = None, on_submit: Optional[Callable[[List[int | None]], None]] = None):
        self.root = tk.Tk()
        self.root.title("Serial Recall")
        self.root.geometry("800x150")
        self.root.resizable(False, False)

        self.Seriallist = Seriallist or []
        self.on_submit = on_submit

        # Container for content
        self.container = tk.Frame(self.root, padx=10, pady=20)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.placeholder_frame = None
        self.input_frame = None
        self.entries = []
        self.buttons_frame = None

        self._show_placeholders()

        # After 5 seconds (5000 ms), swap to inputs
        self.root.after(5000, self._swap_to_inputs)

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
        # Delegate to external checker if provided; otherwise, just print for now.
        if self.on_submit is not None:
            self.on_submit(values)
        else:
            print("Submitted values:", values)


    def run(self) -> None:
        self.root.mainloop()
