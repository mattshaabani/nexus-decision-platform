# ADR-0002: Governance & Quality Gate as Compliance-as-Code

**Status:** Accepted  
**Date:** 2026-10-25

## Context

Regulated financial decisions (credit, underwriting) require:

- Continuous monitoring of model performance, calibration and fairness
- Explicit promotion gates before a model becomes champion
- Full auditability for regulators and internal model risk teams

Manual checklists fail under velocity. The gate must be executable code that can run in CI and in production monitoring.

## Decision

1. **Quality Gate** (`scripts/quality_gate.py` + domain rules) is the single source of truth for promotion readiness.
2. A model may only become champion if it passes **all** of the following (thresholds live in config, not hardcoded):
   - Gini / AUC uplift vs current champion (or absolute floor for first model)
   - Calibration (Brier score / ECE) within tolerance
   - Fairness flags (four-fifths rule + equal-opportunity gap) not breached at statistical significance
   - Monotonicity / sign constraints respected (for scorecards)
   - PSI / CSI drift vs training window under threshold
3. The gate produces a machine-readable report + human-readable model card.
4. CI fails if the gate fails on the candidate model artifact.
5. Agents and LLMs **never** override the gate or make the final credit decision.

## Consequences

Positive:
- Auditable, reproducible promotion decisions.
- Same logic used in research experiments and production.

Negative:
- Threshold tuning requires care; too strict blocks progress, too loose undermines governance.

## Related

- ADR-0003 Person-level statistics
- ADR-0004 Evaluation methodology
