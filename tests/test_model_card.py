"""Tests for model card builder."""

from nexus.domain.model_card import build_model_card, render_model_card_markdown
from nexus.domain.models import ModelStatus
from nexus.domain.quality_gate import evaluate_gate


def test_build_and_render_passing_card():
    gate = evaluate_gate(
        "v-test",
        {
            "gini": 0.45,
            "brier": 0.15,
            "psi": 0.05,
            "four_fifths_ratio": 0.9,
            "eo_gap": 0.02,
        },
        is_first_model=True,
    )
    card = build_model_card("v-test", gate, training_window="2023")
    assert card.status == ModelStatus.CANDIDATE
    md = render_model_card_markdown(card)
    assert "v-test" in md
    assert "PASS" in md or "pass" in md.lower()


def test_rejected_card_has_limitation():
    gate = evaluate_gate(
        "v-bad",
        {"gini": 0.1, "brier": 0.15},
        is_first_model=True,
    )
    card = build_model_card("v-bad", gate)
    assert card.status == ModelStatus.REJECTED
    assert any("failed the quality gate" in x.lower() for x in card.limitations)