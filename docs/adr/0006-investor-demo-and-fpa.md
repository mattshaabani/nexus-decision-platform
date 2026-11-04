# ADR 0006 – Investor demo path and FP&A surface

## Status

Proposed

## Context

Phases 0–3 deliver a governed credit decision core plus subordinate support agents.
For investors and pilot banks we need a **demoable lifecycle** and a clear path to FP&A
without weakening model risk controls.

## Decision

### Investor demo path (must show in one sitting)

1. Train scorecard on sample/OOT data → quality gate → model card  
2. Promote champion (or show rejected uplift failure)  
3. `POST /score` → decision + reason codes → audit row  
4. Monitoring snapshot (PSI, ECE, retrain policy)  
5. `POST /support/explain` with policy citations + agent audit turn  

All steps scriptable; no manual notebook magic.

### FP&A surface (Phase 4 scope)

- Scenario / variance **investigation** agents only (read metrics, retrieve policy/notes)
- No autonomous booking of forecasts
- Same grounding rule: agents propose narratives; humans accept

### Packaging for pilots

- Docker Compose profile `demo`
- Seeded synthetic data + policy pack
- One-command `scripts/run_investor_demo.py`

## Consequences

- Demo is reproducible and regulator-friendly
- FP&A is an expansion of the same architecture, not a second product
- Engineering remains decision-core-first

## Non-goals

- Full general ledger integration in Phase 4
- Customer self-serve model training