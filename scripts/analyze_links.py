"""Aggregate explicit A<->B links and compute secondary co-occurrence diagnostics.

Primary evidence is the reviewed link registry when supplied. Jaccard, descriptive phi, and optional
definition cosine are secondary signals; none establishes causation, importance, or prevalence.
"""

from __future__ import annotations

from collections import defaultdict
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


def phi_from_counts(n11: int, n10: int, n01: int, n00: int) -> float:
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


def load_reviewed_links(
    path: Path | None,
    unit_column: str,
    episode_to_interview: dict[str, str],
) -> tuple[
    dict[tuple[str, str], set[str]],
    dict[tuple[str, str], set[str]],
    dict[tuple[str, str], set[str]],
]:
    explicit: dict[tuple[str, str], set[str]] = defaultdict(set)
    inferred: dict[tuple[str, str], set[str]] = defaultdict(set)
    evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    if path is None:
        return explicit, inferred, evidence

    df = normalize_column_names(read_table(path))
    require_columns(df, ["episode", "a_code", "b_code", "basis", "evidence"], path)
    for _, row in df.iterrows():
        episode = str(row["episode"]).strip()
        unit = episode if unit_column == "episode" else episode_to_interview.get(episode, "")
        if not unit:
            raise typer.BadParameter(f"Cannot resolve analysis unit for link episode {episode}")
        a_code = str(row["a_code"]).strip()
        b_code = str(row["b_code"]).strip()
        if not validate_id(a_code, "a_code") or not validate_id(b_code, "b_code"):
            raise typer.BadParameter(f"Invalid A/B link pair in {path}: {a_code}/{b_code}")
        pair = (a_code, b_code)
        basis = str(row["basis"]).strip().upper()
        if basis == "EXPLICIT":
            explicit[pair].add(unit)
        elif basis == "INFERRED":
            inferred[pair].add(unit)
        else:
            raise typer.BadParameter(f"Invalid link basis in {path}: {basis}")
        evidence[pair].update(split_tokens(row["evidence"]))
    return explicit, inferred, evidence


