"""Tests for evaluation metrics and OOT split."""

import numpy as np
import pandas as pd
import pytest

from nexus.domain.evaluation import (
    brier_score,
    evaluate_predictions,
    gini_coefficient,
    out_of_time_split,
    psi,
)


def test_gini_perfect():
    y = np.array([0, 0, 1, 1])
    s = np.array([0.1, 0.2, 0.8, 0.9])
    assert gini_coefficient(y, s) == pytest.approx(1.0)


def test_gini_randomish():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 200)
    s = rng.random(200)
    g = gini_coefficient(y, s)
    assert -0.3 < g < 0.3


def test_brier_range():
    y = np.array([0, 1, 0, 1])
    p = np.array([0.1, 0.9, 0.2, 0.8])
    b = brier_score(y, p)
    assert 0 <= b <= 1


def test_evaluate_with_persons():
    y = np.array([0, 1, 0, 1, 0])
    p = np.array([0.2, 0.8, 0.3, 0.7, 0.1])
    pids = np.array(["a", "a", "b", "c", "c"])
    r = evaluate_predictions(y, p, person_ids=pids)
    assert r.n_obs == 5
    assert r.n_persons == 3
    assert r.gini >= 0


def test_psi_identical():
    x = np.random.default_rng(0).normal(size=500)
    assert psi(x, x) < 0.01


def test_oot_split():
    df = pd.DataFrame(
        {
            "dt": pd.date_range("2023-01-01", periods=12, freq="ME"),
            "y": range(12),
        }
    )
    train, oot = out_of_time_split(
        df, "dt", train_end="2023-06-30", oot_start="2023-08-01"
    )
    assert len(train) == 6
    assert len(oot) == 5