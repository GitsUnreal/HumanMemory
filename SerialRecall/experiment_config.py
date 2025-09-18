# Configuration for Serial Recall Experiments

from dataclasses import dataclass

@dataclass
class Timing:
    item_on_ms: int = 750         # duration each item is shown
    isi_blank_ms: int = 250       # blank between items
    retention_ms: int = 200      # retention interval (default; overrides in certain tasks)
    iti_ms: int = 200             # inter-trial interval

@dataclass
class Design:
    trials_per_condition: int = 5
    # Choose one fixed list length or a list of possible lengths to randomize from:
    list_lengths = [10]            # classic span length; can change e.g., [5,6,7,8,9]
    randomize_block_order: bool = False
    # Item mode for baseline/error/suppression/tapping: "letters" or "digits" (letters match literature here)
    item_mode: str = "letters"

# Output
LOG_DIR = "data"
LOG_FILE = "serial_recall_log.csv"

# Keys
SUBMIT_KEY = "Return"    # ENTER to submit response
BACKSPACE_KEY = "BackSpace"
TAP_KEY = "space"

# UI
WINDOW_TITLE = "Serial Recall Experiment"
FONT_FAMILY = "Helvetica"
FONT_SIZE = 40
INSTRUCTION_FONT_SIZE = 18
