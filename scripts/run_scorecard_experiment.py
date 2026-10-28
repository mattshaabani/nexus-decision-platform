#!/usr/bin/env python3
"""Train scorecard → evaluate OOT → quality gate (Phase 1 demo)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus.adapters.mlflow_registry import log_scorecard_run, start_run
from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
from nexus.domain.evaluation import evaluate_predictions, out_of_time_split
from nexus.domain.fairness import four_fifths_and_eo
from nexus.domain.model_card import build_model_card, render_model_card_markdown
from nexus.domain.models import Decision, DecisionOutcome
from nexus.domain.monitoring import monitor_scores
from nexus.domain.scorecard import fit_scorecard

from nexus.adapters.champion_store import ChampionStore
from nexus.application.promote import evaluate_challenger, promote_if_passed


def make_synthetic(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # time axis
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    income = rng.normal(55_000, 18_000, n).clip(12_000, 200_000)
    age = rng.integers(22, 68, n)
    util = rng.uniform(0, 1, n)  # credit utilisation
    person_id = rng.integers(0, n // 3, n)  # ~3 rows per person
    protected = rng.integers(0, 2, n)  # binary protected group

    logit = (
        -1.8
        - 0.000035 * (income - 55_000)
        - 0.025 * (age - 40)
        + 1.4 * util
    )
    p = 1 / (1 + np.exp(-logit))
    y = rng.binomial(1, p)

    return pd.DataFrame(
        {
            "person_id": person_id,
            "application_date": dates,
            "income": income,
            "age": age,
            "utilisation": util,
            "default": y,
            "protected": protected,
        }
    )


def main() -> int:
    print("1. Generate synthetic data")
    df = make_synthetic()

    print("2. OOT split (train ≤ 2023-06, OOT ≥ 2023-08 — embargo July)")
    train, oot = out_of_time_split(
        df,
        "application_date",
        train_end="2023-06-30",
        oot_start="2023-08-01",
    )
    print(f"   train={len(train)}  oot={len(oot)}")

    features = ["income", "age", "utilisation"]
    print(f"3. Fit scorecard on train ({features})")
    sc = fit_scorecard(
        train,
        target="default",
        features=features,
        min_bin_size=40,
        max_bins=8,
    )
    for f, c in sc.coefficients.items():
        print(f"   coef[{f}] = {c:.4f}")

    print("4. Score OOT")
    proba = sc.predict_proba(oot)
    scores = sc.score(oot)
    y_oot = oot["default"].values
    pids = oot["person_id"].values

    ev = evaluate_predictions(y_oot, proba, person_ids=pids)
    print(
        f"   Gini={ev.gini:.4f}  Brier={ev.brier:.4f}  "
        f"n_obs={ev.n_obs}  n_persons={ev.n_persons}"
    )
    print(f"   score range: {scores.min():.1f} – {scores.max():.1f}")

    print("4b. Monitoring (train scores vs OOT scores)")
    train_scores = sc.score(train)
    mon = monitor_scores(
        baseline_scores=train_scores,
        live_scores=scores,
        live_y=y_oot,
        live_proba=proba,
        baseline_gini=evaluate_predictions(
            train["default"].values, sc.predict_proba(train)
        ).gini,
        psi_threshold=0.20,
        gini_drop_max=0.08,
    )
    print(
        f"   PSI={mon.psi_score:.4f}  gini_live={mon.gini_live:.4f}  "
        f"gini_base={mon.gini_baseline:.4f}"
    )
    if mon.alerts:
        for a in mon.alerts:
            print(f"   ALERT: {a}")
    else:
        print("   no alerts")

    print("5. Fairness (person-level)")
    fair = four_fifths_and_eo(
        pids,
        y_oot,
        proba,
        oot["protected"].values,
        approve_threshold=0.5,
    )
    print(
        f"   four_fifths={fair.four_fifths_ratio:.3f}  eo_gap={fair.eo_gap:.3f}  "
        f"n_a={fair.n_persons_a} n_b={fair.n_persons_b}"
    )

    print("6. Quality gate (champion–challenger)")
    metrics = {
        "gini": ev.gini,
        "brier": ev.brier,
        "psi": mon.psi_score,
        "four_fifths_ratio": fair.four_fifths_ratio,
        "eo_gap": fair.eo_gap,
    }
    store = ChampionStore("artifacts/champion.json")
    gate = evaluate_challenger("scorecard-v0.1.0", metrics, store)
    print(f"   gate={gate.status.value.upper()}")
    for m in gate.metrics:
        flag = "OK" if m.passed else "FAIL"
        print(f"   [{flag}] {m.name}={m.value:.4f}")
    if gate.blockers:
        for b in gate.blockers:
            print(f"   blocker: {b}")

    promoted = promote_if_passed(
        "scorecard-v0.1.0",
        metrics,
        gate,
        store,
        extra={"n_oot": len(oot)},
    )
    print(f"   promoted={promoted}  champion_file=artifacts/champion.json")

    print("7. Model card")
    card = build_model_card(
        "scorecard-v0.1.0",
        gate,
        training_window="2022-01-01 → 2023-06-30",
        evaluation_window="2023-08-01 → end",
        features=features,
    )
    md = render_model_card_markdown(card)
    out = Path("artifacts")
    out.mkdir(exist_ok=True)
    card_path = out / "model_card_scorecard-v0.1.0.md"
    card_path.write_text(md, encoding="utf-8")
    print(f"   written → {card_path}")

    print("8. Sample reason codes:", sc.score_one(oot.iloc[0]).reason_codes)
    print("8b. Audit log (sample 20 OOT decisions)")
    store = SqliteDecisionStore("artifacts/decisions.db")
    for i, (_, row) in enumerate(oot.head(20).iterrows()):
        result = sc.score_one(row)
        outcome = (
            DecisionOutcome.APPROVE
            if result.probability < 0.5
            else DecisionOutcome.DECLINE
        )
        store.save(
            Decision(
                decision_id=f"oot-{i}",
                person_id=str(row["person_id"]),
                model_version="scorecard-v0.1.0",
                score=result.score,
                probability=result.probability,
                outcome=outcome,
                reason_codes=list(result.reason_codes),
                features={f: float(row[f]) for f in features},
            )
        )
    print("   stored 20 decisions → artifacts/decisions.db")

    print("9. MLflow logging")
    tracking = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    with start_run(
        experiment_name="nexus-scorecard",
        run_name="scorecard-v0.1.0",
        tracking_uri=tracking,
    ):
        run_id = log_scorecard_run(
            scorecard=sc,
            metrics=metrics,
            gate=gate,
            model_card_markdown=md,
            params={
                "n_train": len(train),
                "n_oot": len(oot),
                "n_persons_oot": ev.n_persons,
            },
            artifact_dir=out,
        )
        print(f"   run_id={run_id}")
        print(f"   tracking={tracking}")

    return 0 if gate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())