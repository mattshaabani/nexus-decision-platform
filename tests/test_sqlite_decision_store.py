"""Tests for SQLite decision audit log."""

from pathlib import Path

from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
from nexus.domain.models import Decision, DecisionOutcome


def test_save_get_list(tmp_path: Path):
    store = SqliteDecisionStore(tmp_path / "test.db")
    d = Decision(
        decision_id="d1",
        person_id="p1",
        model_version="v1",
        score=620.0,
        probability=0.12,
        outcome=DecisionOutcome.APPROVE,
        reason_codes=["RC:utilisation"],
        features={"utilisation": 0.3},
    )
    store.save(d)
    got = store.get("d1")
    assert got is not None
    assert got.person_id == "p1"
    assert got.outcome == DecisionOutcome.APPROVE
    assert store.list_by_person("p1")[0].decision_id == "d1"
    assert store.get("missing") is None