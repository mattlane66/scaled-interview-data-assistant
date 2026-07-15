"""Export a resumable synthesis checkpoint JSON."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from checkpoint_validation import CheckpointValidationError, validate_checkpoint_document
from common import console, ensure_parent, normalize_column_names, read_table, records_without_nan

app = typer.Typer(add_completion=False)


def table_records(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    return records_without_nan(normalize_column_names(read_table(path)))


def load_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise typer.BadParameter("Metadata must be a JSON object.")
    return data


@app.command()
def main(
    evidence: Path = typer.Option(..., "--evidence", "-e"),
    sources: Path = typer.Option(..., "--sources"),
    interviews: Path = typer.Option(..., "--interviews"),
    episodes: Path = typer.Option(..., "--episodes"),
    segments: Path = typer.Option(..., "--segments"),
    codebook: Path = typer.Option(..., "--codebook", "-c"),
    mappings: Path = typer.Option(..., "--mappings", "-m"),
    links: Path | None = typer.Option(None, "--links"),
    clusters: Path | None = typer.Option(None, "--clusters"),
    aliases: Path | None = typer.Option(None, "--aliases", "-a"),
    diff_log: Path | None = typer.Option(None, "--diff-log"),
    decision_log: Path | None = typer.Option(None, "--decision-log"),
    metadata: Path | None = typer.Option(None, "--metadata"),
    analysis_unit: str = typer.Option("episode", "--analysis-unit"),
    clustering_method: str = typer.Option(
        "average-linkage hierarchical clustering on Jaccard distance",
        "--clustering-method",
    ),
    cluster_count: int | None = typer.Option(None, "--cluster-count"),
    output: Path = typer.Option(Path("CHECKPOINT.json"), "--output", "-o"),
) -> None:
    if analysis_unit not in {"episode", "interview"}:
        raise typer.BadParameter("--analysis-unit must be episode or interview")
    cluster_records = table_records(clusters)
    actual_cluster_count = len({row.get("cluster") for row in cluster_records})
    if cluster_count is not None and cluster_count != actual_cluster_count:
        raise typer.BadParameter(
            "--cluster-count must match the distinct cluster assignments "
            f"({actual_cluster_count})"
        )
    checkpoint = {
        "checkpoint_version": "1.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_unit": analysis_unit,
        "computation": {
            "a_to_b_association": (
                "reviewed links primary; Jaccard and descriptive phi secondary"
            ),
            "clustering_method": clustering_method,
            "cluster_count": actual_cluster_count,
        },
        "metadata": load_metadata(metadata),
        "source_index": table_records(sources),
        "interview_index": table_records(interviews),
        "episode_index": table_records(episodes),
        "segment_index": table_records(segments),
        "evidence_bank": table_records(evidence),
        "codebook": table_records(codebook),
        "evidence_to_code_mappings": table_records(mappings),
        "a_to_b_links": table_records(links),
        "clusters": cluster_records,
        "alias_map": table_records(aliases),
        "decision_log": decision_log.read_text() if decision_log else "",
        "latest_diff_log": diff_log.read_text() if diff_log else "",
    }

    try:
        checkpoint = validate_checkpoint_document(checkpoint)
    except CheckpointValidationError as error:
        raise typer.BadParameter(f"Checkpoint validation failed:\n{error}") from error

    ensure_parent(output)
    output.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    console.print(f"[bold green]Wrote checkpoint to {output}[/bold green]")


if __name__ == "__main__":
    app()
