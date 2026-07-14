"""Audit a synthesis report for traceability and computation guardrails."""

from __future__ import annotations

import re
from pathlib import Path

import typer
from common import console, fail_if_errors, normalize_column_names, read_table

app = typer.Typer(add_completion=False)

EVIDENCE_RE = re.compile(r"\bE\d{3,}\b")
POSSIBLE_EVIDENCE_RE = re.compile(r"\bE\d+\b")
CODE_RE = re.compile(r"\b[AB]\d{2,}\b")
POSSIBLE_CODE_RE = re.compile(r"\b[AB]\d+\b")
CLUSTER_RE = re.compile(r"\bC\d{2,}\b")
POSSIBLE_CLUSTER_RE = re.compile(r"\bC\d+\b")
SECTION_RE = re.compile(r"^#{2,6}\s+(VERIFIED|INFERRED|SPECULATIVE)\s*$", re.I)


def _claim_lines(text: str) -> list[tuple[str, str]]:
    """Return epistemically labelled report lines while ignoring headings and separators."""
    section: str | None = None
    claims: list[tuple[str, str]] = []
    pending_label: str | None = None
    pending_parts: list[str] = []

    def flush() -> None:
        nonlocal pending_label, pending_parts
        if pending_label and pending_parts:
            claims.append((pending_label, " ".join(pending_parts)))
        pending_label = None
        pending_parts = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading = SECTION_RE.match(line)
        if heading:
            flush()
            section = heading.group(1).upper()
            continue
        if line.startswith("#"):
            flush()
            section = None
            continue
        if not line:
            flush()
            continue
        if re.fullmatch(r"\|?[\s:|-]+\|?", line):
            continue
        inline = next(
            (label for label in ("VERIFIED", "INFERRED", "SPECULATIVE") if label in line),
            None,
        )
        label = inline or section
        if label is None:
            flush()
            continue
        if line.startswith(("-", "*", "|")):
            flush()
            pending_label = label
            pending_parts = [line]
        elif pending_label == label:
            pending_parts.append(line)
        elif not line.endswith(":"):
            flush()
            pending_label = label
            pending_parts = [line]
    flush()
    return claims


@app.command()
def main(
    report: Path = typer.Option(..., "--report", "-r", help="Markdown synthesis report."),
    evidence: Path = typer.Option(..., "--evidence", "-e", help="Evidence bank file."),
    codebook: Path | None = typer.Option(None, "--codebook", "-c"),
    clusters: Path | None = typer.Option(None, "--clusters"),
) -> None:
    errors: list[str] = []
    text = report.read_text()

    evidence_df = normalize_column_names(read_table(evidence))
    evidence_col = next((column for column in ("evidence", "e") if column in evidence_df), None)
    if evidence_col is None:
        errors.append(f"{evidence} is missing evidence ID column")
        evidence_ids: set[str] = set()
    else:
        evidence_ids = set(evidence_df[evidence_col].astype(str))

    code_ids: set[str] = set()
    if codebook:
        codebook_df = normalize_column_names(read_table(codebook))
        if "code" in codebook_df:
            code_ids = set(codebook_df["code"].astype(str))
        else:
            errors.append(f"{codebook} is missing code column")

    cluster_ids: set[str] = set()
    if clusters:
        cluster_df = normalize_column_names(read_table(clusters))
        cluster_col = next(
            (column for column in ("cluster", "cluster_id") if column in cluster_df), None
        )
        if cluster_col:
            cluster_ids = set(cluster_df[cluster_col].astype(str))
        else:
            errors.append(f"{clusters} is missing cluster column")

    malformed_evidence = set(POSSIBLE_EVIDENCE_RE.findall(text)) - set(EVIDENCE_RE.findall(text))
    malformed_codes = set(POSSIBLE_CODE_RE.findall(text)) - set(CODE_RE.findall(text))
    malformed_clusters = set(POSSIBLE_CLUSTER_RE.findall(text)) - set(CLUSTER_RE.findall(text))
    errors.extend(
        f"Malformed evidence ID in report: {value}" for value in sorted(malformed_evidence)
    )
    errors.extend(f"Malformed code ID in report: {value}" for value in sorted(malformed_codes))
    errors.extend(
        f"Malformed cluster ID in report: {value}" for value in sorted(malformed_clusters)
    )

    for evidence_id in sorted(set(EVIDENCE_RE.findall(text)) - evidence_ids):
        errors.append(f"Report references missing evidence ID: {evidence_id}")
    if code_ids:
        for code_id in sorted(set(CODE_RE.findall(text)) - code_ids):
            errors.append(f"Report references missing code ID: {code_id}")
    if cluster_ids:
        for cluster_id in sorted(set(CLUSTER_RE.findall(text)) - cluster_ids):
            errors.append(f"Report references missing cluster ID: {cluster_id}")

    for label, line in _claim_lines(text):
        if label in {"VERIFIED", "INFERRED"} and not EVIDENCE_RE.search(line):
            errors.append(f"{label} claim lacks evidence ID: {line[:160]}")

    required_declarations = {
        "analysis unit": "Report does not declare its analysis unit.",
        "clustering method": "Report does not declare clustering method.",
        "computed vs. heuristic": "Report does not declare computed vs. heuristic status.",
    }
    lower_text = text.lower()
    for phrase, message in required_declarations.items():
        if phrase not in lower_text:
            errors.append(message)

    if re.search(r"\b(jaccard|phi)\b", text, re.I):
        if "co-occurrence" not in lower_text and "association" not in lower_text:
            errors.append("Report does not describe Jaccard/phi as association or co-occurrence.")
        if "not causal" not in lower_text and "does not establish causation" not in lower_text:
            errors.append("Report does not state that code association is not causal.")

    fail_if_errors(errors)
    console.print("Report traceability audit passed.")


if __name__ == "__main__":
    app()
