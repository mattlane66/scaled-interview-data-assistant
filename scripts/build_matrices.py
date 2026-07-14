"""Build binary analysis-unit x code incidence matrices from evidence mappings."""

from __future__ import annotations

from pathlib import Path

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

app = typer.Typer(add_completion=False)


@app.command()
def main(
    mappings: Path = typer.Option(..., "--mappings", "-m", help="E -> code mapping file."),
    output_dir: Path = typer.Option(
        Path("outputs/matrices"), "--output-dir", "-o", help="Directory for matrix CSVs."
    ),
    unit_column: str = typer.Option(
        "episode",
        "--unit-column",
        help="Analysis unit: episode (recommended) or interview.",
    ),
) -> None:
    df = normalize_column_names(read_table(mappings))
    if unit_column not in {"episode", "interview"}:
        raise typer.BadParameter("--unit-column must be episode or interview")
    require_columns(df, [unit_column, "evidence", "a_codes", "b_codes"], mappings)

    all_units = sorted(df[unit_column].astype(str).str.strip().unique())
    invalid_units = [unit for unit in all_units if not validate_id(unit, unit_column)]
    if invalid_units:
        raise typer.BadParameter(
            f"Invalid {unit_column} IDs in {mappings}: {', '.join(invalid_units)}"
        )
    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        unit = str(row[unit_column]).strip()
        for code in split_tokens(row["a_codes"]):
            if not validate_id(code, "a_code"):
                raise typer.BadParameter(f"Invalid A-code in {mappings}: {code}")
            rows.append({unit_column: unit, "code": code, "family": "A"})
        for code in split_tokens(row["b_codes"]):
            if not validate_id(code, "b_code"):
                raise typer.BadParameter(f"Invalid B-code in {mappings}: {code}")
            rows.append({unit_column: unit, "code": code, "family": "B"})

    long_df = pd.DataFrame(rows)
    if long_df.empty:
        raise typer.BadParameter("No A/B codes found in mapping file.")

    def pivot(family: str | None = None) -> pd.DataFrame:
        subset = long_df if family is None else long_df[long_df["family"] == family]
        if subset.empty:
            return pd.DataFrame({unit_column: all_units})
        matrix = pd.crosstab(subset[unit_column], subset["code"]).clip(upper=1)
        matrix = matrix.reindex(all_units, fill_value=0)
        matrix.index.name = unit_column
        return matrix.reset_index()

    a_matrix = pivot("A")
    b_matrix = pivot("B")
    combined_matrix = pivot(None)

    write_table(a_matrix, output_dir / f"{unit_column}_x_a_code.csv")
    write_table(b_matrix, output_dir / f"{unit_column}_x_b_code.csv")
    write_table(combined_matrix, output_dir / f"{unit_column}_x_combined_code.csv")

    console.print(f"[bold green]Wrote matrices to {output_dir}[/bold green]")


if __name__ == "__main__":
    app()
