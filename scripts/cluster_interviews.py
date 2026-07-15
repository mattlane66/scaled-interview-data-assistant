"""Cluster decision episodes with average linkage on Jaccard distance.

The historical filename is retained for compatibility. Clustering may be automatic, explicitly
sized, reduced to one coherent group, or skipped.
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
    """Map raw labels to deterministic or previously registered cluster IDs."""
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
        if raw_id not in mapping:
            cluster_id = _next_cluster_id(used)
            mapping[raw_id] = cluster_id
            used.add(cluster_id)
    return mapping


def _labels_for_k(distances: np.ndarray, hierarchy: np.ndarray, k: int, n_units: int) -> np.ndarray:
    if k == 1:
        return np.ones(n_units, dtype=int)
    return fcluster(hierarchy, t=k, criterion="maxclust")


def _automatic_labels(
    distances: np.ndarray, hierarchy: np.ndarray, n_units: int
) -> tuple[np.ndarray, float | None]:
    if n_units < 3 or np.allclose(distances, 0):
        return np.ones(n_units, dtype=int), None

    distance_matrix = squareform(distances)
    best_labels: np.ndarray | None = None
    best_score: float | None = None
    for k in range(2, min(6, n_units - 1) + 1):
        labels = _labels_for_k(distances, hierarchy, k, n_units)
        distinct = len(set(labels))
        if distinct < 2 or distinct >= n_units:
            continue
        score = float(silhouette_score(distance_matrix, labels, metric="precomputed"))
        if best_score is None or score > best_score:
            best_labels = labels
            best_score = score
    return (best_labels if best_labels is not None else np.ones(n_units, dtype=int), best_score)


@app.command()
def main(
    matrix: Path = typer.Option(
        Path("outputs/matrices/episode_x_combined_code.csv"),
        "--matrix",
        "-m",
        help="Analysis-unit x combined A+B code matrix.",
    ),
    clusters: str = typer.Option(
        "auto", "--clusters", "-k", help="Cluster count, 'auto', or 'none'."
    ),
    unit_column: str = typer.Option(
        "episode", "--unit-column", help="Analysis unit: episode (recommended) or interview."
    ),
    previous_assignments: Path | None = typer.Option(
        None, "--previous-assignments", help="Prior assignments used to preserve cluster IDs."
    ),
    assignments_output: Path | None = typer.Option(None, "--assignments-output"),
    heatmap_output: Path | None = typer.Option(None, "--heatmap-output"),
) -> None:
    if unit_column not in {"episode", "interview"}:
        raise typer.BadParameter("--unit-column must be episode or interview")

    df = normalize_column_names(read_table(matrix))
    require_columns(df, [unit_column], matrix)
    units = df[unit_column].astype(str).tolist()
    duplicates = sorted({unit for unit in units if units.count(unit) > 1})
    if duplicates:
        raise typer.BadParameter(f"Duplicate {unit_column} rows: {', '.join(duplicates)}")
    invalid_units = [unit for unit in units if not validate_id(unit, unit_column)]
    if invalid_units:
        raise typer.BadParameter(f"Invalid {unit_column} IDs: {', '.join(invalid_units)}")

    assignments_output = assignments_output or Path(
        f"outputs/matrices/{unit_column}_cluster_assignments.csv"
    )
    heatmap_output = heatmap_output or Path(f"outputs/matrices/{unit_column}_x_cluster.csv")
    if clusters.lower() == "none":
        write_table(pd.DataFrame(columns=[unit_column, "cluster"]), assignments_output)
        write_table(pd.DataFrame({unit_column: units}), heatmap_output)
        console.print("[yellow]Clustering skipped by request.[/yellow]")
        return

    feature_df = df.drop(columns=[unit_column]).apply(pd.to_numeric, errors="coerce").fillna(0)
    if feature_df.empty:
        raise typer.BadParameter("Need at least one analysis unit to cluster.")
    if feature_df.shape[1] == 0:
        raise typer.BadParameter("The matrix has no A/B code columns.")

    x = feature_df.to_numpy(dtype=float)
    n_units = len(feature_df)
    distances = pdist(x, metric="jaccard") if n_units > 1 else np.array([])
    hierarchy = (
        linkage(distances, method="average")
        if n_units > 1 and not np.allclose(distances, 0)
        else np.empty((0, 4))
    )

    selected_score: float | None = None
    if clusters.lower() == "auto":
        if n_units == 1 or np.allclose(distances, 0):
            raw_labels = np.ones(n_units, dtype=int)
        else:
            raw_labels, selected_score = _automatic_labels(distances, hierarchy, n_units)
    else:
        try:
            requested = int(clusters)
        except ValueError as error:
            raise typer.BadParameter(
                "--clusters must be 'auto', 'none', or a positive integer"
            ) from error
        if requested < 1 or requested > n_units:
            raise typer.BadParameter("--clusters must be between 1 and the number of units")
        if requested > 1 and (n_units == 1 or np.allclose(distances, 0)):
            console.print("[yellow]Identical profiles support only one computed cluster.[/yellow]")
            raw_labels = np.ones(n_units, dtype=int)
        else:
            raw_labels = _labels_for_k(distances, hierarchy, requested, n_units)

    previous = (
        normalize_column_names(read_table(previous_assignments))
        if previous_assignments
        else None
    )
    label_map = stable_cluster_map(units, raw_labels, previous, unit_column)
    cluster_ids = [label_map[int(label)] for label in raw_labels]
    assignments = pd.DataFrame({unit_column: units, "cluster": cluster_ids})
    heatmap = (
        pd.crosstab(assignments[unit_column], assignments["cluster"]).clip(upper=1).reset_index()
    )
    write_table(assignments, assignments_output)
    write_table(heatmap, heatmap_output)

    distinct = len(set(raw_labels))
    if selected_score is None and distinct > 1 and n_units > distinct:
        selected_score = float(
            silhouette_score(squareform(distances), raw_labels, metric="precomputed")
        )
    if selected_score is not None:
        console.print(f"Exploratory silhouette score: {selected_score:.3f}")
    console.print(f"Actual cluster count: {distinct}")
    console.print(f"[bold green]Wrote cluster outputs to {assignments_output.parent}[/bold green]")


if __name__ == "__main__":
    app()
