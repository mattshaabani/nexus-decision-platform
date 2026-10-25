# Nexus Decision Platform – Roadmap

## Phase 0 – Foundation (current)

- [x] Repository skeleton + hexagonal layout
- [x] Core ADRs (architecture, governance, person-level stats, evaluation)
- [ ] Domain ports & pure scorecard / metrics stubs
- [ ] Quality gate script (executable)
- [ ] Docker Compose development stack
- [ ] Minimal FastAPI health endpoint
- [ ] First unit tests + CI skeleton

## Phase 1 – Credit Decision Core

- [ ] WoE / monotonic binning + logistic scorecard (sign-constrained)
- [ ] Reason codes
- [ ] Champion–challenger evaluation harness (OOT + embargo)
- [ ] Person-level fairness audit (permutation)
- [ ] Model card generation
- [ ] Quality gate fully wired to real metrics

## Phase 2 – Monitoring & MLOps loop

- [ ] Continuous monitoring (PSI, CSI, calibration drift, fairness)
- [ ] MLflow model registry integration
- [ ] Retrain trigger policies
- [ ] Production decision audit log

## Phase 3 – Agentic support layer (subordinate)

- [ ] LLM gateway (cost routing, semantic cache, rate limits)
- [ ] Policy RAG + evaluation harness
- [ ] Explanation / dispute / investigation agents (MCP-ready)
- [ ] Grounding rule enforced (no free-form final decisions)

## Phase 4 – FP&A surface + product hardening

- [ ] Scenario & variance investigation agents
- [ ] Investor demo path (full decision lifecycle with audit trail)
- [ ] Hardening, observability, security review
- [ ] Packaging for pilot customers

---

Success metric for Phase 1: a scorecard can be trained, evaluated OOT, fairness-audited, and either promoted or rejected by the quality gate with a complete model card — all from scripts that run in CI.
