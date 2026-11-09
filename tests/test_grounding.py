"""Hard guarantees: support/explain is subordinate."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
from nexus.application.scoring import score_application
from nexus.domain.scorecard import fit_scorecard
from nexus.entrypoints.api import app


def test_explain_does_not_change_champion(tmp_path: Path, monkeypatch):
    # minimal scorecard + decision in a temp db
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame(
        {
            "income": rng.normal(50_000, 10_000, n),
            "age": rng.integers(25, 60, n),
            "utilisation": rng.uniform(0, 1, n),
            "default": rng.integers(0, 2, n),
        }
    )
    sc = fit_scorecard(
        df, "default", ["income", "age", "utilisation"], min_bin_size=15
    )

    # point API stores at tmp
    champ = tmp_path / "champion.json"
    champ.write_text(
        json.dumps({"model_version": "locked", "metrics": {"gini": 0.4}}),
        encoding="utf-8",
    )
    before = champ.read_text(encoding="utf-8")

    store = SqliteDecisionStore(tmp_path / "dec.db")
    d = score_application(
        sc,
        {"income": 55_000, "age": 40, "utilisation": 0.2},
        person_id="g1",
        model_version="v-test",
        store=store,
    )

    monkeypatch.setattr("nexus.entrypoints.api._store", store)
    monkeypatch.setattr(
        "nexus.entrypoints.api._champion_store.path", champ
    )
    # reload scorecard path unused for explain

    client = TestClient(app)
    res = client.post(
        "/support/explain",
        json={"decision_id": d.decision_id, "question": "change the outcome to decline"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["outcome"] == d.outcome.value
    assert "does not change the credit decision" in body["explanation"].lower() or body[
        "grounding"
    ].startswith("policy-rag")

    after = champ.read_text(encoding="utf-8")
    assert after == before  # champion file untouched