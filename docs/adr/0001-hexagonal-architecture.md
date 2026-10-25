# ADR-0001: Hexagonal (Ports & Adapters) Architecture

**Status:** Accepted  
**Date:** 2026-10-25

## Context

Nexus Decision Platform will contain domain logic (scorecards, fairness, quality gates), application orchestration, infrastructure (databases, model stores, LLM gateways, vector stores), and multiple entrypoints (API, CLI, workers, future agents).

We need strict boundaries so that:

- Domain logic stays pure and testable without infrastructure.
- Swapping an adapter (e.g. MLflow → another registry) does not force domain changes.
- Import-linter can enforce the rules in CI.

## Decision

Adopt classic hexagonal architecture with three layers inside `src/nexus/`:

```
nexus/
├── domain/          # Pure business rules. No I/O, no FastAPI, no MLflow, no Redis.
├── application/     # Use-cases / orchestration. Depends only on domain + ports.
├── adapters/        # Concrete implementations of ports (infra).
└── entrypoints/     # API, CLI, batch jobs, workers.
```

Ports (interfaces) live in `domain` or `application` as Protocol / ABC classes.  
Adapters implement those ports.

Import-linter contracts (see `pyproject.toml`) forbid:

- `domain` → anything outside domain
- `application` → `adapters` or `entrypoints`

## Consequences

Positive:
- Domain tests are fast and deterministic.
- Clear ownership of responsibilities.
- Easy to extract services later if needed.

Negative:
- Slightly more boilerplate for ports.
- New contributors must learn the layering rules.

## Related

- ADR-0002 Governance & Quality Gate
- ADR-0003 Person-level statistics
