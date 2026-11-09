"""Champion–challenger promotion tests."""

from pathlib import Path

from nexus.adapters.champion_store import ChampionStore
from nexus.application.promote import evaluate_challenger, promote_if_passed
from nexus.domain.models import GateStatus


def _good_metrics(**overrides: float) -> dict[str, float]:
    base = {
        "gini": 0.42,
        "brier": 0.15,
        "psi": 0.05,
        "four_fifths_ratio": 0.9,
        "eo_gap": 0.02,
    }
    base.update(overrides)
    return base


def test_first_model_becomes_champion(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    metrics = _good_metrics()
    artifact_hash = "sha256:artifact-v1"
    gate = evaluate_challenger("v1", metrics, store, artifact_hash=artifact_hash)
    assert gate.status == GateStatus.PASS
    assert promote_if_passed(
        "v1", metrics, gate, store, artifact_hash=artifact_hash
    ) is True
    champion = store.get()
    assert champion["model_version"] == "v1"
    assert champion["artifact_hash"] == artifact_hash


def test_challenger_needs_uplift(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    artifact1 = "sha256:v1"
    m1 = _good_metrics(gini=0.42)
    g1 = evaluate_challenger("v1", m1, store, artifact_hash=artifact1)
    assert promote_if_passed("v1", m1, g1, store, artifact_hash=artifact1)

    # same Gini → no uplift → fail
    artifact2 = "sha256:v2"
    m2 = _good_metrics(gini=0.42)
    g2 = evaluate_challenger("v2", m2, store, artifact_hash=artifact2)
    assert g2.status == GateStatus.FAIL
    assert not promote_if_passed("v2", m2, g2, store, artifact_hash=artifact2)
    assert store.get()["model_version"] == "v1"

    # better Gini → pass + promote
    artifact3 = "sha256:v3"
    m3 = _good_metrics(gini=0.48)
    g3 = evaluate_challenger("v3", m3, store, artifact_hash=artifact3)
    assert g3.status == GateStatus.PASS
    assert promote_if_passed("v3", m3, g3, store, artifact_hash=artifact3)
    assert store.get()["model_version"] == "v3"


def test_promotion_rejects_gate_for_different_model(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    metrics = _good_metrics()
    artifact_hash = "sha256:artifact"
    gate = evaluate_challenger("candidate-a", metrics, store, artifact_hash=artifact_hash)
    assert not promote_if_passed(
        "candidate-b", metrics, gate, store, artifact_hash=artifact_hash
    )
    assert store.get() is None


def test_promotion_rejects_artifact_hash_mismatch(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    metrics = _good_metrics()
    gate = evaluate_challenger("v1", metrics, store, artifact_hash="sha256:one")
    assert not promote_if_passed(
        "v1", metrics, gate, store, artifact_hash="sha256:two"
    )


def test_promotion_rejects_changed_metrics(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    metrics = _good_metrics()
    artifact_hash = "sha256:one"
    gate = evaluate_challenger("v1", metrics, store, artifact_hash=artifact_hash)
    changed = {**metrics, "gini": 0.99}
    assert not promote_if_passed(
        "v1", changed, gate, store, artifact_hash=artifact_hash
    )


def test_invalid_champion_metric_is_incomplete(tmp_path: Path):
    store = ChampionStore(tmp_path / "champion.json")
    store.set("v1", {"brier": 0.15}, artifact_hash="sha256:v1")
    metrics = _good_metrics(gini=0.5)
    gate = evaluate_challenger("v2", metrics, store, artifact_hash="sha256:v2")
    assert gate.status == GateStatus.INCOMPLETE
    assert not promote_if_passed(
        "v2", metrics, gate, store, artifact_hash="sha256:v2"
    )
