import csv
import os
from datetime import datetime
from typing import List, Dict, Optional


class GameLogger:
    """CSV logger with one file per mode."""

    def __init__(self, base_prefix: str = "game_log"):
        self.base_prefix = base_prefix
        # Cumulative counters per mode
        self._correct_numbers_totals: Dict[str, int] = {}
        self._first_correct_totals: Dict[str, int] = {}
        self._last_correct_totals: Dict[str, int] = {}

    def _file_for_mode(self, mode: str) -> str:
        return f"{self.base_prefix}_{mode.lower()}.csv"

    def calculate_correct_numbers(self, serial: List[int], user_input: List[Optional[int]]) -> int:
        """
        Calculate correct numbers using strict scoring methodology:
        - Count each user number, but limited by how many times it appears in the serial
        - Empty fields (None) count as WRONG answers (0 points)
        
        Example: If serial has [1,2,3,4,5] and user writes [1,2,None,None,5]:
        - Gets credit for 1, 2, 5 (3 correct)
        - Empty fields for positions 3,4 count as wrong (not added to score)
        - Total score: 3 out of 5
        """
        if not serial or not user_input:
            return 0
        
        # Extend user_input to match serial length if needed, filling with None
        if len(user_input) < len(serial):
            user_input = user_input + [None] * (len(serial) - len(user_input))
        
        # Filter out None values from user input for counting correct answers
        valid_user_input = [num for num in user_input if num is not None]
        
        # Count occurrences in both serial and user input
        from collections import Counter
        serial_counts = Counter(serial)
        user_counts = Counter(valid_user_input)
        
        # For each number, credit the minimum of what user wrote vs what's in serial
        correct_count = 0
        for number, user_count in user_counts.items():
            if number in serial_counts:
                # Credit up to the number of times this number appears in serial
                credit = min(user_count, serial_counts[number])
                correct_count += credit
        
        # Note: Empty fields (None values) automatically count as wrong 
        # because they don't contribute to correct_count
        return correct_count

    def calculate_wrong_numbers(self, serial: List[int], user_input: List[Optional[int]]) -> int:
        """
        Calculate wrong numbers (including empty fields as wrong):
        Total numbers in serial minus correct numbers = wrong numbers
        """
        if not serial:
            return 0
        
        correct_numbers = self.calculate_correct_numbers(serial, user_input)
        total_numbers = len(serial)
        wrong_numbers = total_numbers - correct_numbers
        
        return wrong_numbers

    def calculate_empty_fields(self, user_input: List[Optional[int]]) -> int:
        """
        Calculate how many fields the user left empty.
        This can be used to penalize incomplete responses if desired.
        """
        if not user_input:
            return 0
        return sum(1 for value in user_input if value is None)

    def calculate_completion_rate(self, user_input: List[Optional[int]]) -> float:
        """
        Calculate what percentage of fields the user filled in.
        Returns value between 0.0 and 1.0
        """
        if not user_input:
            return 0.0
        
        total_fields = len(user_input)
        filled_fields = sum(1 for value in user_input if value is not None)
        return filled_fields / total_fields

    def calculate_first_last_correct(self, serial: List[int], user_input: List[Optional[int]]) -> tuple[bool, bool]:
        """
        Calculate if user correctly included the first and last numbers from the serial
        """
        if not serial or not user_input:
            return False, False
        
        # Filter out None values from user input
        valid_user_input = [num for num in user_input if num is not None]
        
        if not valid_user_input:
            return False, False
        
        first_correct = serial[0] in valid_user_input
        last_correct = serial[-1] in valid_user_input
        
        return first_correct, last_correct

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
                    "correct_numbers",
                    "wrong_numbers",
                    "first_correct",
                    "last_correct",
                    "pattern_correct",
                    "correct_numbers_total",
                    "first_correct_total",
                    "last_correct_total",
                    "speed_ms",
                ])

    def log_attempt(
        self,
        attempt: int,
        mode: str,
        serial: List[int],
        user_input: List[Optional[int]],
        correct_numbers: int,
        wrong_numbers: int,
        first_correct: bool,
        last_correct: bool,
        speed_ms: Optional[int] = None,
        pattern_correct: Optional[bool] = None,
    ) -> None:
        # Prepare file and counters
        self._ensure_header(mode)
        self._correct_numbers_totals.setdefault(mode, 0)
        self._first_correct_totals.setdefault(mode, 0)
        self._last_correct_totals.setdefault(mode, 0)

        # Update cumulative counters
        self._correct_numbers_totals[mode] += correct_numbers
        if first_correct:
            self._first_correct_totals[mode] += 1
        if last_correct:
            self._last_correct_totals[mode] += 1

        # Write row
        path = self._file_for_mode(mode)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(),
                attempt,
                " ".join(map(str, serial)),
                " ".join(str(v) if v is not None else "" for v in user_input),
                correct_numbers,
                wrong_numbers,
                1 if first_correct else 0,
                1 if last_correct else 0,
                1 if pattern_correct else (0 if pattern_correct is not None else ""),
                self._correct_numbers_totals[mode],
                self._first_correct_totals[mode],
                self._last_correct_totals[mode],
                speed_ms if ("speed" in mode.lower() and speed_ms is not None) else "",
            ])

    def log_attempt_auto_calculate(
        self,
        attempt: int,
        mode: str,
        serial: List[int],
        user_input: List[Optional[int]],
        speed_ms: Optional[int] = None,
        pattern_correct: Optional[bool] = None,
    ) -> None:
        """
        Convenience method that automatically calculates all metrics
        """
        correct_numbers = self.calculate_correct_numbers(serial, user_input)
        wrong_numbers = self.calculate_wrong_numbers(serial, user_input)
        first_correct, last_correct = self.calculate_first_last_correct(serial, user_input)
        
        self.log_attempt(
            attempt=attempt,
            mode=mode,
            serial=serial,
            user_input=user_input,
            correct_numbers=correct_numbers,
            wrong_numbers=wrong_numbers,
            first_correct=first_correct,
            last_correct=last_correct,
            speed_ms=speed_ms,
            pattern_correct=pattern_correct,
        )

    def get_totals(self, mode: str) -> Dict[str, int]:
        """
        Get current cumulative totals for a mode
        """
        return {
            "correct_numbers_total": self._correct_numbers_totals.get(mode, 0),
            "first_correct_total": self._first_correct_totals.get(mode, 0),
            "last_correct_total": self._last_correct_totals.get(mode, 0),
        }

    def reset_totals(self, mode: str) -> None:
        """
        Reset cumulative totals for a mode (useful when starting a new session)
        """
        self._correct_numbers_totals[mode] = 0
        self._first_correct_totals[mode] = 0
        self._last_correct_totals[mode] = 0