@app.command()
def main(
    mappings: Path = typer.Option(..., "--mappings", "-m", help="E -> code mapping file."),
    codebook: Path | None = typer.Option(None, "--codebook", "-c", help="Optional codebook."),
    links: Path | None = typer.Option(
        None, "--links", help="Reviewed explicit/inferred link registry."
    ),
    output: Path = typer.Option(
        Path("outputs/matrices/a_to_b_associations.csv"), "--output", "-o"
    ),
    unit_column: str = typer.Option(
        "episode", "--unit-column", help="Analysis unit: episode (recommended) or interview."
    ),
    minimum_support: int = typer.Option(
        2, "--minimum-support", min=1, help="Minimum co-occurrence count for phi reporting."
    ),
    nonoccurrence_assessable: bool = typer.Option(
        False,
        "--nonoccurrence-assessable",
        help="Permit negative-edge flags only when zeros represent assessed nonoccurrence.",
    ),
) -> None:
    df = normalize_column_names(read_table(mappings))
    if unit_column not in {"episode", "interview"}:
        raise typer.BadParameter("--unit-column must be episode or interview")
    require_columns(
        df,
        [unit_column, "episode", "interview", "evidence", "a_codes", "b_codes"],
        mappings,
    )

    all_units = sorted(df[unit_column].astype(str).str.strip().unique())
    invalid_units = [unit for unit in all_units if not validate_id(unit, unit_column)]
    if invalid_units:
        raise typer.BadParameter(
            f"Invalid {unit_column} IDs in {mappings}: {', '.join(invalid_units)}"
        )

    episode_to_interview: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        episode = str(row["episode"]).strip()
        interview = str(row["interview"]).strip()
        owner = episode_to_interview.setdefault(episode, interview)
        if owner != interview:
            raise typer.BadParameter(f"Episode {episode} maps to multiple interviews")
        unit = str(row[unit_column]).strip()
        a_codes = split_tokens(row["a_codes"])
        b_codes = split_tokens(row["b_codes"])
        invalid_a = [code for code in a_codes if not validate_id(code, "a_code")]
        invalid_b = [code for code in b_codes if not validate_id(code, "b_code")]
        if invalid_a or invalid_b:
            raise typer.BadParameter(
                f"Invalid code family in {mappings}: {', '.join(invalid_a + invalid_b)}"
            )
        rows.extend({unit_column: unit, "code": code} for code in a_codes + b_codes)

    if not rows:
        raise typer.BadParameter("No A/B codes found.")

    long_df = pd.DataFrame(rows).drop_duplicates()
    matrix = pd.crosstab(long_df[unit_column], long_df["code"]).clip(upper=1)
    matrix = matrix.reindex(all_units, fill_value=0)
    a_cols = sorted(col for col in matrix.columns if str(col).startswith("A"))
    b_cols = sorted(col for col in matrix.columns if str(col).startswith("B"))
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
                similarity = cosine_similarity(vectors)
                index = {code: i for i, code in enumerate(a_cols + b_cols)}
                for a_code, b_code in product(a_cols, b_cols):
                    cosine_by_pair[(a_code, b_code)] = float(
                        similarity[index[a_code], index[b_code]]
                    )
            except ValueError:
                console.print("[yellow]Code definitions had no usable TF-IDF terms.[/yellow]")

    explicit, inferred, link_evidence = load_reviewed_links(
        links, unit_column, episode_to_interview
    )
    n_units = len(matrix)
    output_rows: list[dict[str, object]] = []
    for a_code, b_code in product(a_cols, b_cols):
        a = matrix[a_code].to_numpy()
        b = matrix[b_code].to_numpy()
        n11 = int(((a == 1) & (b == 1)).sum())
        n10 = int(((a == 1) & (b == 0)).sum())
        n01 = int(((a == 0) & (b == 1)).sum())
        n00 = int(((a == 0) & (b == 0)).sum())
        union = n11 + n10 + n01
        jaccard = n11 / union if union else 0.0
        low_support = n11 < minimum_support or n_units < 10
        raw_phi = phi_from_counts(n11, n10, n01, n00)
        reported_phi = "" if low_support or np.isnan(raw_phi) else round(float(raw_phi), 4)
        pair = (a_code, b_code)
        explicit_units = explicit.get(pair, set())
        inferred_units = inferred.get(pair, set())
        linked_units = explicit_units | inferred_units
        output_rows.append(
            {
                "analysis_unit": unit_column,
                "a_code": a_code,
                "b_code": b_code,
                "n_units": n_units,
                "a_units": int(a.sum()),
                "b_units": int(b.sum()),
                "n11": n11,
                "n10": n10,
                "n01": n01,
                "n00": n00,
                "cooccurring_units": n11,
                "union_units": union,
                "jaccard": round(jaccard, 4),
                "phi": reported_phi,
                "definition_cosine": round(cosine_by_pair[pair], 4)
                if pair in cosine_by_pair
                else "",
                "explicit_linked_units": len(explicit_units),
                "inferred_linked_units": len(inferred_units),
                "linked_units": len(linked_units),
                "supporting_evidence": ", ".join(sorted(link_evidence.get(pair, set()))),
                "link_registry_status": "REVIEWED" if links else "NOT_PROVIDED",
                "low_support_flag": low_support,
                "negative_edge_flag": bool(
                    nonoccurrence_assessable
                    and not low_support
                    and not np.isnan(raw_phi)
                    and raw_phi < -0.20
                ),
            }
        )

    result = pd.DataFrame(output_rows).sort_values(
        ["linked_units", "jaccard", "cooccurring_units"], ascending=[False, False, False]
    )
    write_table(result, output)
    console.print(f"[bold green]Wrote A<->B associations to {output}[/bold green]")


if __name__ == "__main__":
    app()
