"""Build binary interview x code incidence matrices from E -> code mappings."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from common import console, normalize_column_names, read_table, require_columns, split_codes, write_table

app = typer.Typer(add_completion=False)


@app.command()
def main(
    mappings: Path = typer.Option(..., "--mappings", "-m", help="E -> code mapping file."),
    output_dir: Path = typer.Option(
        Path("outputs/matrices"), "--output-dir", "-o", help="Directory for matrix CSVs."
    ),
) -> None:
    df = normalize_column_names(read_table(mappings))
    require_columns(df, ["interview", "evidence"], mappings)

    if "a_codes" not in df.columns and "b_codes" not in df.columns:
        raise typer.BadParameter(f"{mappings} must include a_codes and/or b_codes")

    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        interview = str(row["interview"]).strip()
        for code in split_codes(row.get("a_codes", ""), prefix="A"):
            rows.append({"interview": interview, "code": code, "family": "A"})
        for code in split_codes(row.get("b_codes", ""), prefix="B"):
            rows.append({"interview": interview, "code": code, "family": "B"})

    long_df = pd.DataFrame(rows)
    if long_df.empty:
        raise typer.BadParameter("No A/B codes found in mapping file.")

    def pivot(family: str | None = None) -> pd.DataFrame:
        subset = long_df if family is None else long_df[long_df["family"] == family]
        if subset.empty:
            return pd.DataFrame({"interview": sorted(long_df["interview"].unique())})
        matrix = pd.crosstab(subset["interview"], subset["code"]).clip(upper=1)
        return matrix.reset_index()

    a_matrix = pivot("A")
    b_matrix = pivot("B")
    combined_matrix = pivot(None)

    write_table(a_matrix, output_dir / "interview_x_a_code.csv")
    write_table(b_matrix, output_dir / "interview_x_b_code.csv")
    write_table(combined_matrix, output_dir / "interview_x_combined_code.csv")

    console.print(f"[bold green]Wrote matrices to {output_dir}[/bold green]")


if __name__ == "__main__":
    app()
