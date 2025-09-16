import csv
import os
from datetime import datetime
from typing import List


class GameLogger:
	"""CSV logger for game attempts.

	Tracks only first and last number errors and their cumulative totals.
	"""

	def __init__(self, file_path: str = "game_log.csv"):
		self.file_path = file_path
		self.total_first_wrong = 0
		self.total_last_wrong = 0

		file_exists = os.path.exists(self.file_path)
		if not file_exists:
			with open(self.file_path, mode="w", newline="", encoding="utf-8") as f:
				writer = csv.writer(f)
				writer.writerow([
					"timestamp",
					"attempt",
					"mode",
					"serial",
					"user_input",
					"first_wrong",
					"last_wrong",
					"cumulative_first_wrong",
					"cumulative_last_wrong",
					"recall_time_ms",
					"input_time_seconds",
				])

	def log_attempt(
		self,
		attempt: int,
		mode: str,
		serial: List[int],
		user_input: List[int | None],
		first_wrong: bool,
		last_wrong: bool,
		recall_time_ms: int,
		input_time_s: float | None,
	) -> None:
		# Update cumulative counters
		if first_wrong:
			self.total_first_wrong += 1
		if last_wrong:
			self.total_last_wrong += 1

		with open(self.file_path, mode="a", newline="", encoding="utf-8") as f:
			writer = csv.writer(f)
			writer.writerow([
				datetime.utcnow().isoformat(),
				attempt,
				mode,
				" ".join(map(str, serial)),
				" ".join("" if v is None else str(v) for v in user_input),
				1 if first_wrong else 0,
				1 if last_wrong else 0,
				self.total_first_wrong,
				self.total_last_wrong,
				recall_time_ms,
				f"{input_time_s:.3f}" if input_time_s is not None else "",
			])
