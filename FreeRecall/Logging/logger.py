import csv
import os
from datetime import datetime
from typing import List, Dict, Optional


class GameLogger:
    """CSV logger with one file per mode."""

    def __init__(self, base_prefix: str = "game_log"):
        self.base_prefix = base_prefix
        # Cumulative counters per mode
        self._first_wrong_totals: Dict[str, int] = {}
        self._last_wrong_totals: Dict[str, int] = {}
        self._numbers_wrong_totals: Dict[str, int] = {}

    def _file_for_mode(self, mode: str) -> str:
        return f"{self.base_prefix}_{mode.lower()}.csv"

    def _ensure_header(self, mode: str) -> None:
        path = self._file_for_mode(mode)
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "attempt",
                    "serial",
                    "user_input",
                    "pattern_correct",
                    "first_wrong_attempt",
                    "last_wrong_attempt",
                    "numbers_wrong_attempt",
                    "first_wrong_total",
                    "last_wrong_total",
                    "numbers_wrong_total",
                    "speed_ms",
                ])

    def log_attempt(
        self,
        attempt: int,
        mode: str,
        serial: List[int],
        user_input: List[Optional[int]],
        first_wrong: bool,
        last_wrong: bool,
        numbers_wrong_attempt: int,
        speed_ms: Optional[int] = None,
        pattern_correct: Optional[bool] = None,
    ) -> None:
        # Prepare file and counters
        self._ensure_header(mode)
        self._first_wrong_totals.setdefault(mode, 0)
        self._last_wrong_totals.setdefault(mode, 0)
        self._numbers_wrong_totals.setdefault(mode, 0)

        # Update cumulative counters
        if first_wrong:
            self._first_wrong_totals[mode] += 1
        if last_wrong:
            self._last_wrong_totals[mode] += 1
        self._numbers_wrong_totals[mode] += numbers_wrong_attempt

        # Write row
        path = self._file_for_mode(mode)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(),
                attempt,
                " ".join(map(str, serial)),
                " ".join(str(v) if v is not None else "" for v in user_input),
                1 if pattern_correct else (0 if pattern_correct is not None else ""),
                1 if first_wrong else 0,
                1 if last_wrong else 0,
                numbers_wrong_attempt,
                self._first_wrong_totals[mode],
                self._last_wrong_totals[mode],
                self._numbers_wrong_totals[mode],
                speed_ms if ("speed" in mode.lower() and speed_ms is not None) else "",
            ])
