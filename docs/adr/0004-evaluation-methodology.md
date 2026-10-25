# ADR-0004: Evaluation Methodology

**Status:** Accepted  
**Date:** 2026-10-25

## Context

Credit models are often evaluated on the same distribution they were trained on, or with optimistic leakage. We need an evaluation contract that is honest about the achievable ceiling and that supports champion–challenger comparison.

## Decision

1. **Out-of-time (OOT) primary split** – final reported metrics come from a temporal hold-out that the model never saw during training or hyper-parameter search.
2. **Embargo** – a gap between train and OOT windows to reduce label leakage from overlapping observation windows.
3. **Exact-ceiling / oracle evaluation** (when true default probability or a high-fidelity simulator is available) – used to measure how close a model is to the theoretical maximum, not only relative ranking.
4. **Paired multi-seed comparisons** – challenger vs champion evaluated on identical folds / seeds; sign test or Wilcoxon for significance of uplift.
5. **Calibration is first-class** – Brier score, reliability diagrams, and expected calibration error are reported alongside ranking metrics.
6. **Fairness evaluated with person-level permutation tests** (see ADR-0003).

## Consequences

Positive:
- Metrics that survive contact with production reality.
- Clear language for “this model is better” vs “this model is close to the ceiling”.

Negative:
- Requires careful data pipelines and longer evaluation runtimes.

## Related

- ADR-0002 Governance & Quality Gate
- ADR-0003 Person-level statistics
