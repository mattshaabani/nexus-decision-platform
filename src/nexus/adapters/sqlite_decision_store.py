"""Append-only SQLite decision audit log."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from nexus.domain.models import Decision, DecisionOutcome


class SqliteDecisionStore:
    def __init__(self, db_path: str | Path = "artifacts/decisions.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id   TEXT PRIMARY KEY,
                    person_id     TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    score         REAL NOT NULL,
                    probability   REAL NOT NULL,
                    outcome       TEXT NOT NULL,
                    reason_codes  TEXT NOT NULL,
                    features      TEXT NOT NULL,
                    override      INTEGER NOT NULL DEFAULT 0,
                    override_by   TEXT,
                    override_reason TEXT,
                    created_at    TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decisions_person ON decisions(person_id)"
            )
            conn.commit()

    def save(self, decision: Decision) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO decisions (
                    decision_id, person_id, model_version, score, probability,
                    outcome, reason_codes, features, override, override_by,
                    override_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.decision_id,
                    decision.person_id,
                    decision.model_version,
                    decision.score,
                    decision.probability,
                    decision.outcome.value,
                    json.dumps(list(decision.reason_codes)),
                    json.dumps(decision.features),
                    1 if decision.override else 0,
                    decision.override_by,
                    decision.override_reason,
                    decision.created_at.astimezone(UTC).isoformat(),
                ),
            )
            conn.commit()

    def get(self, decision_id: str) -> Decision | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_decision(row)

    def list_by_person(self, person_id: str, limit: int = 100) -> list[Decision]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM decisions
                WHERE person_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (person_id, limit),
            ).fetchall()
        return [self._row_to_decision(r) for r in rows]

    @staticmethod
    def _row_to_decision(row: sqlite3.Row) -> Decision:
        return Decision(
            decision_id=row["decision_id"],
            person_id=row["person_id"],
            model_version=row["model_version"],
            score=row["score"],
            probability=row["probability"],
            outcome=DecisionOutcome(row["outcome"]),
            reason_codes=json.loads(row["reason_codes"]),
            features=json.loads(row["features"]),
            override=bool(row["override"]),
            override_by=row["override_by"],
            override_reason=row["override_reason"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )