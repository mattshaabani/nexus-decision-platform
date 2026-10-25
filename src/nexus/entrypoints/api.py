"""Minimal FastAPI application – health + version."""

from fastapi import FastAPI

from nexus import __version__

app = FastAPI(
    title="Nexus Decision Platform",
    description="Governed Decision Intelligence for regulated financial decisions",
    version=__version__,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "nexus-decision-platform",
        "version": __version__,
        "docs": "/docs",
    }
