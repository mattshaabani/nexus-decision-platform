"""Lending decision policy — separate from the scorecard model."""

from __future__ import annotations

from dataclasses import dataclass

from nexus.domain.models import DecisionOutcome


@dataclass(frozen=True)
class PolicyConfig:
    """Probability of default thresholds (illustrative defaults)."""

    approve_max_pd: float = 0.08
    refer_max_pd: float = 0.18
    default_lgd: float = 0.45  # loss given default
    # EAD ≈ requested exposure; caller supplies amount


@dataclass(frozen=True)
class PolicyDecision:
    outcome: DecisionOutcome
    pd: float
    lgd: float
    ead: float
    expected_loss: float
    policy_version: str = "policy-v1"


def expected_loss(pd: float, lgd: float, ead: float) -> float:
    return float(pd) * float(lgd) * float(ead)


def apply_policy(
    pd: float,
    *,
    ead: float,
    config: PolicyConfig | None = None,
    policy_version: str | None = None,
    force_refer: bool = False,
) -> PolicyDecision:
    """Map PD (+ optional flags) to APPROVE / REFER / DECLINE and EL."""
    cfg = config or PolicyConfig()
    lgd = cfg.default_lgd
    el = expected_loss(pd, lgd, ead)

    if force_refer:
        outcome = DecisionOutcome.REFER
    elif pd < cfg.approve_max_pd:
        outcome = DecisionOutcome.APPROVE
    elif pd < cfg.refer_max_pd:
        outcome = DecisionOutcome.REFER
    else:
        outcome = DecisionOutcome.DECLINE

    return PolicyDecision(
        outcome=outcome,
        pd=float(pd),
        lgd=lgd,
        ead=float(ead),
        expected_loss=el,
        policy_version=policy_version or "policy-v1",
    )