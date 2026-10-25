# Nexus Decision Platform

**Governed Decision Intelligence for regulated financial decisions.**

Primary beachhead: credit / underwriting decisioning with full model-risk governance, continuous monitoring, agentic explanation & investigation support, and an FP&A scenario surface on the same platform.

> Agents and LLMs explain, draft, investigate and retrieve.  
> Final regulated decisions remain deterministic, auditable, fair, and human-overridable.

---

## Status

**Phase 0 – Foundation** (current)

- Hexagonal architecture
- Credit decision core (ports + domain)
- Quality gate + model card skeleton
- Docker development stack
- ADR-driven design

---

## Quick start

```bash
# Clone
git clone https://github.com/mattshaabani/nexus-decision-platform.git
cd nexus-decision-platform

# Setup (creates venv, installs deps)
make setup

# Run tests + quality gate
make test
make quality-gate

# Local stack (API + monitoring + MLflow + Redis)
docker compose up -d
```

---

## Architecture principles (non-negotiable)

1. **Person-level statistics** – never treat rows as independent observations when they belong to the same person.
2. **Champion–challenger gate** – no model is promoted without explicit uplift + calibration + fairness checks.
3. **Quality gate is compliance-as-code** – fails CI if thresholds are breached.
4. **Agents are subordinate** – they never make the final credit decision.
5. **Full audit trail** – every decision, feature, model version and override is recorded.
6. **Import-linter enforced hexagonal boundaries**.

See `docs/adr/` for the full set of Architecture Decision Records.

---

## Repository layout

```
nexus-decision-platform/
├── docs/
│   ├── adr/                  # Architecture Decision Records
│   └── ROADMAP.md
├── src/
│   └── nexus/
│       ├── domain/           # Pure business logic (no I/O)
│       ├── application/      # Use cases / orchestration
│       ├── adapters/         # Infrastructure (DB, ML, LLM, ...)
│       └── entrypoints/      # API, CLI, workers
├── scripts/                  # quality_gate, evaluate, train, ...
├── tests/
├── docker/
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

---

## License

Proprietary – all rights reserved (for now).
