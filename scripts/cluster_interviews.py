"""Cluster decision episodes using average-linkage clustering on Jaccard distance.

The historical filename is retained for compatibility. Decision episode is the default analysis
unit; interview-level clustering is available only when explicitly requested.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import typer
from common import (
    console,
    normalize_column_names,
    read_table,
    require_columns,
    validate_id,
    write_table,
)
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_score

app = typer.Typer(add_completion=False)


def _groups(units: list[str], labels: np.ndarray) -> dict[int, set[str]]:
    grouped: dict[int, set[str]] = defaultdict(set)
    for unit, label in zip(units, labels, strict=True):
        grouped[int(label)].add(unit)
    return dict(grouped)


def _next_cluster_id(existing: set[str]) -> str:
    numbers = [int(match.group(1)) for value in existing if (match := re.match(r"^C(\d+)$", value))]
    return f"C{max(numbers, default=0) + 1:02d}"


def stable_cluster_map(
    units: list[str],
    raw_labels: np.ndarray,
    previous: pd.DataFrame | None,
    unit_column: str,
) -> dict[int, str]:
    """Map raw algorithm labels to deterministic or previously registered cluster IDs."""
    current = _groups(units, raw_labels)
    if previous is None or previous.empty:
        ordered = sorted(current, key=lambda label: tuple(sorted(current[label])))
        return {label: f"C{index:02d}" for index, label in enumerate(ordered, start=1)}

    require_columns(previous, [unit_column, "cluster"], "previous assignments")
    invalid_prior_units = [
        value for value in previous[unit_column].astype(str) if not validate_id(value, unit_column)
    ]
    invalid_prior_clusters = [
        value for value in previous["cluster"].astype(str) if not validate_id(value, "cluster")
    ]
    if invalid_prior_units or invalid_prior_clusters:
        raise typer.BadParameter("Previous assignments contain malformed unit or cluster IDs.")
    if previous[unit_column].astype(str).duplicated().any():
        raise typer.BadParameter("Previous assignments contain duplicate analysis units.")
    prior_groups = {
        cluster: set(group[unit_column].astype(str))
        for cluster, group in previous.groupby("cluster")
    }
    raw_ids = sorted(current)
    prior_ids = sorted(prior_groups)
    mapping: dict[int, str] = {}

    if raw_ids and prior_ids:
        scores = np.zeros((len(raw_ids), len(prior_ids)))
        for row, raw_id in enumerate(raw_ids):
            for column, prior_id in enumerate(prior_ids):
                intersection = len(current[raw_id] & prior_groups[prior_id])
                union = len(current[raw_id] | prior_groups[prior_id])
                scores[row, column] = intersection / union if union else 0.0
        rows, columns = linear_sum_assignment(-scores)
        for row, column in zip(rows, columns, strict=True):
            if scores[row, column] > 0:
                mapping[raw_ids[row]] = prior_ids[column]

    used = set(prior_ids)
    for raw_id in raw_ids:
        if raw_id in mapping:
            continue
        cluster_id = _next_cluster_id(used)
        mapping[raw_id] = cluster_id
        used.add(cluster_id)
    return mapping


@app.command()
def main(
    matrix: Path = typer.Option(
        Path("outputs/matrices/episode_x_combined_code.csv"),
        "--matrix",
        "-m",
        help="Analysis-unit x combined A+B code matrix.",
    ),
    clusters: int = typer.Option(3, "--clusters", "-k", help="Target cluster count."),
    unit_column: str = typer.Option(
        "episode",
        "--unit-column",
        help="Analysis unit: episode (recommended) or interview.",
    ),
    previous_assignments: Path | None = typer.Option(
        None,
        "--previous-assignments",
        help="Prior assignments used to preserve registered cluster IDs.",
    ),
    assignments_output: Path | None = typer.Option(None, "--assignments-output"),
    heatmap_output: Path | None = typer.Option(None, "--heatmap-output"),
) -> None:
    if unit_column not in {"episode", "interview"}:
        raise typer.BadParameter("--unit-column must be episode or interview")

    df = normalize_column_names(read_table(matrix))
    require_columns(df, [unit_column], matrix)
    units = df[unit_column].astype(str).tolist()
    duplicate_units = sorted({unit for unit in units if units.count(unit) > 1})
    if duplicate_units:
        raise typer.BadParameter(
            f"Duplicate {unit_column} rows in {matrix}: {', '.join(duplicate_units)}"
        )
    invalid_units = [unit for unit in units if not validate_id(unit, unit_column)]
    if invalid_units:
        raise typer.BadParameter(
            f"Invalid {unit_column} IDs in {matrix}: {', '.join(invalid_units)}"
        )
    feature_df = df.drop(columns=[unit_column]).apply(pd.to_numeric, errors="coerce").fillna(0)

    if len(feature_df) < 2:
        raise typer.BadParameter("Need at least 2 analysis units to cluster.")
    if feature_df.shape[1] == 0:
        raise typer.BadParameter("The matrix has no A/B code columns.")
    if clusters < 2 or clusters > len(feature_df):
        raise typer.BadParameter("--clusters must be between 2 and the number of units.")

    x = feature_df.to_numpy(dtype=float)
    distances = pdist(x, metric="jaccard")
    if np.allclose(distances, 0):
        raise typer.BadParameter("All analysis units have identical code profiles.")

    hierarchy = linkage(distances, method="average")
    raw_labels = fcluster(hierarchy, t=clusters, criterion="maxclust")
    previous = None
    if previous_assignments:
        previous = normalize_column_names(read_table(previous_assignments))
    label_map = stable_cluster_map(units, raw_labels, previous, unit_column)
    cluster_ids = [label_map[int(label)] for label in raw_labels]

    assignments = pd.DataFrame({unit_column: units, "cluster": cluster_ids})
    heatmap = (
        pd.crosstab(assignments[unit_column], assignments["cluster"]).clip(upper=1).reset_index()
    )

    assignments_output = assignments_output or Path(
        f"outputs/matrices/{unit_column}_cluster_assignments.csv"
    )
    heatmap_output = heatmap_output or Path(f"outputs/matrices/{unit_column}_x_cluster.csv")
    write_table(assignments, assignments_output)
    write_table(heatmap, heatmap_output)

    distinct_labels = len(set(raw_labels))
    if distinct_labels > 1 and len(feature_df) > distinct_labels:
        score = silhouette_score(squareform(distances), raw_labels, metric="precomputed")
        console.print(f"Exploratory silhouette score: {score:.3f}")
    if distinct_labels != clusters:
        console.print(
            f"[yellow]Requested {clusters} clusters; tied profiles produced "
            f"{distinct_labels}.[/yellow]"
        )
    console.print(f"[bold green]Wrote cluster outputs to {assignments_output.parent}[/bold green]")


if __name__ == "__main__":
    app()
