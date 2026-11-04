"""Simple keyword / overlap retriever over markdown policy files."""

from __future__ import annotations

import re
from pathlib import Path

from nexus.domain.rag import PolicyChunk, PolicyRetrieverPort, RetrievalHit


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


class MarkdownPolicyRetriever:
    def __init__(self, root: str | Path = "data/policy") -> None:
        self.root = Path(root)
        self.chunks: list[PolicyChunk] = []
        self._load()

    def _load(self) -> None:
        if not self.root.exists():
            return
        for path in sorted(self.root.glob("**/*.md")):
            text = path.read_text(encoding="utf-8")
            # split on ## headings
            parts = re.split(r"(?m)^## ", text)
            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                lines = part.splitlines()
                title = lines[0].strip() if lines else path.stem
                body = "\n".join(lines[1:]).strip() if i > 0 else part
                if i == 0 and part.startswith("#"):
                    # preamble
                    title = path.stem
                    body = part
                self.chunks.append(
                    PolicyChunk(
                        chunk_id=f"{path.stem}-{i}",
                        title=title[:120],
                        text=body or part,
                        source=str(path.as_posix()),
                    )
                )

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievalHit]:
        q = _tokenize(query)
        if not q or not self.chunks:
            return []
        scored: list[RetrievalHit] = []
        for ch in self.chunks:
            tokens = _tokenize(ch.title + " " + ch.text)
            if not tokens:
                continue
            overlap = len(q & tokens) / len(q)
            if overlap > 0:
                scored.append(RetrievalHit(chunk=ch, score=float(overlap)))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:top_k]