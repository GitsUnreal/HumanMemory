"""
Aggregate serial recall experiment results by condition and compute:
- count
- mean of n_correct
- quartiles (Q1, median, Q3)
- 95% confidence interval for the mean (t-based if SciPy is available; normal 1.96 fallback otherwise)

Input is assumed to be at: data/serial_recall_log.csv
Outputs:
- data/analysis.csv (summary stats per condition)
- data/errors_top10.csv (top-10 letter-substitution errors pooled across all conditions, excluding 'chunking_words')
"""

import re
from collections import Counter
from pathlib import Path
import pandas as pd
import numpy as np

EXPECTED_LABELS = {
    "baseline_letters",
    "chunking_word",
    "chunking_words",  # in case the file uses plural
    "articulatory_suppression",
    "finger_tapping",
}

TYPE_GUESS_COLUMNS = ["condition", "experiment_type", "experiment", "type"]
SCORE_GUESS_COLUMNS = ["n_correct", "correct", "num_correct", "nCorrect", "N_correct"]


def find_type_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        vals = set(str(v) for v in df[col].dropna().unique())
        if any(label in vals for label in EXPECTED_LABELS):
            return col
    for guess in TYPE_GUESS_COLUMNS:
        if guess in df.columns:
            return guess
    raise ValueError("Couldn't find experiment type column.")


def find_score_column(df: pd.DataFrame) -> str:
    for guess in SCORE_GUESS_COLUMNS:
        if guess in df.columns:
            return guess
    candidates = [c for c in df.columns if c.lower().startswith("n_") or "correct" in c.lower()]
    if candidates:
        return candidates[0]
    raise ValueError("Couldn't find n_correct column.")


def mean_ci_95(series: pd.Series):
    x = series.dropna().astype(float).values
    n = len(x)
    if n == 0:
        return (np.nan, np.nan, np.nan)
    mean = float(np.mean(x))
    if n == 1:
        return (mean, np.nan, np.nan)

    sd = float(np.std(x, ddof=1))
    sem = sd / np.sqrt(n)

    try:
        from scipy.stats import t
        tcrit = float(t.ppf(0.975, df=n - 1))
    except Exception:
        tcrit = 1.96

    margin = tcrit * sem
    return (mean, mean - margin, mean + margin)


def compute_summary(df: pd.DataFrame, type_col: str, score_col: str) -> pd.DataFrame:
    df = df.copy()
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce")

    grouped = df.groupby(type_col)[score_col]

    rows = []
    for gname, s in grouped:
        q1 = float(s.quantile(0.25)) if s.notna().any() else np.nan
        q2 = float(s.quantile(0.50)) if s.notna().any() else np.nan
        q3 = float(s.quantile(0.75)) if s.notna().any() else np.nan
        mean, ci_low, ci_high = mean_ci_95(s)
        count = int(s.dropna().shape[0])
        rows.append({
            "experiment_type": str(gname),
            "n": count,
            "mean_n_correct": mean,
            "q1": q1,
            "median": q2,
            "q3": q3,
            "ci95_low": ci_low,
            "ci95_high": ci_high,
        })

    out = pd.DataFrame(rows).sort_values("experiment_type").reset_index(drop=True)
    return out


def _letters_from_piped_string(s: str):
    if not isinstance(s, str):
        return []
    letters = re.findall(r"\|([A-Za-z])\|", s)
    return [ch.upper() for ch in letters]


def compute_top_errors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count letter-substitution errors pooled across all conditions, excluding 'chunking_words'.
    """
    if "condition" not in df.columns:
        raise ValueError("Expected a 'condition' column to filter by experiment type.")

    filt = df["condition"].astype(str) != "chunking_words"
    sub = df.loc[filt].copy()

    counter = Counter()
    for _, row in sub.iterrows():
        tgt_letters = _letters_from_piped_string(row.get("target", ""))
        resp_letters = _letters_from_piped_string(row.get("response", ""))
        m = min(len(tgt_letters), len(resp_letters))
        for i in range(m):
            t, r = tgt_letters[i], resp_letters[i]
            if r and t and r != t and r.isalpha():
                key = f"{r} instead of {t}"
                counter[key] += 1

    top = counter.most_common(10)
    rows = [{"error": err, "count": cnt, "rank": rank} for rank, (err, cnt) in enumerate(top, start=1)]
    return pd.DataFrame(rows)


def main():
    input_path = Path("data/serial_recall_log.csv")
    output_path = Path("data/analysis.csv")

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    df = pd.read_csv(input_path)
    type_col = find_type_column(df)
    score_col = find_score_column(df)

    # Summary stats
    summary = compute_summary(df, type_col, score_col)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)

    # Error analysis (pooled, excluding chunking_words)
    errors_df = compute_top_errors(df)
    errors_path = Path("data/errors_top10.csv")
    errors_df.to_csv(errors_path, index=False)

    pd.set_option("display.max_columns", None)
    print(f"\nDetected type column: {type_col}")
    print(f"Detected score column: {score_col}")
    print(f"Saved summary to: {output_path}")
    print(f"Saved error analysis to: {errors_path}\n")
    print("Summary (per condition):")
    print(summary.to_string(index=False))
    if not errors_df.empty:
        print("\nTop-10 errors (pooled across all conditions, excluding 'chunking_words'):")
        print(errors_df.to_string(index=False))
    else:
        print("\n(No errors found)")


if __name__ == "__main__":
    main()
