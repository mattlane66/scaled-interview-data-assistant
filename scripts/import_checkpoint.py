"""Restore machine-facing tables from a version 1 synthesis checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from checkpoint_validation import CheckpointValidationError, validate_checkpoint_document
from common import console

app = typer.Typer(add_completion=False)

TABLE_FILES = {
    "source_index": "sources.json",
    "interview_index": "interviews.json",
    "episode_index": "episodes.json",
    "segment_index": "segments.json",
    "evidence_bank": "evidence_bank.json",
    "codebook": "codebook.json",
    "evidence_to_code_mappings": "evidence_mappings.json",
    "a_to_b_links": "links.json",
    "clusters": "clusters.json",
    "alias_map": "aliases.json",
}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


@app.command()
def main(
    checkpoint: Path = typer.Option(..., "--checkpoint", "-c"),
    output_dir: Path = typer.Option(Path("data/restored"), "--output-dir", "-o"),
) -> None:
    data = json.loads(checkpoint.read_text())
    try:
        data = validate_checkpoint_document(data)
    except CheckpointValidationError as error:
        raise typer.BadParameter(f"Checkpoint validation failed:\n{error}") from error
    version = str(data["checkpoint_version"])

    output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in TABLE_FILES.items():
        value = data.get(key, [])
        if not isinstance(value, list):
            raise typer.BadParameter(f"Checkpoint field {key} must be a list.")
        write_json(output_dir / filename, value)

    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise typer.BadParameter("Checkpoint metadata must be an object.")
    metadata = {
        **metadata,
        "restored_checkpoint_version": version,
        "analysis_unit": data.get("analysis_unit", "episode"),
        "checkpoint_generated_at": data.get("generated_at"),
        "computation": data.get("computation", {}),
    }
    write_json(output_dir / "metadata.json", metadata)
    (output_dir / "decision-log.md").write_text(str(data.get("decision_log", "")))
    (output_dir / "diff-log.md").write_text(str(data.get("latest_diff_log", "")))
    console.print(f"[bold green]Restored checkpoint tables to {output_dir}[/bold green]")


if __name__ == "__main__":
    app()
