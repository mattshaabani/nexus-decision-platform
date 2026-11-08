#!/usr/bin/env python3
"""Quality gate – run from CI or locally.

Usage:
    python scripts/quality_gate.py --metrics path/to/metrics.json --first-model
    python scripts/quality_gate.py --demo --first-model
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
    parser.add_argument("--metrics", type=Path, help="JSON file containing candidate metrics")
    parser.add_argument("--demo", action="store_true", help="Use explicitly marked demo metrics")
    parser.add_argument("--model-version", default="candidate-0.1.0")
    parser.add_argument("--first-model", action="store_true", help="Skip challenger uplift check")
    args = parser.parse_args()

    if args.metrics is not None:
        if not args.metrics.is_file():
            print(f"ERROR: metrics file does not exist: {args.metrics}", file=sys.stderr)
            return 2
        try:
            metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: unable to read metrics JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(metrics, dict):
            print("ERROR: metrics JSON must be an object.", file=sys.stderr)
            return 2
    elif args.demo:
        metrics = {
            "gini": 0.42,
            "brier": 0.18,
            "psi": 0.08,
            "four_fifths_ratio": 0.91,
            "eo_gap": 0.02,
        }
        print("NOTE: using synthetic demo metrics; this is not model evaluation evidence.\n")
    else:
        print("ERROR: provide --metrics or explicitly opt in to --demo.", file=sys.stderr)
        return 2

    result = evaluate_gate(
        model_version=args.model_version,
        metrics=metrics,
        is_first_model=args.first_model,
    )

    print("=" * 60)
    print(f"Quality Gate  |  model={result.model_version}")
    print("=" * 60)
    for metric in result.metrics:
        status = "PASS" if metric.passed else "FAIL"
        threshold = f" (threshold={metric.threshold})" if metric.threshold is not None else ""
        print(f"  {status:4s}  {metric.name:20s}  {metric.value:.4f}{threshold}")
    if result.blockers:
        print("-" * 60)
        print("Blockers:")
        for blocker in result.blockers:
            print(f"  - {blocker}")
    print("=" * 60)
    print(f"Result: {result.status.value.upper()}")
    print("=" * 60)
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
