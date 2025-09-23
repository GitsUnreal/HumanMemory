import csv
import os
from datetime import datetime
from typing import List, Dict


class GameLogger:
	"""CSV logger with one file per mode.

	Columns per file:
	- timestamp, attempt, serial, user_input,
	- first_wrong_attempt (0/1), last_wrong_attempt (0/1), numbers_wrong_attempt (int),
	- first_wrong_total (cumulative), last_wrong_total (cumulative), numbers_wrong_total (cumulative)
	- speed_ms (only for Speed mode; blank otherwise)

	Note: Files are named `game_log_<mode>.csv` using the lowercased mode string.
	"""

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
			with open(path, mode="w", newline="", encoding="utf-8") as f:
				writer = csv.writer(f)
				writer.writerow([
					"timestamp",
					"attempt",
					"serial",
					"user_input",
					"pattern_correct",  # new column for MemoryPattern mode
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
		user_input: List[int | None],
		first_wrong: bool,
		last_wrong: bool,
		numbers_wrong_attempt: int,
		speed_ms: int | None = None,
		pattern_correct: bool | None = None,
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
		self._numbers_wrong_totals[mode] += int(numbers_wrong_attempt)

		# Write row
		path = self._file_for_mode(mode)
		with open(path, mode="a", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			writer.writerow([
				datetime.utcnow().isoformat(),
				attempt,
				" ".join(map(str, serial)),
				" ".join("" if v is None else str(v) for v in user_input),
				(1 if pattern_correct else 0) if pattern_correct is not None else "",
				1 if first_wrong else 0,
				1 if last_wrong else 0,
				int(numbers_wrong_attempt),
				self._first_wrong_totals[mode],
				self._last_wrong_totals[mode],
				self._numbers_wrong_totals[mode],
				speed_ms if (mode.lower() == "speed" and speed_ms is not None) else "",
			])
