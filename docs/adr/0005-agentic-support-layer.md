# ADR 0005 – Agentic support layer (subordinate)

## Status

Proposed

## Context

Nexus already produces governed credit decisions via scorecard + quality gate + audit log.
Stakeholders need explanations, policy lookups, and dispute support — but **never** an unconstrained
LLM as the final credit decision-maker.

## Decision

Introduce an **agentic support layer** that is strictly subordinate to the decision core:

1. **Grounding rule**  
   Agents may explain, retrieve policy, draft dispute responses, or investigate FP&A variance.
   They must not approve/decline credit. Final outcome remains scorecard + gate + optional human override.

2. **LLM gateway**  
   Single entrypoint for model calls: routing (cheap vs strong), semantic cache, rate limits, cost accounting.

3. **Policy RAG**  
   Hybrid retrieval over policy / product / underwriting documents with a retrieval evaluation harness
   (recall@k, groundedness) before production use.

4. **Tool interface (MCP-ready)**  
   Agents call tools only: `get_decision`, `get_champion`, `get_policy_chunk`, `get_model_card`.
   No free-form write to champion or gate thresholds.

5. **Audit**  
   Every agent turn logs: prompt hash, tools used, citations, cost, latency — append-only.

## Consequences

- Product can offer “why was I declined?” and internal investigation without regulatory exposure of LLM scoring.
- Extra latency/cost only on support paths, not on `POST /score`.
- Requires retrieval eval and cost budgets before pilot.

## Non-goals (Phase 3)

- LLM feature engineering for the scorecard
- Autonomous promotion of models
- Customer-facing chat that can change outcomes