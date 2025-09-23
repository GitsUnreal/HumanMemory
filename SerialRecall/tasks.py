
# Core GUI tasks (tkinter) for serial recall with per-position input boxes
import tkinter as tk
from tkinter import messagebox
import random
from typing import List, Dict, Any
from experiment_config import Timing, Design, TAP_KEY, WINDOW_TITLE, FONT_FAMILY, FONT_SIZE, INSTRUCTION_FONT_SIZE, LOG_DIR, LOG_FILE
from stimuli import sample_letters, sample_from_clusters, sample_words, score_serial_recall, PHONO_CLUSTERS, VISUAL_CLUSTERS
from logger import append_row_csv, timestamp
from participant_manager import load_next_participant_id, save_participant_id
import os
import json
import traceback

# Conditions
COND_BASELINE = "baseline_letters"
COND_ERROR_TYPES = "error_types_letters"
COND_CHUNKING = "chunking_words"
COND_SUPPRESSION = "articulatory_suppression"
COND_TAPPING = "finger_tapping"

# ALL_CONDITIONS = [COND_BASELINE, COND_ERROR_TYPES, COND_CHUNKING, COND_SUPPRESSION, COND_TAPPING]
ALL_CONDITIONS = [COND_BASELINE, COND_CHUNKING, COND_SUPPRESSION, COND_TAPPING]

def safe_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Error", f"An error occurred:\n{e}")
        return None

