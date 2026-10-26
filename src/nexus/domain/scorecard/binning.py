"""Monotonic Weight-of-Evidence (WoE) binning — pure domain, no I/O."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

@dataclass(frozen=True)
class Bin:
    """One bin for a single feature."""

    feature: str
    bin_id: int
    lower: float  # inclusive; -inf for first bin
    upper: float  # exclusive; +inf for last bin
    woe: float
    iv_contribution: float
    n_goods: int
    n_bads: int
    n_total: int

@dataclass(frozen=True)
class BinningResult:
    """Result of WoE binning for one feature."""

    feature: str
    bins: tuple[Bin, ...]
    iv: float  # total Information Value

    def transform(self, values: pd.Series | np.ndarray) -> np.ndarray:
        """Map raw values → WoE."""
        x = np.asarray(values, dtype=float)
        out = np.full(x.shape, np.nan, dtype=float)
        for b in self.bins:
            mask = (x >= b.lower) & (x < b.upper)
            out[mask] = b.woe
        # NaN / unseen → 0.0 WoE (neutral)
        out[np.isnan(out)] = 0.0
        return out

def _safe_woe(n_good: float, n_bad: float, total_good: float, total_bad: float) -> float:
    """WoE = ln(bad_rate / good_rate) with Laplace smoothing.

    Higher WoE ⇒ more bad-like ⇒ riskier. Positive logistic coefs then make sense.
    """
    g = (n_good + 0.5) / (total_good + 1.0)
    b = (n_bad + 0.5) / (total_bad + 1.0)
    return float(np.log(b / g))

def fit_woe_bins(
    feature: str,
    x: pd.Series | np.ndarray,
    y: pd.Series | np.ndarray,
    *,
    max_bins: int = 10,
    min_bin_size: int = 50,
    monotonic: bool = True,
) -> BinningResult:
    """Fit monotonic (optional) WoE bins for one numeric feature.

    Parameters
    ----------
    feature:
        Feature name.
    x:
        Feature values.
    y:
        Binary target (1 = bad/default, 0 = good).
    max_bins:
        Upper bound on number of bins.
    min_bin_size:
        Minimum observations per bin.
    monotonic:
        If True, enforce monotonic WoE with respect to bin order
        (required for regulated scorecards).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=int)

    mask = ~np.isnan(x)
    x_valid = x[mask]
    y_valid = y[mask]

    if len(x_valid) == 0:
        raise ValueError(f"Feature '{feature}' has no non-null values")

    total_good = float((y_valid == 0).sum())
    total_bad = float((y_valid == 1).sum())
    if total_good == 0 or total_bad == 0:
        raise ValueError(f"Feature '{feature}': target has only one class")

    # Initial quantile cuts
    n_bins = min(max_bins, max(2, len(x_valid) // min_bin_size))
    quantiles = np.linspace(0, 1, n_bins + 1)
    edges = np.unique(np.quantile(x_valid, quantiles))
    if len(edges) < 3:
        edges = np.array([x_valid.min(), x_valid.max() + 1e-9])

    edges[0] = -np.inf
    edges[-1] = np.inf

    # Build provisional bins
    provisional: list[dict] = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        m = (x_valid >= lo) & (x_valid < hi)
        n_g = int((y_valid[m] == 0).sum())
        n_b = int((y_valid[m] == 1).sum())
        n_t = int(m.sum())
        if n_t == 0:
            continue
        woe = _safe_woe(n_g, n_b, total_good, total_bad)
        provisional.append(
            {"lo": lo, "hi": hi, "n_g": n_g, "n_b": n_b, "n_t": n_t, "woe": woe}
        )

    # Merge tiny bins into neighbours
    merged: list[dict] = []
    for p in provisional:
        if merged and p["n_t"] < min_bin_size:
            prev = merged[-1]
            prev["hi"] = p["hi"]
            prev["n_g"] += p["n_g"]
            prev["n_b"] += p["n_b"]
            prev["n_t"] += p["n_t"]
            prev["woe"] = _safe_woe(prev["n_g"], prev["n_b"], total_good, total_bad)
        else:
            merged.append(dict(p))

        # Enforce monotonic WoE along bin order (direction = sign of last-first)
    if monotonic and len(merged) > 2:
        direction = np.sign(merged[-1]["woe"] - merged[0]["woe"])
        if direction == 0:
            direction = 1
        changed = True
        while changed and len(merged) > 1:
            changed = False
            i = 0
            while i < len(merged) - 1:
                diff = merged[i + 1]["woe"] - merged[i]["woe"]
                if diff * direction < 0:  # violation
                    a, b = merged[i], merged[i + 1]
                    a["hi"] = b["hi"]
                    a["n_g"] += b["n_g"]
                    a["n_b"] += b["n_b"]
                    a["n_t"] += b["n_t"]
                    a["woe"] = _safe_woe(a["n_g"], a["n_b"], total_good, total_bad)
                    del merged[i + 1]
                    changed = True
                else:
                    i += 1

    bins: list[Bin] = []
    total_iv = 0.0
    for idx, m in enumerate(merged):
        g_rate = (m["n_g"] + 0.5) / (total_good + 1.0)
        b_rate = (m["n_b"] + 0.5) / (total_bad + 1.0)
        # WoE = ln(b/g) ⇒ IV contribution = (b_rate - g_rate) * WoE
        iv_part = (b_rate - g_rate) * m["woe"]
        total_iv += iv_part
        bins.append(
            Bin(
                feature=feature,
                bin_id=idx,
                lower=float(m["lo"]),
                upper=float(m["hi"]),
                woe=float(m["woe"]),
                iv_contribution=float(iv_part),
                n_goods=m["n_g"],
                n_bads=m["n_b"],
                n_total=m["n_t"],
            )
        )

    return BinningResult(feature=feature, bins=tuple(bins), iv=float(total_iv))