"""Model card generation — pure domain."""

from __future__ import annotations

from datetime import UTC, datetime

from nexus.domain.models import GateResult, ModelCard, ModelStatus


def build_model_card(
    model_version: str,
    gate: GateResult,
    *,
    training_window: str | None = None,
    evaluation_window: str | None = None,
    features: list[str] | None = None,
    extra_limitations: list[str] | None = None,
) -> ModelCard:
    """Build a model card from a gate result and optional metadata."""
    status = ModelStatus.CANDIDATE if gate.passed else ModelStatus.REJECTED

    limitations = [
        "Evaluated on synthetic or limited data until production OOT is connected.",
        "Fairness metrics depend on the protected attribute definition supplied at evaluation.",
        "PSI in demo mode may be a placeholder until train-vs-serve comparison is wired.",
    ]
    if extra_limitations:
        limitations.extend(extra_limitations)
    if not gate.passed:
        limitations.append("Model failed the quality gate and must not be promoted.")

    fairness_summary = {
        m.name: m.value
        for m in gate.metrics
        if m.name in {"four_fifths_ratio", "eo_gap"}
    }

    return ModelCard(
        model_version=model_version,
        status=status,
        training_window=training_window,
        evaluation_window=evaluation_window,
        metrics=list(gate.metrics),
        fairness_summary=fairness_summary,
        limitations=limitations,
        gate_result=gate,
        created_at=datetime.now(UTC),
    )


def render_model_card_markdown(card: ModelCard) -> str:
    """Human-readable Markdown model card."""
    lines = [
        f"# Model Card: `{card.model_version}`",
        "",
        f"- **Status:** {card.status.value}",
        f"- **Created (UTC):** {card.created_at.isoformat()}",
    ]
    if card.training_window:
        lines.append(f"- **Training window:** {card.training_window}")
    if card.evaluation_window:
        lines.append(f"- **Evaluation window:** {card.evaluation_window}")

    lines += ["", "## Metrics", ""]
    for m in card.metrics:
        flag = "PASS" if m.passed else "FAIL"
        thr = f" (threshold={m.threshold})" if m.threshold is not None else ""
        lines.append(f"- `{m.name}`: **{m.value:.4f}** [{flag}]{thr}")

    if card.fairness_summary:
        lines += ["", "## Fairness summary", ""]
        for k, v in card.fairness_summary.items():
            lines.append(f"- `{k}`: {v:.4f}")

    lines += ["", "## Limitations", ""]
    for lim in card.limitations:
        lines.append(f"- {lim}")

    if card.gate_result and card.gate_result.blockers:
        lines += ["", "## Gate blockers", ""]
        for b in card.gate_result.blockers:
            lines.append(f"- {b}")

    lines.append("")
    return "\n".join(lines)