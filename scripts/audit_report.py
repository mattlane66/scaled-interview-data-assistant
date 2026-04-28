"""Audit a synthesis report for traceability and computation guardrails."""

from __future__ import annotations

import re
from pathlib import Path

import typer

from common import console, fail_if_errors, normalize_column_names, read_table

app = typer.Typer(add_completion=False)

EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
CODE_RE = re.compile(r"\b[AB]\d{2,}\b")
CLUSTER_RE = re.compile(r"\bC\d{2,}\b")


@app.command()
def main(
    report: Path = typer.Option(..., "--report", "-r", help="Markdown synthesis report."),
    evidence: Path = typer.Option(..., "--evidence", "-e", help="Evidence bank file."),
    codebook: Path | None = typer.Option(None, "--codebook", "-c"),
    clusters: Path | None = typer.Option(None, "--clusters"),
    n_interviews: int | None = typer.Option(None, "--n-interviews", "-n"),
) -> None:
    errors: list[str] = []
    text = report.read_text()

    evidence_df = normalize_column_names(read_table(evidence))
    evidence_col = next((c for c in ["evidence", "e", "e_"] if c in evidence_df.columns), None)
    if evidence_col is None:
        errors.append(f"{evidence} is missing evidence ID column")
        evidence_ids = set()
    else:
        evidence_ids = set(evidence_df[evidence_col].astype(str))

    code_ids = set()
    if codebook:
        codebook_df = normalize_column_names(read_table(codebook))
        if "code" in codebook_df.columns:
            code_ids = set(codebook_df["code"].astype(str))
        else:
            errors.append(f"{codebook} is missing code column")

    cluster_ids = set()
    if clusters:
        clusters_df = normalize_column_names(read_table(clusters))
        cluster_col = next((c for c in ["cluster", "cluster_id"] if c in clusters_df.columns), None)
        if cluster_col:
            cluster_ids = set(clusters_df[cluster_col].astype(str))
        else:
            errors.append(f"{clusters} is missing cluster column")

    for evidence_id in sorted(set(EVIDENCE_RE.findall(text)) - evidence_ids):
        errors.append(f"Report references missing evidence ID: {evidence_id}")

    if code_ids:
        for code_id in sorted(set(CODE_RE.findall(text)) - code_ids):
            errors.append(f"Report references missing code ID: {code_id}")

    if cluster_ids:
        for cluster_id in sorted(set(CLUSTER_RE.findall(text)) - cluster_ids):
            errors.append(f"Report references missing cluster ID: {cluster_id}")

    verified_lines = [
        line for line in text.splitlines() if "VERIFIED" in line and not EVIDENCE_RE.search(line)
    ]
    for line in verified_lines[:20]:
        errors.append(f"VERIFIED claim lacks evidence ID: {line[:160]}")

    if n_interviews is not None and n_interviews < 5:
        phi_mentions = [line for line in text.splitlines() if re.search(r"\bphi\b", line, re.I)]
        bad_phi = [line for line in phi_mentions if "N < 5" not in line and "below" not in line.lower()]
        if bad_phi:
            errors.append("Report appears to use/discuss phi without noting N < 5 limitation.")

    if "Clustering method" not in text and "clustering method" not in text:
        errors.append("Report does not declare clustering method.")

    if "Computed vs. heuristic" not in text and "HEURISTIC" not in text:
        errors.append("Report does not declare computed vs. heuristic status.")

    fail_if_errors(errors)
    console.print("Report traceability audit passed.")


if __name__ == "__main__":
    app()
