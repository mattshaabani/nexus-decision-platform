"""Evaluation metrics and OOT split helpers — pure domain."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def gini_coefficient(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Gini = 2 * AUC - 1."""
    y_true = np.asarray(y_true).ravel()
    y_score = np.asarray(y_score).ravel()
    if len(np.unique(y_true)) < 2:
        return 0.0
    auc = roc_auc_score(y_true, y_score)
    return float(2.0 * auc - 1.0)


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_prob = np.asarray(y_prob, dtype=float).ravel()
    return float(np.mean((y_prob - y_true) ** 2))


def psi(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Population Stability Index between two score distributions."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    breakpoints = np.unique(np.quantile(expected, np.linspace(0, 1, n_bins + 1)))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    def _share(x: np.ndarray) -> np.ndarray:
        counts = np.histogram(x, bins=breakpoints)[0].astype(float)
        shares = (counts + 0.5) / (counts.sum() + 0.5 * len(counts))
        return shares

    e, a = _share(expected), _share(actual)
    return float(np.sum((a - e) * np.log(a / e)))


@dataclass(frozen=True)
class EvalResult:
    gini: float
    brier: float
    n_obs: int
    n_persons: int | None = None


def evaluate_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    person_ids: np.ndarray | None = None,
) -> EvalResult:
    """Core metrics. If person_ids given, n_persons is reported (person-level honesty)."""
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n_persons = None
    if person_ids is not None:
        n_persons = int(len(np.unique(person_ids)))
    return EvalResult(
        gini=gini_coefficient(y_true, y_prob),
        brier=brier_score(y_true, y_prob),
        n_obs=int(len(y_true)),
        n_persons=n_persons,
    )


def out_of_time_split(
    df: pd.DataFrame,
    time_col: str,
    *,
    train_end: str | pd.Timestamp,
    oot_start: str | pd.Timestamp,
    oot_end: str | pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Temporal train / OOT split with optional embargo (gap between train_end and oot_start)."""
    t = pd.to_datetime(df[time_col])
    train_end = pd.Timestamp(train_end)
    oot_start = pd.Timestamp(oot_start)
    train = df[t <= train_end].copy()
    oot_mask = t >= oot_start
    if oot_end is not None:
        oot_mask &= t <= pd.Timestamp(oot_end)
    oot = df[oot_mask].copy()
    return train, oot