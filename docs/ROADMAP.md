# Nexus Decision Platform – Roadmap

## Phase 0 – Foundation

- [x] Repository skeleton + hexagonal layout
- [x] Core ADRs (architecture, governance, person-level stats, evaluation)
- [x] Domain ports & models
- [x] Quality gate script (executable)
- [x] Docker Compose development stack (API, Redis, MLflow)
- [x] FastAPI health endpoint
- [x] Unit tests + GitHub Actions CI (green)

## Phase 1 – Credit Decision Core

- [x] WoE / monotonic binning + logistic scorecard (sign-constrained)
- [x] Reason codes
- [x] OOT split + embargo evaluation harness
- [x] Person-level fairness (four-fifths, equal opportunity)
- [x] Model card generation (Markdown)
- [x] Quality gate wired to real metrics (incl. real PSI)
- [x] End-to-end experiment script

## Phase 2 – Monitoring & MLOps loop

- [x] Monitoring (PSI, Gini-drop alerts vs training baseline)
- [x] MLflow experiment logging (params, metrics, artifacts)
- [x] Decision audit log (SQLite append-only store)
- [x] Champion–challenger promotion with Gini uplift
- [x] Configurable gate thresholds (YAML)
- [x] Decision API: `POST /score`, `GET /champion`, `GET /health`
- [x] Reproducibility metadata (seed, feature list, gate status in MLflow)
- [ ] Retrain trigger policies (scheduled / drift-based)
- [ ] CSI / calibration drift depth

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

**Success metric for Phase 1 (met):** a scorecard can be trained, evaluated OOT, fairness-audited, and either promoted or rejected by the quality gate with a complete model card — runnable from scripts and checked in CI.

**Success metric for Phase 2 (mostly met):** decisions are scored via API, audited, monitored for drift, logged to MLflow, and promotion requires measurable uplift over the champion.