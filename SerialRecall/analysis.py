# Basic analysis for serial recall experiments
import os
import json
import math
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from experiment_config import LOG_DIR, LOG_FILE

DATA_PATH = os.path.join(LOG_DIR, LOG_FILE)
OUT_SUMMARY = os.path.join(LOG_DIR, "summary_by_condition.csv")
CONFUSION_DIR = os.path.join(LOG_DIR, "confusions")

def wilson_ci(k, n, alpha=0.05):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054 # approx for 95%
    phat = k / n
    denom = 1 + z**2/n
    center = (phat + z*z/(2*n)) / denom
    margin = z*math.sqrt(phat*(1-phat)/n + z*z/(4*n*n)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))

def explode_pos_correct(df):
    rows = []
    for _, r in df.iterrows():
        pos = json.loads(r["pos_correct"])
        for i, v in enumerate(pos):
            rows.append({"condition": r["condition"], "participant": r["participant"], "position": i+1, "correct": v})
    return pd.DataFrame(rows)

def summarize(df):
    g = df.groupby("condition").agg(
        trials=("prop_correct", "count"),
        mean_prop=("prop_correct", "mean")
    ).reset_index()
    ci_lo = []
    ci_hi = []
    for _, row in g.iterrows():
        sub = df[df["condition"] == row["condition"]]
        total_correct = int(sub["n_correct"].sum())
        total_positions = int((sub["target_length"]).sum())
        lo, hi = wilson_ci(total_correct, total_positions)
        ci_lo.append(lo)
        ci_hi.append(hi)
    g["ci95_lo"] = ci_lo
    g["ci95_hi"] = ci_hi
    return g

def confusion_matrices(df):
    os.makedirs(CONFUSION_DIR, exist_ok=True)
    for cond, sub in df[df["is_words"] == 0].groupby("condition"):
        counts = defaultdict(Counter)
        for _, r in sub.iterrows():
            target = r["target"].split("||")
            resp = r["response"].split("||")
            L = max(len(target), len(resp))
            for i in range(L):
                t = target[i] if i < len(target) else None
                s = resp[i] if i < len(resp) else None
                if t is None: continue
                if s is None: s = "<MISSING>"
                counts[t][s] += 1
        labels = sorted(set(k for k in counts.keys()) | set(x for c in counts.values() for x in c.keys()))
        mat = pd.DataFrame(0, index=labels, columns=labels)
        for t, row in counts.items():
            for s, v in row.items():
                if s not in mat.columns:
                    mat[s] = 0
                mat.loc[t, s] = v
        mat.to_csv(os.path.join(CONFUSION_DIR, f"confusion_{cond}.csv"))

def main():
    if not os.path.exists(DATA_PATH):
        print(f"No data found at {DATA_PATH}")
        return
    df = pd.read_csv(DATA_PATH)
    summ = summarize(df)
    print("=== Summary by condition ===")
    print(summ)
    summ.to_csv(OUT_SUMMARY, index=False)

    gp = df.groupby(["participant", "condition"]).agg(
        trials=("prop_correct", "count"),
        mean_prop=("prop_correct", "mean")
    ).reset_index()
    print("\n=== By participant & condition ===")
    print(gp)

    confusion_matrices(df)
    print(f"\nSaved confusion matrices in {CONFUSION_DIR}")
    print(f"\nSummary CSV saved to {OUT_SUMMARY}")

if __name__ == "__main__":
    main()
