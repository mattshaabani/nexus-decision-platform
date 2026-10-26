"""Unit tests for scorecard domain."""

import numpy as np
import pandas as pd
import pytest

from nexus.domain.scorecard import fit_scorecard, fit_woe_bins

def _synthetic_data(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    income = rng.normal(50_000, 15_000, n).clip(10_000, 150_000)
    age = rng.integers(21, 70, n)
    # Higher default rate when income low / age low
    logit = -2.0 - 0.00004 * (income - 50_000) - 0.03 * (age - 40)
    p = 1 / (1 + np.exp(-logit))
    y = rng.binomial(1, p)
    return pd.DataFrame({"income": income, "age": age, "default": y})

def test_woe_bins_monotonic():
    df = _synthetic_data()
    result = fit_woe_bins("income", df["income"], df["default"], max_bins=5, min_bin_size=30)
    assert result.iv >= 0
    assert len(result.bins) >= 2
    woes = [b.woe for b in result.bins]
    # monotonic in one direction (no local reversals)
    diffs = np.diff(woes)
    assert np.all(diffs >= -1e-9) or np.all(diffs <= 1e-9)


def test_fit_scorecard_runs():
    df = _synthetic_data()
    sc = fit_scorecard(df, target="default", features=["income", "age"], min_bin_size=30)
    assert set(sc.features) == {"income", "age"}
    assert all(c >= 0 for c in sc.coefficients.values())

    scores = sc.score(df)
    assert len(scores) == len(df)
    assert scores.min() > 0

    proba = sc.predict_proba(df)
    assert np.all((proba >= 0) & (proba <= 1))

    one = sc.score_one(df.iloc[0])
    assert isinstance(one.score, float)
    assert len(one.reason_codes) <= 3