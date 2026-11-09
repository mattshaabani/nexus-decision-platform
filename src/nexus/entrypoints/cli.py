"""Nexus command-line entrypoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from nexus.adapters.champion_store import ChampionStore
from nexus.domain.quality_gate import evaluate_gate

app = typer.Typer(help="Nexus Decision Platform CLI", no_args_is_help=True)


@app.command("quality-gate")
def quality_gate_command(
    metrics_file: Annotated[
        Path,
        typer.Option("--metrics", exists=True, readable=True, help="JSON metrics file"),
    ],
    model_version: Annotated[str, typer.Option("--model-version")] = "candidate",
    first_model: Annotated[bool, typer.Option("--first-model")] = False,
) -> None:
    """Evaluate a candidate model against the quality gate."""
    try:
        metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        typer.echo(f"Invalid metrics file: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if not isinstance(metrics, dict):
        typer.echo("Metrics JSON must be an object.", err=True)
        raise typer.Exit(code=2)

    result = evaluate_gate(
        model_version=model_version,
        metrics=metrics,
        is_first_model=first_model,
    )
    typer.echo(f"Model: {result.model_version}")
    typer.echo(f"Gate: {result.status.value.upper()}")
    for blocker in result.blockers:
        typer.echo(f"- {blocker}")
    raise typer.Exit(code=0 if result.passed else 1)


@app.command("champion")
def champion_command(
    registry: Annotated[
        Path,
        typer.Option("--registry", help="Champion JSON path"),
    ] = Path("artifacts/champion.json"),
) -> None:
    """Print the current champion registry snapshot."""
    champion = ChampionStore(registry).get()
    if champion is None:
        typer.echo("No champion registered.")
        raise typer.Exit(code=1)
    typer.echo(json.dumps(champion, indent=2, sort_keys=True))
