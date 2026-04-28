"""Validate registry, evidence-bank, codebook, and evidence-to-code mapping files.

Expected flexible inputs:
- evidence bank with columns: evidence/e/e#, interview/i#, segment/s#, verbatim_excerpt
- codebook with columns: code, definition
- mappings with columns: evidence, a_codes, b_codes
- aliases with columns: alias, canonical
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from common import (
    console,
    fail_if_errors,
    normalize_column_names,
    read_table,
    require_columns,
    split_codes,
    validate_id,
)

app = typer.Typer(add_completion=False)


def _first_present(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


@app.command()
def main(
    evidence: Path = typer.Option(..., "--evidence", "-e", help="Evidence bank CSV/JSON/XLSX/MD."),
    codebook: Path | None = typer.Option(None, "--codebook", "-c", help="Codebook file."),
    mappings: Path | None = typer.Option(None, "--mappings", "-m", help="E -> code mapping file."),
    aliases: Path | None = typer.Option(None, "--aliases", "-a", help="Alias map file."),
) -> None:
    errors: list[str] = []

    evidence_df = normalize_column_names(read_table(evidence))
    e_col = _first_present(evidence_df, ["evidence", "e", "e_"])
    i_col = _first_present(evidence_df, ["interview", "i", "i_"])
    s_col = _first_present(evidence_df, ["segment", "s", "s_"])
    quote_col = _first_present(evidence_df, ["verbatim_excerpt", "excerpt", "quote"])

    for label, col in {
        "evidence ID": e_col,
        "interview ID": i_col,
        "segment ID": s_col,
        "verbatim excerpt": quote_col,
    }.items():
        if col is None:
            errors.append(f"{evidence} is missing {label} column")

    if e_col:
        bad = evidence_df[~evidence_df[e_col].apply(lambda v: validate_id(v, "evidence"))]
        errors += [f"Bad evidence ID in {evidence}: {v}" for v in bad[e_col].head(20)]
        dupes = evidence_df[evidence_df[e_col].duplicated()][e_col].dropna().unique()
        errors += [f"Duplicate evidence ID in {evidence}: {v}" for v in dupes]

    if i_col:
        bad = evidence_df[~evidence_df[i_col].apply(lambda v: validate_id(v, "interview"))]
        errors += [f"Bad interview ID in {evidence}: {v}" for v in bad[i_col].head(20)]

    if s_col:
        bad = evidence_df[~evidence_df[s_col].apply(lambda v: validate_id(v, "segment"))]
        errors += [f"Bad segment ID in {evidence}: {v}" for v in bad[s_col].head(20)]

    if quote_col:
        empty_quotes = evidence_df[evidence_df[quote_col].fillna("").astype(str).str.strip() == ""]
        if not empty_quotes.empty:
            errors.append(f"{len(empty_quotes)} evidence rows have empty verbatim excerpts")

    evidence_ids = set(evidence_df[e_col].astype(str)) if e_col else set()
    code_ids: set[str] = set()

    if codebook:
        codebook_df = normalize_column_names(read_table(codebook))
        require_columns(codebook_df, ["code", "definition"], codebook)
        for code in codebook_df["code"].astype(str):
            if validate_id(code, "a_code") or validate_id(code, "b_code"):
                code_ids.add(code)
            else:
                errors.append(f"Bad A/B code ID in {codebook}: {code}")

        dupes = codebook_df[codebook_df["code"].duplicated()]["code"].dropna().unique()
        errors += [f"Duplicate code in {codebook}: {v}" for v in dupes]

        empty_defs = codebook_df[codebook_df["definition"].fillna("").astype(str).str.strip() == ""]
        if not empty_defs.empty:
            errors.append(f"{len(empty_defs)} codebook rows have empty definitions")

    if mappings:
        mapping_df = normalize_column_names(read_table(mappings))
        require_columns(mapping_df, ["evidence"], mappings)
        if "a_codes" not in mapping_df.columns and "b_codes" not in mapping_df.columns:
            errors.append(f"{mappings} must include a_codes and/or b_codes")

        for _, row in mapping_df.iterrows():
            ev = str(row["evidence"]).strip()
            if ev not in evidence_ids:
                errors.append(f"Mapping references missing evidence ID: {ev}")

            for col, kind, prefix in (("a_codes", "a_code", "A"), ("b_codes", "b_code", "B")):
                if col not in mapping_df.columns:
                    continue
                for code in split_codes(row[col], prefix=prefix):
                    if not validate_id(code, kind):
                        errors.append(f"Bad {kind} in {mappings}: {code}")
                    if code_ids and code not in code_ids:
                        errors.append(f"Mapping references missing codebook code: {code}")

    if aliases:
        aliases_df = normalize_column_names(read_table(aliases))
        require_columns(aliases_df, ["alias", "canonical"], aliases)
        for _, row in aliases_df.iterrows():
            alias = str(row["alias"]).strip()
            canonical = str(row["canonical"]).strip()
            if code_ids and alias not in code_ids:
                errors.append(f"Alias references missing code: {alias}")
            if code_ids and canonical not in code_ids:
                errors.append(f"Alias canonical references missing code: {canonical}")

    fail_if_errors(errors)
    console.print("Registry files are internally consistent.")


if __name__ == "__main__":
    app()
