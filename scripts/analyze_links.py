"""Compute A<->B link strengths from an E -> code mapping file.

Primary metric: Jaccard co-occurrence across interviews.
Secondary metric: phi coefficient when N >= 5.
Optional text metric: TF-IDF cosine similarity between code definitions.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
import typer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from common import console, normalize_column_names, read_table, require_columns, split_codes, write_table

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
) -> None:
    df = normalize_column_names(read_table(mappings))
    require_columns(df, ["interview", "evidence", "a_codes", "b_codes"], mappings)

    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        interview = str(row["interview"]).strip()
        a_codes = split_codes(row["a_codes"], prefix="A")
        b_codes = split_codes(row["b_codes"], prefix="B")
        for code in a_codes + b_codes:
            rows.append({"interview": interview, "code": code})

    if not rows:
        raise typer.BadParameter("No A/B codes found.")

    long_df = pd.DataFrame(rows).drop_duplicates()
    matrix = pd.crosstab(long_df["interview"], long_df["code"]).clip(upper=1)
    a_cols = sorted([col for col in matrix.columns if str(col).startswith("A")])
    b_cols = sorted([col for col in matrix.columns if str(col).startswith("B")])

    definitions = load_code_definitions(codebook)
    cosine_by_pair: dict[tuple[str, str], float] = {}
    if definitions:
        texts = [definitions.get(code, "") for code in a_cols + b_cols]
        if any(texts):
            vectors = TfidfVectorizer().fit_transform(texts)
            sim = cosine_similarity(vectors)
            idx = {code: i for i, code in enumerate(a_cols + b_cols)}
            for a_code, b_code in product(a_cols, b_cols):
                cosine_by_pair[(a_code, b_code)] = float(sim[idx[a_code], idx[b_code]])

    n = len(matrix)
    out_rows = []
    for a_code, b_code in product(a_cols, b_cols):
        a = matrix[a_code].to_numpy()
        b = matrix[b_code].to_numpy()
        intersection = int(((a == 1) & (b == 1)).sum())
        union = int(((a == 1) | (b == 1)).sum())
        jaccard = intersection / union if union else 0.0
        phi_value = phi(a, b) if n >= 5 else np.nan
        out_rows.append(
            {
                "a_code": a_code,
                "b_code": b_code,
                "n_interviews": n,
                "cooccurring_interviews": intersection,
                "jaccard": round(jaccard, 4),
                "phi": round(float(phi_value), 4) if not np.isnan(phi_value) else "",
                "cosine": round(cosine_by_pair.get((a_code, b_code), np.nan), 4)
                if (a_code, b_code) in cosine_by_pair
                else "",
                "negative_edge_flag": bool(n >= 5 and not np.isnan(phi_value) and phi_value < -0.20),
            }
        )

    result = pd.DataFrame(out_rows).sort_values(
        ["jaccard", "cooccurring_interviews"], ascending=[False, False]
    )
    write_table(result, output)
    console.print(f"[bold green]Wrote A<->B links to {output}[/bold green]")


if __name__ == "__main__":
    app()
