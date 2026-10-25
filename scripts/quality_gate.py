#!/usr/bin/env python3
"""Quality gate – run from CI or locally.

Usage:
    python scripts/quality_gate.py
    python scripts/quality_gate.py --metrics path/to/metrics.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running without install during early bootstrap
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nexus.domain.quality_gate import evaluate_gate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Nexus quality / promotion gate")
    parser.add_argument(
        "--metrics",
        type=Path,
        help="JSON file with metric values (otherwise uses demo values)",
    )
    parser.add_argument("--model-version", default="candidate-0.1.0")
    parser.add_argument(
        "--first-model", action="store_true", help="Skip uplift check"
    )
    args = parser.parse_args()

    if args.metrics and args.metrics.exists():
        metrics = json.loads(args.metrics.read_text())
    else:
        # Demo metrics that pass the default gate (first model)
        metrics = {
            "gini": 0.42,
            "brier": 0.18,
            "psi": 0.08,
            "four_fifths_ratio": 0.91,
            "eo_gap": 0.02,
        }
        print("ℹ️  No metrics file supplied – using demo values that should PASS.\n")

    result = evaluate_gate(
        model_version=args.model_version,
        metrics=metrics,
        is_first_model=args.first_model or "gini_champion" not in metrics,
    )

    print("=" * 60)
    print(f"Quality Gate  |  model={result.model_version}")
    print("=" * 60)
    for m in result.metrics:
        status = "✅" if m.passed else "❌"
        thr = f" (threshold={m.threshold})" if m.threshold is not None else ""
        print(f"  {status}  {m.name:20s}  {m.value:.4f}{thr}")
    print("-" * 60)
    if result.blockers:
        print("Blockers:")
        for b in result.blockers:
            print(f"  • {b}")
    else:
        print("No blockers.")
    print("=" * 60)
    print(f"Result: {result.status.value.upper()}")
    print("=" * 60)

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
