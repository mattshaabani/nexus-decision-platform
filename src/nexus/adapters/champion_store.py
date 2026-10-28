"""File-based champion registry (simple, auditable)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ChampionStore:
    """Persists the current champion model_version + metrics as JSON."""

    def __init__(self, path: str | Path = "artifacts/champion.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def set(
        self,
        model_version: str,
        metrics: dict[str, float],
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "model_version": model_version,
            "metrics": metrics,
        }
        if extra:
            payload["extra"] = extra
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()