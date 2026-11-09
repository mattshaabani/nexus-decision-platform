#!/usr/bin/env python3
"""One-command investor demo: train → gate → score → monitor → explain."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    print("=" * 60)
    print("NEXUS INVESTOR DEMO")
    print("=" * 60)

    print("\n[A] Train / evaluate / gate / MLflow / audit sample")
    rc = subprocess.call(
        [sys.executable, str(ROOT / "scripts" / "run_scorecard_experiment.py")],
        cwd=str(ROOT),
    )
    print(f"    experiment exit code: {rc}")

    # Load scorecard and score one application via application layer
    print("\n[B] Score a single application (product path)")
    import pickle

    from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
    from nexus.application.scoring import score_application
    from nexus.domain.models import DecisionOutcome

    pkl = ROOT / "artifacts" / "scorecard_scorecard-v0.1.0.pkl"
    if not pkl.exists():
        print(f"    FAIL: missing {pkl}")
        return 1
    with open(pkl, "rb") as f:
        sc = pickle.load(f)

    store = SqliteDecisionStore(ROOT / "artifacts" / "decisions.db")
    decision = score_application(
        sc,
        {"income": 62000, "age": 38, "utilisation": 0.28},
        person_id="demo-investor-1",
        model_version="scorecard-v0.1.0",
        store=store,
    )
    print(
        f"    decision_id={decision.decision_id}\n"
        f"    outcome={decision.outcome.value}  score={decision.score:.1f}  "
        f"p={decision.probability:.4f}\n"
        f"    reasons={list(decision.reason_codes)}"
    )

    print("\n[C] Champion snapshot")
    champ_path = ROOT / "artifacts" / "champion.json"
    if champ_path.exists():
        print(json.dumps(json.loads(champ_path.read_text(encoding="utf-8")), indent=2)[:500])
    else:
        print("    (no champion file — first model may still be pending uplift)")

    print("\n[D] Support explain (grounded, subordinate)")
    from nexus.adapters.llm_echo import InMemoryCache, build_default_llm
    from nexus.adapters.policy_retriever import MarkdownPolicyRetriever
    from nexus.domain.llm_gateway import LLMMessage, LLMRequest

    retriever = MarkdownPolicyRetriever(ROOT / "data" / "policy")
    llm = build_default_llm(InMemoryCache())
    hits = retriever.retrieve(" ".join(decision.reason_codes), top_k=2)
    policy = "\n".join(f"- {h.chunk.title}: {h.chunk.text[:160]}" for h in hits)
    resp = llm.complete(
        LLMRequest(
            messages=(
                LLMMessage(
                    role="system",
                    content="Explain only. Never change the credit decision.",
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Explain outcome={decision.outcome.value} "
                        f"reasons={list(decision.reason_codes)}\nPolicy:\n{policy}"
                    ),
                ),
            )
        )
    )
    print(f"    {resp.content[:300]}")
    print(f"    citations={[h.chunk.chunk_id for h in hits]}")

    print("\n[E] Demo complete")
    print("    Artifacts: artifacts/model_card_*.md, decisions.db, champion.json")
    print("    API (optional): uvicorn nexus.entrypoints.api:app --port 8000")
    return 0 if decision.outcome in {DecisionOutcome.APPROVE, DecisionOutcome.DECLINE} else 1


if __name__ == "__main__":
    # Allow importing run_scorecard_experiment as module
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())