"""Champion-challenger promotion tests."""

from pathlib import Path

from nexus.adapters.champion_store import ChampionStore
from nexus.application.promote import evaluate_challenger, promote_if_passed
from nexus.domain.models import GateStatus


def _good_metrics(**overrides: float) -> dict[str, float]:
    base = {
        "gini": 0.42,
        "brier": 0.15,
        "psi" : 0.05,
        "four_fifths_ratio": 0.9,
        "eo_gap": 0.02,
    }
    base.update(overrides)
    return base

def test_first_model_becomes_champion(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    metrics = _good_metrics()
    gate = evaluate_challenger("v1", metrics, store)
    assert gate.status == GateStatus.PASS
    assert promote_if_passed("v1", metrics, gate, store) is True
    assert store.get()["model_version"] == "v1"

def test_challenger_needs_uplift(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    m1 = _good_metrics(gini=0.42)
    g1 = evaluate_challenger("v1", m1, store)
    promote_if_passed("v1", m1, g1, store)

    # same gini → no uplift → fail
    m2 = _good_metrics(gini=0.42)
    g2 = evaluate_challenger("v2", m2, store)
    assert g2.status == GateStatus.FAIL
    assert promote_if_passed("v2", m2, g2, store) is False
    assert store.get()["model_version"] == "v1"

    # better gini → pass + promote
    m3 = _good_metrics(gini=0.48)
    g3 = evaluate_challenger("v3", m3, store)
    assert g3.status == GateStatus.PASS
    assert promote_if_passed("v3", m3, g3, store) is True
    assert store.get()["model_version"] == "v3"