"""Agent toolbox allow-list tests."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nexus.adapters.champion_store import ChampionStore
from nexus.adapters.policy_retriever import MarkdownPolicyRetriever
from nexus.adapters.sqlite_decision_store import SqliteDecisionStore
from nexus.application.agent_tools import AgentToolError, AgentToolbox
from nexus.application.scoring import score_application
from nexus.domain.scorecard import fit_scorecard


def test_tools_read_only(tmp_path: Path):
    rng = np.random.default_rng(1)
    n = 150
    df = pd.DataFrame(
        {
            "income": rng.normal(50_000, 8_000, n),
            "age": rng.integers(25, 55, n),
            "utilisation": rng.uniform(0, 1, n),
            "default": rng.integers(0, 2, n),
        }
    )
    sc = fit_scorecard(df, "default", ["income", "age", "utilisation"], min_bin_size=12)
    store = SqliteDecisionStore(tmp_path / "d.db")
    d = score_application(
        sc,
        {"income": 48_000, "age": 33, "utilisation": 0.5},
        person_id="t1",
        model_version="v1",
        store=store,
    )
    champ = ChampionStore(tmp_path / "c.json")
    champ.set("v1", {"gini": 0.4})
    box = AgentToolbox(store, champ, MarkdownPolicyRetriever("data/policy"))

    assert box.get_decision(d.decision_id)["outcome"] in {"approve", "decline"}
    assert box.get_champion()["model_version"] == "v1"
    assert len(box.get_policy("utilisation")) >= 1
    with pytest.raises(AgentToolError):
        box.call("promote_to_champion", model_version="evil")