"""Sign-constrained logistic scorecard + PDO scaling + reason codes."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from nexus.domain.scorecard.binning import BinningResult, fit_woe_bins


@dataclass(frozen=True)
class ScorecardResult:
    """One scored observation."""

    score: float
    probability: float
    reason_codes: tuple[str, ...]

@dataclass
class Scorecard:
    """Fitted WoE logistic scorecard with PDO scaling."""

    features: tuple[str, ...]
    binnings: dict[str, BinningResult]
    coefficients: dict[str, float]  # feature → beta
    intercept: float
    # PDO scaling
    base_score: float = 600.0
    pdo: float = 20.0  # points to double the odds
    base_odds: float = 50.0  # odds at base_score

    # derived
    factor: float = field(init=False)
    offset: float = field(init=False)

    def __post_init__(self) -> None:
        # score = offset - factor * log(odds)
        # factor = pdo / log(2)
        object.__setattr__(self, "factor", self.pdo / np.log(2))
        object.__setattr__(
            self,
            "offset",
            self.base_score - self.factor * np.log(self.base_odds),
        )

    def _woe_matrix(self, df: pd.DataFrame) -> np.ndarray:
        cols = []
        for f in self.features:
            cols.append(self.binnings[f].transform(df[f]))
        return np.column_stack(cols)

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """P(bad) for each row."""
        X = self._woe_matrix(df)
        logits = self.intercept + X @ np.array([self.coefficients[f] for f in self.features])
        return 1.0 / (1.0 + np.exp(-logits))

    def score(self, df: pd.DataFrame) -> np.ndarray:
        """Scaled score (higher = better / lower risk)."""
        p = self.predict_proba(df)
        # avoid 0/1
        p = np.clip(p, 1e-6, 1 - 1e-6)
        odds = (1 - p) / p  # good:bad
        return self.offset + self.factor * np.log(odds)

    def reason_codes(self, row: pd.Series, top_k: int = 3) -> tuple[str, ...]:
        """Top-k features that most hurt the score (most negative contribution)."""
        contribs: list[tuple[str, float]] = []
        for f in self.features:
            woe = float(self.binnings[f].transform(pd.Series([row[f]]))[0])
            beta = self.coefficients[f]
            # contribution to logit (higher → higher P(bad) → worse)
            contribs.append((f, beta * woe))
        # most positive contrib to P(bad) = worst for applicant
        contribs.sort(key=lambda t: t[1], reverse=True)
        return tuple(f"RC:{name}" for name, _ in contribs[:top_k])

    def score_one(self, row: pd.Series, top_k: int = 3) -> ScorecardResult:
        df = row.to_frame().T
        sc = float(self.score(df)[0])
        pr = float(self.predict_proba(df)[0])
        rc = self.reason_codes(row, top_k=top_k)
        return ScorecardResult(score=sc, probability=pr, reason_codes=rc)

def fit_scorecard(
    df: pd.DataFrame,
    target: str,
    features: list[str],
    *,
    max_bins: int = 10,
    min_bin_size: int = 50,
    base_score: float = 600.0,
    pdo: float = 20.0,
    base_odds: float = 50.0,
    C: float = 1.0,
) -> Scorecard:
    """Fit a sign-constrained WoE logistic scorecard.

    Sign constraint: after WoE transform, coefficients are forced ≥ 0
    so higher WoE (more bad-like) always increases P(bad).
    """
    y = df[target].astype(int).values

    binnings: dict[str, BinningResult] = {}
    woe_cols = {}
    for f in features:
        br = fit_woe_bins(
            f, df[f], y, max_bins=max_bins, min_bin_size=min_bin_size, monotonic=True
        )
        binnings[f] = br
        woe_cols[f] = br.transform(df[f])

    X = np.column_stack([woe_cols[f] for f in features])

    # LogisticRegression with non-negative coefficients (sign constraint)
    clf = LogisticRegression(
        C=C,
        fit_intercept=True,
        solver="lbfgs",
        max_iter=1000,
    )
    clf.fit(X, y)

    raw_coef = clf.coef_.ravel()
    # Enforce ≥ 0 (if a coef went negative, clip to 0 — feature drops out)
    coefs = {
        f: float(max(0.0, c)) for f, c in zip(features, raw_coef, strict=True)
    }

    
    return Scorecard(
        features=tuple(features),
        binnings=binnings,
        coefficients=coefs,
        intercept=float(clf.intercept_[0]),
        base_score=base_score,
        pdo=pdo,
        base_odds=base_odds,
    )