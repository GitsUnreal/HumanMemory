import random
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class GridPos:
	"""A 0-based position in a 3x3 grid.

	row: 0..2, col: 0..2
	index: 0..8 (derived as row*3 + col)
	"""
	row: int
	col: int

	@property
	def index(self) -> int:
		return self.row * 3 + self.col


class PatternGame:
	"""Core logic for a 3x3 pattern memory game.

	Contract:
	- Board: 3x3 grid, positions 0..8 (row-major).
	- A random sequence of length `sequence_len` (default 6) is generated.
	- The GUI can reveal the sequence one-by-one to the user.
	- Then the user clicks cells; we validate the order.

	Public API:
	- new_round(sequence_len=6) -> List[int]: generate and return the sequence (list of indices 0..8)
	- expected_index() -> Optional[int]: returns the index expected next, None if round completed
	- submit_click(idx:int) -> Tuple[bool, bool]: (is_correct, round_done)
	- progress() -> Tuple[int, int]: (current_step, total)
	- get_sequence() -> List[int]: returns the current round sequence
	- mistakes: count of mistakes in current round

	Error modes:
	- submit_click on no active round raises RuntimeError
	- invalid index raises ValueError
	"""

	def __init__(self, seed: Optional[int] = None) -> None:
		self._rng = random.Random(seed)
		self._sequence: List[int] = []
		self._cursor: int = 0
		self.mistakes: int = 0

	def new_round(self, sequence_len: int = 6) -> List[int]:
		if sequence_len <= 0:
			raise ValueError("sequence_len must be > 0")
		# Generate random sequence of 0..8
		self._sequence = [self._rng.randrange(0, 9) for _ in range(sequence_len)]
		self._cursor = 0
		self.mistakes = 0
		return list(self._sequence)

	def get_sequence(self) -> List[int]:
		return list(self._sequence)

	def expected_index(self) -> Optional[int]:
		if not self._sequence or self._cursor >= len(self._sequence):
			return None
		return self._sequence[self._cursor]

	def progress(self) -> Tuple[int, int]:
		return (self._cursor, len(self._sequence))

	def submit_click(self, idx: int) -> Tuple[bool, bool]:
		if not self._sequence:
			raise RuntimeError("No active round. Call new_round() first.")
		if not (0 <= idx <= 8):
			raise ValueError("Index must be in 0..8 for 3x3 grid")

		expected = self._sequence[self._cursor]
		correct = (idx == expected)
		if correct:
			self._cursor += 1
			round_done = self._cursor >= len(self._sequence)
			return True, round_done
		else:
			# Count mistake but do not advance; allow retry on same expected position
			self.mistakes += 1
			return False, False