class SerialRecallApp:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.canvas = tk.Canvas(root, width=1200, height=800, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.label = tk.Label(root, text="", font=(FONT_FAMILY, FONT_SIZE), bg="white")
        self.label.place(relx=0.5, rely=0.45, anchor="center")

        self.instr = tk.Label(root, text="", font=(FONT_FAMILY, INSTRUCTION_FONT_SIZE), bg="white")
        self.instr.place(relx=0.5, rely=0.8, anchor="center")

        # Per-position response UI (the only input widgets used)
        self.response_frame = None
        self.response_boxes: List[tk.Entry] = []
        self.box_mode_active = False
        self.box_word_mode = False
        self.box_max_chars = 1

        self.submit_button = tk.Button(root, text="Submit", font=(FONT_FAMILY, 14), command=lambda: safe_call(self.collect_response))
        self.submit_button.place_forget()

        self.cont_button = tk.Button(root, text="Continue", font=(FONT_FAMILY, 16), command=lambda: safe_call(self._continue_button))
        self.cont_button.place_forget()

        self.timing = Timing()
        self.design = Design()

        # Participant and logging
        self.participant_id = None
        self.log_path = os.path.join(LOG_DIR, LOG_FILE)

        # State
        self.current_condition = None
        self.trial_index = 0
        self.block_conditions = ALL_CONDITIONS.copy()
        if self.design.randomize_block_order:
            random.shuffle(self.block_conditions)
        self.block_trials_remaining = self.design.trials_per_condition
        self.current_target: List[str] = []
        self.current_is_words = False
        self.tap_count = 0
        self.tapping_active = False

        # Global key bindings
        self.root.bind_all("<Return>", lambda e: safe_call(self._on_submit_or_continue, e))
        self.root.bind_all("<KP_Enter>", lambda e: safe_call(self._on_submit_or_continue, e))
        self.root.bind_all(f"<{TAP_KEY}>", lambda e: safe_call(self._on_tap, e))
        self.root.bind_all("<Button-1>", lambda e: safe_call(self._maybe_continue_mouse, e))

        self.show_welcome()

    def show_welcome(self):
        self.label.config(text="Serial Recall Experiments", font=(FONT_FAMILY, 48))
        self.instr.config(text="Press ENTER or click to begin")
        self._destroy_response_boxes()
        self._show_continue_button(self.start_without_prompt)

    def start_without_prompt(self):
        # Auto increment participant id without prompt
        pid = load_next_participant_id()
        self.participant_id = f"P{pid:03d}"
        save_participant_id(pid)
        self.start_next_block()

    def _show_continue_button(self, callback):
        self.pending_callback = callback
        self.cont_button.place(relx=0.5, rely=0.65, anchor="center")

    def _hide_continue_button(self):
        self.cont_button.place_forget()

    def _continue_button(self):
        self._trigger_pending_callback()

    def _trigger_pending_callback(self):
        cb = getattr(self, "pending_callback", None)
        self.pending_callback = None
        self._hide_continue_button()
        if cb:
            cb()

    def _on_submit_or_continue(self, event):
        # If box UI is visible, submit; otherwise continue
        if self.box_mode_active and self.response_boxes:
            self.collect_response()
        else:
            self._trigger_pending_callback()

    def _maybe_continue_mouse(self, event):
        if not self.box_mode_active:
            self._trigger_pending_callback()

    def _on_tap(self, event):
        if self.tapping_active:
            self.tap_count += 1

    def start_next_block(self):
        if not self.block_conditions:
            self.end_experiment()
            return
        self.current_condition = self.block_conditions.pop(0)
        self.block_trials_remaining = self.design.trials_per_condition
        self.trial_index = 0
        block_name = self.current_condition.replace("_", " ").title()
        self._destroy_response_boxes()
        self.label.config(text=f"Starting block:\n{block_name}")
        self.instr.config(text="Press ENTER, click, or button to continue")
        self._show_continue_button(self.start_trial)

    def end_experiment(self):
        self._destroy_response_boxes()
        self.label.config(text="All blocks complete! 🎉", font=(FONT_FAMILY, 36))
        self.instr.config(text="You may close the window.")

    # Trial flow
    def start_trial(self):
        if self.block_trials_remaining <= 0:
            self.start_next_block()
            return
        self.trial_index += 1
        self.block_trials_remaining -= 1

        # Decide list length
        L = random.choice(self.design.list_lengths)

        # Build target sequence depending on condition
        cond = self.current_condition
        self.current_is_words = (cond == COND_CHUNKING)

        if cond == COND_BASELINE:
            target = sample_letters(L)
            retention_task = "none"
        elif cond == COND_ERROR_TYPES:
            if random.random() < 0.5:
                target = sample_from_clusters(L, PHONO_CLUSTERS)
            else:
                target = sample_from_clusters(L, VISUAL_CLUSTERS)
            retention_task = "none"
        elif cond == COND_CHUNKING:
            target = sample_words(L)
            retention_task = "none"
        elif cond == COND_SUPPRESSION:
            target = sample_letters(L)
            retention_task = "articulatory_suppression"
        elif cond == COND_TAPPING:
            target = sample_letters(L)
            retention_task = "finger_tapping"
        else:
            target = sample_letters(L)
            retention_task = "none"

        self.current_target = target
        self.tap_count = 0
        self.tapping_active = False

        # Present sequence (no fixation '+')
        self.present_sequence(target, retention_task)

    def present_sequence(self, target: List[str], retention_task: str):
        self._destroy_response_boxes()
        self._hide_continue_button()
        self.instr.config(text="")
        self.label.config(text="")
        self.root.update_idletasks()
        # brief blank pause for consistency
        self.root.after(500, lambda: self._present_items(target, retention_task, 0))

    def _present_items(self, target: List[str], retention_task: str, idx: int):
        if idx >= len(target):
            self.begin_retention(retention_task)
            return
        item = target[idx]
        self.label.config(text=item)
        self.root.update_idletasks()
        self.root.after(self.timing.item_on_ms, lambda: self._blank_then_next(target, retention_task, idx))

    def _blank_then_next(self, target: List[str], retention_task: str, idx: int):
        self.label.config(text="")
        self.root.update_idletasks()
        self.root.after(self.timing.isi_blank_ms, lambda: self._present_items(target, retention_task, idx+1))

    def begin_retention(self, retention_task: str):
        # Default duration
        duration_ms = self.timing.retention_ms
        if retention_task == "articulatory_suppression":
            duration_ms = 10000
            self.label.config(text="Repeat \"tah-dah\" silently", font=(FONT_FAMILY, 30))
            self.instr.config(text="Keep repeating until the response screen appears")
            self.tapping_active = False
            self.root.after(duration_ms, self.prompt_response)
        elif retention_task == "finger_tapping":
            duration_ms = 10000
            self.label.config(text="Tap SPACE repeatedly", font=(FONT_FAMILY, 30))
            self.instr.config(text="Keep tapping; we'll continue after you've tapped at least once")
            self.tapping_active = True
            def check_end():
                if self.tap_count > 0:
                    self.prompt_response()
                else:
                    self.instr.config(text="No taps detected yet — press SPACE to continue")
                    self.root.after(500, check_end)
            self.root.after(duration_ms, check_end)
        else:
            self.label.config(text="", font=(FONT_FAMILY, 30))
            self.instr.config(text="")
            self.root.after(duration_ms, self.prompt_response)

    # ===== Response UI: per-position boxes =====
    def prompt_response(self):
        self.tapping_active = False  # stop counting taps

        n_boxes = len(self.current_target)
        self._destroy_response_boxes()
        self.response_frame = tk.Frame(self.root, bg="white")
        self.response_frame.place(relx=0.5, rely=0.6, anchor="center")

        if self.current_is_words:
            self.box_word_mode = True
            self.box_max_chars = 3
            self.label.config(text="Type the words in order")
            self.instr.config(text="One word per box (3 letters). Example: CAT | DOG | JOB  —  Press ENTER or Submit")
        else:
            self.box_word_mode = False
            self.box_max_chars = 1
            self.label.config(text="Type the letters in order")
            self.instr.config(text="One letter per box. Example: F | Z | M | W | R | T | K  —  Press ENTER or Submit")

        self.response_boxes = []
        self.box_mode_active = True

        for i in range(n_boxes):
            width = 4 if self.box_word_mode else 2
            e = tk.Entry(self.response_frame, font=(FONT_FAMILY, 28), width=width, justify="center")
            e.grid(row=0, column=i, padx=6, pady=6)
            e.bind("<KeyRelease>", lambda ev, idx=i: self._on_box_key(ev, idx))
            e.bind("<FocusIn>", lambda ev, idx=i: ev.widget.select_range(0, 'end'))
            self.response_boxes.append(e)

        if self.response_boxes:
            self.response_boxes[0].focus_set()
        self.submit_button.place(relx=0.5, rely=0.75, anchor="center")

    def _destroy_response_boxes(self):
        try:
            if self.response_frame is not None:
                self.response_frame.destroy()
            self.response_frame = None
            self.response_boxes = []
            self.box_mode_active = False
            self.submit_button.place_forget()
        except Exception:
            pass

    def _focus_box(self, idx: int):
        if 0 <= idx < len(self.response_boxes):
            w = self.response_boxes[idx]
            w.focus_set()
            w.icursor('end')
            w.select_range(0, 'end')

    def _next_box(self, idx: int):
        self._focus_box(min(idx + 1, len(self.response_boxes) - 1))

    def _prev_box(self, idx: int):
        self._focus_box(max(idx - 1, 0))

    def _on_box_key(self, event, idx: int):
        w = self.response_boxes[idx]
        text = w.get().upper()
        filtered = "".join(ch for ch in text if ch.isalpha())
        if len(filtered) > self.box_max_chars:
            filtered = filtered[:self.box_max_chars]
        if filtered != text:
            w.delete(0, 'end')
            w.insert(0, filtered)

        key = event.keysym

        if key in ("Left", "Up"):
            self._prev_box(idx)
            return
        if key in ("Right", "Down", "Tab"):
            self._next_box(idx)
            return
        if key == "BackSpace":
            if w.get() == "" and idx > 0:
                self._prev_box(idx)
            return

        if len(w.get()) >= self.box_max_chars and idx < len(self.response_boxes) - 1 and key not in ("Left","Right","Up","Down"):
            self._next_box(idx)

    def collect_response(self):
        # Read response from per-position boxes, preserving blanks for alignment
        if self.box_mode_active and self.response_boxes:
            if self.box_word_mode:
                resp_list = [bx.get().strip().upper() for bx in self.response_boxes]  # may include ""
            else:
                resp_list = [bx.get().strip().upper()[:1] for bx in self.response_boxes]  # may include ""
        else:
            # Fallback (shouldn't be used now)
            resp_list = []

        target = self.current_target
        score = score_serial_recall(target, resp_list)

        # Log trial
        row = self._build_log_row(target, resp_list, score)
        append_row_csv(self.log_path, row)

        # Feedback & next
        feedback = f"Correct positions: {score['n_correct']} / {len(target)}"
        self.label.config(text=feedback)
        self.instr.config(text="Press ENTER or click for next trial")
        self._destroy_response_boxes()
        self._show_continue_button(self.start_trial)

    def _build_log_row(self, target, response, score) -> Dict[str, Any]:
        cond = self.current_condition
        is_words = self.current_is_words
        row = {
            "timestamp_utc": timestamp(),
            "participant": self.participant_id,
            "condition": cond,
            "is_words": int(is_words),
            "trial_index_in_block": self.trial_index,
            "target_length": len(target),
            "target": "|" + "||".join(target) + "|",
            "response": "|" + "||".join(response) + "|",
            "prop_correct": score["prop_correct"],
            "n_correct": score["n_correct"],
            "all_or_nothing": score["all_or_nothing"],
            "pos_correct": json.dumps(score["pos_correct"]),
            "item_on_ms": self.timing.item_on_ms,
            "isi_blank_ms": self.timing.isi_blank_ms,
            "retention_ms": self.timing.retention_ms,
            "iti_ms": self.timing.iti_ms,
            "taps": self.tap_count,
        }
        return row
