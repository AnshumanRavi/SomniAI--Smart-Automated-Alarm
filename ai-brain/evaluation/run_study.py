"""Regenerate every reported evaluation table from one command.

    python evaluation/run_study.py --out results/

Real-data sections need `SOMNIAI_DATA_DIR` pointing at a directory holding
`lifesnaps.zip` and `pmdata/`; they are skipped if it is absent, so the
simulation half runs anywhere.

Each table lands as a CSV so the paper's figures and numbers trace back to a
file rather than to a console scroll.
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wake_plan  # noqa: E402
from evaluation import planner_eval, scenarios, simulation  # noqa: E402

DATA_DIR = os.environ.get("SOMNIAI_DATA_DIR", "")


def _write(df: pd.DataFrame, out_dir: str, name: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df)} rows)")


def simulation_tables(out_dir: str) -> None:
    print("[1/4] simulation: planner against exhaustive ground truth")
    df = simulation.study(scenarios.SCENARIOS)
    _write(df, out_dir, "simulation_grid")

    summary = pd.DataFrame([{
        "bedtime_optimal": df["bedtime_optimal"].mean(),
        "verdict_correct": df["verdict_correct"].mean(),
        "false_refusals": int(df["false_refusal"].sum()),
        "broken_promises": int(df["broken_promise"].sum()),
        "n": len(df),
    }])
    _write(summary, out_dir, "simulation_summary")
    _write(df.groupby("scenario", as_index=False).agg(
        bedtime_optimal=("bedtime_optimal", "mean"),
        verdict_correct=("verdict_correct", "mean"),
        false_refusals=("false_refusal", "sum"),
        broken_promises=("broken_promise", "sum")), out_dir, "simulation_by_scenario")


def budget_table(out_dir: str) -> None:
    print("[2/4] simulation: iteration-budget sensitivity")
    original = wake_plan._optimize_plan
    rows = []
    try:
        for budget in (3, 4, 6, 8):
            def patched(features, target, max_rounds=budget, _f=original):
                return _f(features, target, max_rounds=max_rounds)
            wake_plan._optimize_plan = patched
            # Ground truth must cover what the planner can reach at this budget.
            df = simulation.study(scenarios.SCENARIOS, max_steps=3 * budget)
            solved = df[df.truth_minimal_levers.notna() & df.planner_promises]
            rows.append({
                "max_rounds": budget,
                "verdict_correct": round(df.verdict_correct.mean(), 3),
                "false_refusals": int(df.false_refusal.sum()),
                "broken_promises": int(df.broken_promise.sum()),
                "bedtime_optimal": round(df.bedtime_optimal.mean(), 3),
                "exactly_minimal": round(
                    (solved.planner_levers == solved.truth_minimal_levers).mean(), 3),
            })
    finally:
        wake_plan._optimize_plan = original
    _write(pd.DataFrame(rows), out_dir, "simulation_budget")


def real_data_tables(out_dir: str) -> None:
    if not DATA_DIR or not os.path.isdir(DATA_DIR):
        print("[3/4] real data: SKIPPED (set SOMNIAI_DATA_DIR)")
        return
    from sklearn.ensemble import RandomForestClassifier

    from datasets import cache, wake_proxy
    from training import train_real

    print("[3/4] real data: calibration")
    ls = wake_proxy.wake_success(
        cache.lifesnaps_cached(os.path.join(DATA_DIR, "lifesnaps.zip")))
    feats = [c for c in train_real.available_features(ls) if c != "stress_level"]
    work = ls.dropna(subset=feats + ["wake_success"]).reset_index(drop=True)

    truths, probs = [], []
    for seed in range(5):
        tr, te = train_real.grouped_split(work, seed=seed)
        m = RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=8,
                                   random_state=seed, n_jobs=1).fit(
            tr[feats], tr.wake_success.astype(int))
        truths.append(te.wake_success.astype(int).values)
        probs.append(m.predict_proba(te[feats])[:, list(m.classes_).index(1)])
    y = pd.concat([pd.Series(t) for t in truths], ignore_index=True)
    p = pd.concat([pd.Series(v) for v in probs], ignore_index=True)
    _write(planner_eval.calibration_table(y, p), out_dir, "calibration_table")
    _write(pd.DataFrame([planner_eval.calibration_error(y, p)]), out_dir,
           "calibration_summary")

    print("[4/4] real data: refusal quality")
    frames = []
    for seed in range(3):
        tr, te = train_real.grouped_split(work, seed=seed)
        m = RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=8,
                                   random_state=seed, n_jobs=1).fit(
            tr[feats], tr.wake_success.astype(int))
        with planner_eval.planner_using(m, feats):
            frames.append(planner_eval.refusal_evaluation(
                te, feats, targets=(0.70, 0.80, 0.90, 0.95),
                max_nights_per_participant=8))
    _write(pd.concat(frames).groupby(["planner", "target"], as_index=False)
             .mean(numeric_only=True), out_dir, "refusal_quality")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results", help="directory for the CSVs")
    ap.add_argument("--skip-real", action="store_true",
                    help="simulation tables only")
    args = ap.parse_args()

    simulation_tables(args.out)
    budget_table(args.out)
    if not args.skip_real:
        real_data_tables(args.out)
    print(f"\ndone -> {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
