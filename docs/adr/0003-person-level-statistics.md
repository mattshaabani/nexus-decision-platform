# ADR-0003: Person-level Statistics & Cluster-Robust Uncertainty

**Status:** Accepted  
**Date:** 2026-10-25

## Context

Credit and underwriting data almost always contain multiple observations (applications, loans, time periods) that belong to the same person or entity. Treating every row as independent inflates degrees of freedom, understates standard errors, and produces over-confident fairness and performance claims.

## Decision

All primary evaluation metrics (Gini, calibration, fairness gaps, PSI) that claim statistical significance **must** be computed or adjusted at the person / entity level:

- Cluster-robust standard errors or person-level aggregation before testing
- Permutation tests that shuffle labels / protected attributes at the person level when assessing fairness
- Reporting of both observation-level and person-level sample sizes

Row-level metrics may be shown for diagnostics but must be clearly labelled as secondary.

## Consequences

Positive:
- Honest uncertainty estimates
- Defensible claims in front of model risk and regulators

Negative:
- Slightly more complex evaluation code
- Power analysis becomes more conservative (which is desirable)

## Related

- ADR-0002 Governance & Quality Gate
- ADR-0004 Evaluation methodology
