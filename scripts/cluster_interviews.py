"""Cluster interviews using Ward hierarchical clustering on combined A+B incidence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from common import console, normalize_column_names, read_table, write_table

app = typer.Typer(add_completion=False)


@app.command()
def main(
    matrix: Path = typer.Option(
        Path("outputs/matrices/interview_x_combined_code.csv"),
        "--matrix",
        "-m",
        help="Interview x combined A+B code matrix.",
    ),
    clusters: int = typer.Option(3, "--clusters", "-k", help="Target number of clusters."),
    assignments_output: Path = typer.Option(
        Path("outputs/matrices/interview_cluster_assignments.csv"), "--assignments-output"
    ),
    heatmap_output: Path = typer.Option(
        Path("outputs/matrices/interview_x_cluster.csv"), "--heatmap-output"
    ),
) -> None:
    df = normalize_column_names(read_table(matrix))
    if "interview" not in df.columns:
        raise typer.BadParameter(f"{matrix} must include an interview column.")

    interviews = df["interview"].astype(str)
    feature_df = df.drop(columns=["interview"]).apply(pd.to_numeric, errors="coerce").fillna(0)

    if len(feature_df) < 2:
        raise typer.BadParameter("Need at least 2 interviews to cluster.")
    if clusters < 2 or clusters > len(feature_df):
        raise typer.BadParameter("--clusters must be between 2 and the number of interviews.")

    # Ward clustering uses Euclidean distance. Scaling keeps high-frequency codes from dominating.
    x = StandardScaler(with_mean=True, with_std=True).fit_transform(feature_df)
    z = linkage(x, method="ward")
    labels = fcluster(z, t=clusters, criterion="maxclust")
    cluster_ids = [f"C{label:02d}" for label in labels]

    assignments = pd.DataFrame({"interview": interviews, "cluster": cluster_ids})
    heatmap = pd.crosstab(assignments["interview"], assignments["cluster"]).clip(upper=1).reset_index()

    write_table(assignments, assignments_output)
    write_table(heatmap, heatmap_output)

    if len(set(labels)) > 1 and len(feature_df) > clusters:
        score = silhouette_score(x, labels)
        console.print(f"Silhouette score: {score:.3f}")

    console.print(f"[bold green]Wrote cluster outputs to {assignments_output.parent}[/bold green]")


if __name__ == "__main__":
    app()
