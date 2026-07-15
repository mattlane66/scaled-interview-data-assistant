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
    sources: Path = typer.Option(..., "--sources"),
    links: Path = typer.Option(..., "--links"),
    source_root: Path | None = typer.Option(None, "--source-root"),
    interviews: Path = typer.Option(..., "--interviews"),
    episodes: Path = typer.Option(..., "--episodes"),
    segments: Path = typer.Option(..., "--segments"),
    aliases: Path | None = typer.Option(None, "--aliases"),
    report: Path | None = typer.Option(None, "--report"),
    metadata: Path | None = typer.Option(None, "--metadata"),
    previous_assignments: Path | None = typer.Option(None, "--previous-assignments"),
    output_dir: Path = typer.Option(Path("outputs"), "--output-dir", "-o"),
    unit_column: str = typer.Option("episode", "--unit-column"),
    clusters: str = typer.Option("auto", "--clusters", "-k"),
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
        "--sources",
        str(sources),
        "--links",
        str(links),
        *optional_argument("--source-root", source_root),
        "--interviews",
        str(interviews),
        "--episodes",
        str(episodes),
        "--segments",
        str(segments),
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
        "--links",
        str(links),
        "--output",
        str(matrices_dir / "a_to_b_associations.csv"),
        "--unit-column",
        unit_column,
    )
    clustering_skipped = clusters.lower() == "none"
    if not clustering_skipped:
        run(
            "cluster_interviews.py",
            "--matrix",
            str(matrices_dir / f"{unit_column}_x_combined_code.csv"),
            "--clusters",
            clusters,
            "--unit-column",
            unit_column,
            "--assignments-output",
            str(assignments),
            "--heatmap-output",
            str(heatmap),
            *optional_argument("--previous-assignments", previous_assignments),
        )
        run(
            "validate_registry.py",
            *validation_args,
            "--clusters",
            str(assignments),
            "--unit-column",
            unit_column,
        )

    checkpoint_args = [
        "export_checkpoint.py",
        "--evidence",
        str(evidence),
        "--sources",
        str(sources),
        "--codebook",
        str(codebook),
        "--mappings",
        str(mappings),
        "--links",
        str(links),
        "--analysis-unit",
        unit_column,
        "--output",
        str(output_dir / "CHECKPOINT.json"),
        "--interviews",
        str(interviews),
        "--episodes",
        str(episodes),
        "--segments",
        str(segments),
        *optional_argument("--aliases", aliases),
        *optional_argument("--metadata", metadata),
    ]
    if not clustering_skipped:
        checkpoint_args.extend(
            [
                "--clusters",
                str(assignments),
                "--clustering-method",
                f"average-linkage Jaccard; selection={clusters}",
            ]
        )
    else:
        checkpoint_args.extend(["--clustering-method", "not performed"])
    run(*checkpoint_args)
    if report:
        audit_args = [
            "--report",
            str(report),
            "--evidence",
            str(evidence),
            "--codebook",
            str(codebook),
        ]
        if not clustering_skipped:
            audit_args.extend(["--clusters", str(assignments)])
        run("audit_report.py", *audit_args)
    console.print(f"[bold green]Pipeline completed. Outputs: {output_dir}[/bold green]")


if __name__ == "__main__":
    app()
