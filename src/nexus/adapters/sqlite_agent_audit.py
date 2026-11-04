"""Append-only audit log for agent / support turns."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SqliteAgentAuditStore:
    def __init__(self, db_path: str | Path = "artifacts/agent_audit.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_turns (
                    turn_id        TEXT PRIMARY KEY,
                    decision_id    TEXT,
                    endpoint       TEXT NOT NULL,
                    prompt_hash    TEXT NOT NULL,
                    tools_json     TEXT NOT NULL,
                    citations_json TEXT NOT NULL,
                    model          TEXT,
                    cached         INTEGER NOT NULL,
                    cost_usd       REAL NOT NULL,
                    latency_ms     REAL,
                    created_at     TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def hash_prompt(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def log_turn(
        self,
        *,
        turn_id: str,
        decision_id: str | None,
        endpoint: str,
        prompt_text: str,
        tools: list[str],
        citations: list[dict[str, Any]],
        model: str | None,
        cached: bool,
        cost_usd: float,
        latency_ms: float | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_turns (
                    turn_id, decision_id, endpoint, prompt_hash, tools_json,
                    citations_json, model, cached, cost_usd, latency_ms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    turn_id,
                    decision_id,
                    endpoint,
                    self.hash_prompt(prompt_text),
                    json.dumps(tools),
                    json.dumps(citations),
                    model,
                    1 if cached else 0,
                    cost_usd,
                    latency_ms,
                    datetime.now(UTC).isoformat(),
                ),
            )
            conn.commit()