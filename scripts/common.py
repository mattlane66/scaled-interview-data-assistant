"""Shared helpers for deterministic JTBD/A2B synthesis scripts.

The scripts intentionally avoid LLM calls. They validate and compute over analyst/model-produced
artifacts so synthesis reports can separate interpretation from calculation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import typer
import yaml
from rich.console import Console

console = Console()

ID_PATTERNS = {
    "interview": re.compile(r"^I\d{2,}$"),
    "segment": re.compile(r"^S\d{2,}$"),
    "evidence": re.compile(r"^E\d{3,}$"),
    "a_code": re.compile(r"^A\d{2,}$"),
    "b_code": re.compile(r"^B\d{2,}$"),
    "cluster": re.compile(r"^C\d{2,}$"),
}


def read_table(path: Path) -> pd.DataFrame:
    """Read CSV, Excel, JSON, JSONL, YAML, or Markdown table files."""
    if not path.exists():
        raise typer.BadParameter(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".json":
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            for key in ("rows", "data", "evidence_bank", "codebook", "mappings"):
                if isinstance(data.get(key), list):
                    return pd.DataFrame(data[key])
            return pd.DataFrame([data])
        return pd.DataFrame(data)
    if suffix in {".jsonl", ".ndjson"}:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        return pd.DataFrame(rows)
    if suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(path.read_text())
        if isinstance(data, dict):
            for key in ("rows", "data", "evidence_bank", "codebook", "mappings"):
                if isinstance(data.get(key), list):
                    return pd.DataFrame(data[key])
            return pd.DataFrame([data])
        return pd.DataFrame(data)
    if suffix == ".md":
        return read_markdown_table(path)

    raise typer.BadParameter(f"Unsupported file type: {path.suffix}")


def read_markdown_table(path: Path) -> pd.DataFrame:
    """Parse the first GitHub-style Markdown table in a file."""
    lines = path.read_text().splitlines()
    table_lines: list[str] = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines.append(stripped)
            in_table = True
        elif in_table:
            break

    if len(table_lines) < 2:
        raise typer.BadParameter(f"No Markdown table found in {path}")

    header = [clean_cell(c) for c in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:
        cells = [clean_cell(c) for c in line.strip("|").split("|")]
        if len(cells) == len(header):
            rows.append(cells)

    return pd.DataFrame(rows, columns=header)


def clean_cell(value: Any) -> str:
    return str(value).strip()


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common human-readable column names to snake-ish names."""
    rename = {}
    for col in df.columns:
        normalized = str(col).strip().lower()
        normalized = normalized.replace("↔", "_to_")
        normalized = normalized.replace("<->", "_to_")
        normalized = normalized.replace("->", "_to_")
        normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
        rename[col] = normalized
    return df.rename(columns=rename)


def split_codes(value: Any, prefix: str | None = None) -> list[str]:
    """Split cells like 'A01, A02; A03' into code lists."""
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[,;/\n]+", text)
    codes = []
    for part in parts:
        candidate = part.strip()
        if not candidate or candidate in {"-", "—"}:
            continue
        if prefix and not candidate.startswith(prefix):
            continue
        codes.append(candidate)
    return codes


def require_columns(df: pd.DataFrame, required: list[str], source: Path | str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise typer.BadParameter(f"{source} is missing required columns: {', '.join(missing)}")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_table(df: pd.DataFrame, path: Path) -> None:
    ensure_parent(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix in {".xlsx", ".xls"}:
        df.to_excel(path, index=False)
    elif suffix == ".json":
        path.write_text(json.dumps(df.to_dict(orient="records"), indent=2))
    else:
        raise typer.BadParameter(f"Unsupported output type: {path.suffix}")


def validate_id(value: Any, kind: str) -> bool:
    if pd.isna(value):
        return False
    return bool(ID_PATTERNS[kind].match(str(value).strip()))


def fail_if_errors(errors: list[str]) -> None:
    if errors:
        console.print("[bold red]Validation failed[/bold red]")
        for error in errors:
            console.print(f"- {error}")
        raise typer.Exit(1)
    console.print("[bold green]OK[/bold green]")
