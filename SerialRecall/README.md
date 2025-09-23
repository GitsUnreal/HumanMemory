# Serial Recall Experiments (Working Memory)
This repo contains a **tkinter-based** set of experiments to replicate classic findings about working memory:
- Limited capacity of working memory
- Error types (phonological vs visual similarity)
- Chunking (3-letter words vs single letters)
- Articulatory suppression
- Finger tapping

## What's included
- `experiment_config.py` — tweakable parameters.
- `stimuli.py` — stimulus pools and helpers.
- `logger.py` — robust CSV logger (appends, creates header if needed).
- `participant_manager.py` — auto-increment participant IDs (P001, P002, …).
- `tasks.py` — core trial/task logic (GUI with `tkinter`).
- `run_experiment.py` — the main entry point; runs all blocks.
- `analysis.py` — quick analysis utilities for computing accuracy and confidence intervals.

## Quick start
1. Ensure Python 3.9+ is installed. On Linux, you may need `sudo apt-get install python3-tk` for `tkinter`.
2. Open a terminal in this folder and run:
   ```bash
   python run_experiment.py
   ```
3. The program auto-assigns a **participant ID** (increments each run) and then runs **five blocks** (one per condition), each with the number of trials configured in `experiment_config.py` (default: 20 per condition).

## Conditions (blocks)
1. **Baseline** (letters; no secondary task)
2. **Chunking** (items = 3-letter high-frequency words; no secondary task)
3. **Articulatory Suppression** (letters; during retention, participants silently repeat “tah-dah” for **10 s**)
4. **Finger Tapping** (letters; during retention, participants tap SPACE for **10 s**; the task requires at least one tap to proceed)

> Notes:
> - All trials are **serial recall**: items appear one-by-one (no fixation symbol), then a retention interval, then the response screen.
> - **Response entry instructions** appear on the answer screen:
>   - **Letters**: type letters with **no spaces** (e.g., `FZMWRTK`), then press ENTER.
>   - **Words**: type words separated by **spaces or commas** (e.g., `CAT DOG JOB`), then press ENTER.
> - We log both **position-wise correctness** and full response strings.
> - Correctness is the **proportion of positions recalled in the correct serial position** per trial; we also log an **all-or-nothing** flag.

## Data logging
- File: `data/serial_recall_log.csv` (created if missing; appended otherwise).
- Each row = one trial with metadata: participant, condition, list length, exact sequence, response, per-position correctness vector, number of correct positions, timestamps, timing parameters, taps (for tapping), and more.

## Analysis
Once you have data, run:
```bash
python analysis.py
```
This writes a summary CSV in `data/summary_by_condition.csv` with 95% Wilson CIs and saves confusion matrices in `data/confusions/`.

## Design defaults
- **Items**: letters for most blocks (A–Z consonants) or 3-letter words for chunking.
- **Presentation rate**: item_on = 750 ms, ISI_blank = 250 ms.
- **Retention**: default 2 s; **10 s** for articulatory suppression and finger tapping.
- **Response**: edit allowed; ENTER submits.
- **Reps**: 20 per block; configurable in `experiment_config.py`.
