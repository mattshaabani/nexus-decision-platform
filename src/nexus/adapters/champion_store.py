"""File-based champion registry with atomic snapshot replacement."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class ChampionStore:
    """Persists champion version, artifact hash, and evaluation metrics."""

    def __init__(self, path: str | Path = "artifacts/champion.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid champion registry format: {self.path}")
        return payload

    def set(
        self,
        model_version: str,
        metrics: dict[str, float],
        *,
        artifact_hash: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if not model_version.strip():
            raise ValueError("model_version must be non-empty")
        if not artifact_hash.strip():
            raise ValueError("artifact_hash must be non-empty")
        payload: dict[str, Any] = {
            "model_version": model_version,
            "artifact_hash": artifact_hash,
            "metrics": metrics,
        }
        if extra:
            payload["extra"] = extra

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        except Exception:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temp_name)
            raise

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
