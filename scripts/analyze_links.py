"""Compute A<->B link strengths from an E -> code mapping file.

Primary metric: Jaccard co-occurrence across decision episodes.
Secondary descriptive metric: phi coefficient with explicit support counts.
Optional discovery aid: TF-IDF cosine similarity between code definitions.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import typer
from common import (
    console,
    normalize_column_names,
    read_table,
    require_columns,
    split_tokens,
    validate_id,
    write_table,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = typer.Typer(add_completion=False)


def phi(a: np.ndarray, b: np.ndarray) -> float:
    n11 = int(((a == 1) & (b == 1)).sum())
    n10 = int(((a == 1) & (b == 0)).sum())
    n01 = int(((a == 0) & (b == 1)).sum())
    n00 = int(((a == 0) & (b == 0)).sum())
    denom = np.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    if denom == 0:
        return float("nan")
    return ((n11 * n00) - (n10 * n01)) / denom


def load_code_definitions(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    df = normalize_column_names(read_table(path))
    require_columns(df, ["code", "definition"], path)
    return dict(zip(df["code"].astype(str), df["definition"].astype(str), strict=False))


@app.command()
def main(
    mappings: Path = typer.Option(..., "--mappings", "-m", help="E -> code mapping file."),
    codebook: Path | None = typer.Option(None, "--codebook", "-c", help="Optional codebook."),
    output: Path = typer.Option(
        Path("outputs/matrices/a_to_b_link_strengths.csv"), "--output", "-o"
    ),
    unit_column: str = typer.Option(
        "episode",
        "--unit-column",
        help="Analysis unit: episode (recommended) or interview.",
    ),
    minimum_support: int = typer.Option(
        2,
        "--minimum-support",
        min=1,
        help="Co-occurrence count below which a link is marked low-support.",
    ),
) -> None:
    df = normalize_column_names(read_table(mappings))
    if unit_column not in {"episode", "interview"}:
        raise typer.BadParameter("--unit-column must be episode or interview")
    require_columns(df, [unit_column, "evidence", "a_codes", "b_codes"], mappings)

    rows: list[dict[str, str]] = []
    all_units = sorted(df[unit_column].astype(str).str.strip().unique())
    invalid_units = [unit for unit in all_units if not validate_id(unit, unit_column)]
    if invalid_units:
        raise typer.BadParameter(
            f"Invalid {unit_column} IDs in {mappings}: {', '.join(invalid_units)}"
        )
    for _, row in df.iterrows():
        unit = str(row[unit_column]).strip()
        a_codes = split_tokens(row["a_codes"])
        b_codes = split_tokens(row["b_codes"])
        invalid_a = [code for code in a_codes if not validate_id(code, "a_code")]
        invalid_b = [code for code in b_codes if not validate_id(code, "b_code")]
        if invalid_a or invalid_b:
            raise typer.BadParameter(
                f"Invalid code family in {mappings}: {', '.join(invalid_a + invalid_b)}"
            )
        for code in a_codes + b_codes:
            rows.append({unit_column: unit, "code": code})

    if not rows:
        raise typer.BadParameter("No A/B codes found.")

    long_df = pd.DataFrame(rows).drop_duplicates()
    matrix = pd.crosstab(long_df[unit_column], long_df["code"]).clip(upper=1)
    matrix = matrix.reindex(all_units, fill_value=0)
    a_cols = sorted([col for col in matrix.columns if str(col).startswith("A")])
    b_cols = sorted([col for col in matrix.columns if str(col).startswith("B")])
    if not a_cols or not b_cols:
        raise typer.BadParameter(
            "Association analysis requires at least one A-code and one B-code."
        )

    definitions = load_code_definitions(codebook)
    cosine_by_pair: dict[tuple[str, str], float] = {}
    if definitions:
        texts = [definitions.get(code, "") for code in a_cols + b_cols]
        if any(texts):
            try:
                vectors = TfidfVectorizer().fit_transform(texts)
                sim = cosine_similarity(vectors)
                idx = {code: i for i, code in enumerate(a_cols + b_cols)}
                for a_code, b_code in product(a_cols, b_cols):
                    cosine_by_pair[(a_code, b_code)] = float(sim[idx[a_code], idx[b_code]])
            except ValueError:
                console.print("[yellow]Code definitions had no usable TF-IDF terms.[/yellow]")

    n = len(matrix)
    out_rows = []
    for a_code, b_code in product(a_cols, b_cols):
        a = matrix[a_code].to_numpy()
        b = matrix[b_code].to_numpy()
        intersection = int(((a == 1) & (b == 1)).sum())
        union = int(((a == 1) | (b == 1)).sum())
        jaccard = intersection / union if union else 0.0
        phi_value = phi(a, b)
        low_support = intersection < minimum_support or n < 10
        out_rows.append(
            {
                "analysis_unit": unit_column,
                "a_code": a_code,
                "b_code": b_code,
                "n_units": n,
                "a_units": int(a.sum()),
                "b_units": int(b.sum()),
                "cooccurring_units": intersection,
                "union_units": union,
                "jaccard": round(jaccard, 4),
                "phi": round(float(phi_value), 4) if not np.isnan(phi_value) else "",
                "definition_cosine": round(cosine_by_pair.get((a_code, b_code), np.nan), 4)
                if (a_code, b_code) in cosine_by_pair
                else "",
                "low_support_flag": low_support,
                "negative_edge_flag": bool(
                    not low_support and not np.isnan(phi_value) and phi_value < -0.20
                ),
            }
        )

    result = pd.DataFrame(out_rows).sort_values(
        ["jaccard", "cooccurring_units"], ascending=[False, False]
    )
    write_table(result, output)
    console.print(f"[bold green]Wrote A<->B links to {output}[/bold green]")


if __name__ == "__main__":
    app()
