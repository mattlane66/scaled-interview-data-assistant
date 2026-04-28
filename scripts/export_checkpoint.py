"""Export a resumable synthesis checkpoint JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from common import console, normalize_column_names, read_table

app = typer.Typer(add_completion=False)


def table_records(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    return normalize_column_names(read_table(path)).to_dict(orient="records")


@app.command()
def main(
    evidence: Path = typer.Option(..., "--evidence", "-e"),
    codebook: Path | None = typer.Option(None, "--codebook", "-c"),
    mappings: Path | None = typer.Option(None, "--mappings", "-m"),
    clusters: Path | None = typer.Option(None, "--clusters"),
    aliases: Path | None = typer.Option(None, "--aliases", "-a"),
    diff_log: Path | None = typer.Option(None, "--diff-log"),
    output: Path = typer.Option(Path("CHECKPOINT.json"), "--output", "-o"),
) -> None:
    checkpoint = {
        "checkpoint_version": "0.1.0",
        "evidence_bank": table_records(evidence),
        "codebook": table_records(codebook),
        "evidence_to_code_mappings": table_records(mappings),
        "clusters": table_records(clusters),
        "alias_map": table_records(aliases),
        "latest_diff_log": diff_log.read_text() if diff_log else "",
    }

    output.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False))
    console.print(f"[bold green]Wrote checkpoint to {output}[/bold green]")


if __name__ == "__main__":
    app()
