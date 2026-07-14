"""Run the validated deterministic portion of the synthesis workflow."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from common import console

app = typer.Typer(add_completion=False)
ROOT = Path(__file__).resolve().parents[1]


def run(script: str, *arguments: str) -> None:
    command = [sys.executable, str(ROOT / "scripts" / script), *arguments]
    subprocess.run(command, cwd=ROOT, check=True)


def optional_argument(flag: str, value: Path | None) -> list[str]:
    return [flag, str(value)] if value else []


@app.command()
def main(
    evidence: Path = typer.Option(..., "--evidence", "-e"),
    codebook: Path = typer.Option(..., "--codebook", "-c"),
    mappings: Path = typer.Option(..., "--mappings", "-m"),
    source_root: Path | None = typer.Option(None, "--source-root"),
    interviews: Path | None = typer.Option(None, "--interviews"),
    episodes: Path | None = typer.Option(None, "--episodes"),
    segments: Path | None = typer.Option(None, "--segments"),
    aliases: Path | None = typer.Option(None, "--aliases"),
    report: Path | None = typer.Option(None, "--report"),
    metadata: Path | None = typer.Option(None, "--metadata"),
    previous_assignments: Path | None = typer.Option(None, "--previous-assignments"),
    output_dir: Path = typer.Option(Path("outputs"), "--output-dir", "-o"),
    unit_column: str = typer.Option("episode", "--unit-column"),
    clusters: int = typer.Option(3, "--clusters", "-k"),
) -> None:
    """Validate inputs, compute associations/clusters, checkpoint, and audit a report."""
    matrices_dir = output_dir / "matrices"
    assignments = matrices_dir / f"{unit_column}_cluster_assignments.csv"
    heatmap = matrices_dir / f"{unit_column}_x_cluster.csv"

    validation_args = [
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
        "--mappings",
        str(mappings),
        *optional_argument("--source-root", source_root),
        *optional_argument("--interviews", interviews),
        *optional_argument("--episodes", episodes),
        *optional_argument("--segments", segments),
        *optional_argument("--aliases", aliases),
    ]
    run("validate_registry.py", *validation_args)

    run(
        "build_matrices.py",
        "--mappings",
        str(mappings),
        "--output-dir",
        str(matrices_dir),
        "--unit-column",
        unit_column,
    )
    run(
        "analyze_links.py",
        "--mappings",
        str(mappings),
        "--codebook",
        str(codebook),
        "--output",
        str(matrices_dir / "a_to_b_associations.csv"),
        "--unit-column",
        unit_column,
    )
    run(
        "cluster_interviews.py",
        "--matrix",
        str(matrices_dir / f"{unit_column}_x_combined_code.csv"),
        "--clusters",
        str(clusters),
        "--unit-column",
        unit_column,
        "--assignments-output",
        str(assignments),
        "--heatmap-output",
        str(heatmap),
        *optional_argument("--previous-assignments", previous_assignments),
    )
    run(
        "export_checkpoint.py",
        "--evidence",
        str(evidence),
        "--codebook",
        str(codebook),
        "--mappings",
        str(mappings),
        "--clusters",
        str(assignments),
        "--analysis-unit",
        unit_column,
        "--cluster-count",
        str(clusters),
        "--output",
        str(output_dir / "CHECKPOINT.json"),
        *optional_argument("--interviews", interviews),
        *optional_argument("--episodes", episodes),
        *optional_argument("--segments", segments),
        *optional_argument("--aliases", aliases),
        *optional_argument("--metadata", metadata),
    )
    if report:
        run(
            "audit_report.py",
            "--report",
            str(report),
            "--evidence",
            str(evidence),
            "--codebook",
            str(codebook),
            "--clusters",
            str(assignments),
        )
    console.print(f"[bold green]Pipeline completed. Outputs: {output_dir}[/bold green]")


if __name__ == "__main__":
    app()
