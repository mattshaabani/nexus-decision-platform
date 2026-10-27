"""Person-level fairness metrics — pure domain."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FairnessResult:
    four_fifths_ratio: float
    eo_gap: float  # |TPR_group_a - TPR_group_b|
    approval_rate_a: float
    approval_rate_b: float
    tpr_a: float
    tpr_b: float
    n_persons_a: int
    n_persons_b: int
    notes: str = ""


def _person_aggregate(
    person_ids: np.ndarray,
    y_true: np.ndarray,
    y_pred_approve: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Collapse to one row per person: any default → bad; any approve → approved."""
    person_ids = np.asarray(person_ids)
    y_true = np.asarray(y_true).astype(int)
    y_pred_approve = np.asarray(y_pred_approve).astype(bool)

    persons, inv = np.unique(person_ids, return_inverse=True)
    n = len(persons)
    bad = np.zeros(n, dtype=int)
    approved = np.zeros(n, dtype=bool)
    for i in range(len(person_ids)):
        bad[inv[i]] = max(bad[inv[i]], y_true[i])
        approved[inv[i]] = approved[inv[i]] or y_pred_approve[i]
    return persons, bad, approved


def four_fifths_and_eo(
    person_ids: np.ndarray,
    y_true: np.ndarray,
    y_prob: np.ndarray,
    protected: np.ndarray,
    *,
    approve_threshold: float = 0.5,
    group_a_value: int | str = 0,
    group_b_value: int | str = 1,
) -> FairnessResult:
    """Compute four-fifths ratio and equal-opportunity gap at person level.

    Approval = P(bad) < approve_threshold  (lower risk → approve).
    Four-fifths: min(rate_a, rate_b) / max(rate_a, rate_b).
    EO gap: |TPR_a - TPR_b| where TPR = approve rate among people who did not default.
    """
    person_ids = np.asarray(person_ids)
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    protected = np.asarray(protected)

    approve = y_prob < approve_threshold
    persons, bad, approved = _person_aggregate(person_ids, y_true, approve)

    # map person → protected (first occurrence)
    person_to_idx = {p: i for i, p in enumerate(person_ids)}
    prot_person = np.array([protected[person_to_idx[p]] for p in persons])

    mask_a = prot_person == group_a_value
    mask_b = prot_person == group_b_value

    def _rates(mask: np.ndarray) -> tuple[float, float, int]:
        if mask.sum() == 0:
            return 0.0, 0.0, 0
        app_rate = float(approved[mask].mean())
        # TPR among non-defaults (good people correctly approved)
        goods = mask & (bad == 0)
        tpr = float(approved[goods].mean()) if goods.sum() > 0 else 0.0
        return app_rate, tpr, int(mask.sum())

    rate_a, tpr_a, n_a = _rates(mask_a)
    rate_b, tpr_b, n_b = _rates(mask_b)

    if max(rate_a, rate_b) < 1e-9:
        ratio = 1.0
    else:
        ratio = min(rate_a, rate_b) / max(rate_a, rate_b)

    return FairnessResult(
        four_fifths_ratio=float(ratio),
        eo_gap=float(abs(tpr_a - tpr_b)),
        approval_rate_a=rate_a,
        approval_rate_b=rate_b,
        tpr_a=tpr_a,
        tpr_b=tpr_b,
        n_persons_a=n_a,
        n_persons_b=n_b,
    )