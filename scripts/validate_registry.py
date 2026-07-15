"""Validate the registries and structured artifacts used by the synthesis pipeline."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd
import typer
from common import (
    console,
    fail_if_errors,
    normalize_column_names,
    read_table,
    require_columns,
    split_tokens,
    validate_id,
)

app = typer.Typer(add_completion=False)

EVIDENCE_TYPES = {
    "concrete_event_or_behavior",
    "current_state",
    "observation",
    "interpretation",
    "aspiration",
    "generalization",
    "hypothetical",
    "interviewer_statement",
    "unknown",
}


def _first_present(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((column for column in candidates if column in df.columns), None)


def _nonempty(value: object) -> bool:
    return not pd.isna(value) and bool(str(value).strip())


def _normalized_source_text(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _id_kind(value: str) -> str | None:
    for kind in ("a_code", "b_code", "cluster"):
        if validate_id(value, kind):
            return kind
    return None


def _validate_registry_ids(
    frame: pd.DataFrame,
    column: str,
    kind: str,
    source: Path,
    errors: list[str],
) -> set[str]:
    require_columns(frame, [column], source)
    values = frame[column].astype(str).str.strip()
    for value in values:
        if not validate_id(value, kind):
            errors.append(f"Bad {kind} ID in {source}: {value}")
    duplicates = values[values.duplicated()].unique()
    errors.extend(f"Duplicate {kind} ID in {source}: {value}" for value in duplicates)
    return set(values)


@app.command()
def main(
    evidence: Path = typer.Option(..., "--evidence", "-e", help="Evidence bank."),
    codebook: Path = typer.Option(..., "--codebook", "-c", help="A/B codebook."),
    mappings: Path = typer.Option(..., "--mappings", "-m", help="Evidence-to-code map."),
    sources: Path | None = typer.Option(None, "--sources", help="Source coverage registry."),
    links: Path | None = typer.Option(None, "--links", help="Explicit A-to-B link registry."),
    source_root: Path | None = typer.Option(
        None,
        "--source-root",
        help="Optional root used to verify excerpts against local source files.",
    ),
    interviews: Path | None = typer.Option(None, "--interviews", help="Interview registry."),
    episodes: Path | None = typer.Option(None, "--episodes", help="Decision-episode registry."),
    segments: Path | None = typer.Option(None, "--segments", help="Segment registry."),
    clusters: Path | None = typer.Option(None, "--clusters", help="Cluster assignments."),
    unit_column: str = typer.Option(
        "episode", "--unit-column", help="Cluster assignment unit: episode or interview."
    ),
    aliases: Path | None = typer.Option(None, "--aliases", "-a", help="Alias map."),
    allow_unmapped: bool = typer.Option(
        False,
        "--allow-unmapped",
        help="Allow evidence rows that have not yet been coded.",
    ),
) -> None:
    """Fail when IDs, references, code families, or required provenance are inconsistent."""
    errors: list[str] = []

    if unit_column not in {"episode", "interview"}:
        raise typer.BadParameter("--unit-column must be episode or interview")

    source_ids: set[str] = set()
    source_paths: dict[str, str] = {}
    if sources:
        source_df = normalize_column_names(read_table(sources))
        require_columns(source_df, ["source_id", "source", "coverage"], sources)
        source_ids = _validate_registry_ids(
            source_df, "source_id", "source", sources, errors
        )
        seen_paths: set[str] = set()
        for _, row in source_df.iterrows():
            source_id = str(row["source_id"]).strip()
            source = str(row["source"]).strip()
            coverage = str(row["coverage"]).strip().upper()
            if not source:
                errors.append(f"{source_id} has an empty source")
            if source in seen_paths:
                errors.append(f"Duplicate source path in {sources}: {source}")
            seen_paths.add(source)
            if coverage not in {"FULL", "PARTIAL", "UNREADABLE", "UNKNOWN"}:
                errors.append(f"Bad coverage for {source_id}: {coverage}")
            source_paths[source_id] = source

    interview_ids: set[str] = set()
    if interviews:
        interview_df = normalize_column_names(read_table(interviews))
        interview_ids = _validate_registry_ids(
            interview_df, "interview", "interview", interviews, errors
        )

    episode_ids: set[str] = set()
    episode_owner: dict[str, str] = {}
    if episodes:
        episode_df = normalize_column_names(read_table(episodes))
        require_columns(episode_df, ["episode", "interview"], episodes)
        episode_ids = _validate_registry_ids(episode_df, "episode", "episode", episodes, errors)
        for _, row in episode_df.iterrows():
            episode = str(row["episode"]).strip()
            interview = str(row["interview"]).strip()
            if not validate_id(interview, "interview"):
                errors.append(f"Bad interview ID in {episodes}: {interview}")
            if interview_ids and interview not in interview_ids:
                errors.append(f"Episode {episode} references unknown interview: {interview}")
            episode_owner[episode] = interview

    segment_keys: set[tuple[str, str]] = set()
    if segments:
        segment_df = normalize_column_names(read_table(segments))
        require_columns(segment_df, ["interview", "segment"], segments)
        for _, row in segment_df.iterrows():
            interview = str(row["interview"]).strip()
            segment = str(row["segment"]).strip()
            if not validate_id(interview, "interview"):
                errors.append(f"Bad interview ID in {segments}: {interview}")
            if not validate_id(segment, "segment"):
                errors.append(f"Bad segment ID in {segments}: {segment}")
            key = (interview, segment)
            if key in segment_keys:
                errors.append(f"Duplicate segment in {segments}: {interview}/{segment}")
            segment_keys.add(key)

    evidence_df = normalize_column_names(read_table(evidence))
    evidence_columns = [
        "evidence",
        "source_id",
        "interview",
        "episode",
        "segment",
        "source",
        "source_location",
        "speaker",
        "evidence_type",
        "verbatim_excerpt",
    ]
    require_columns(evidence_df, evidence_columns, evidence)

    evidence_ids: set[str] = set()
    evidence_owner: dict[str, tuple[str, str]] = {}
    for _, row in evidence_df.iterrows():
        evidence_id = str(row["evidence"]).strip()
        source_id = str(row["source_id"]).strip()
        interview = str(row["interview"]).strip()
        episode = str(row["episode"]).strip()
        segment = str(row["segment"]).strip()

        if not validate_id(evidence_id, "evidence"):
            errors.append(f"Bad evidence ID in {evidence}: {evidence_id}")
        if evidence_id in evidence_ids:
            errors.append(f"Duplicate evidence ID in {evidence}: {evidence_id}")
        evidence_ids.add(evidence_id)

        if not validate_id(source_id, "source"):
            errors.append(f"Bad source ID for {evidence_id}: {source_id}")
        if source_ids and source_id not in source_ids:
            errors.append(f"{evidence_id} references unknown source: {source_id}")
        if source_paths and source_paths.get(source_id) != str(row["source"]).strip():
            errors.append(f"{evidence_id} source path does not match {source_id}")

        if not validate_id(interview, "interview"):
            errors.append(f"Bad interview ID for {evidence_id}: {interview}")
        if not validate_id(episode, "episode"):
            errors.append(f"Bad episode ID for {evidence_id}: {episode}")
        if not validate_id(segment, "segment"):
            errors.append(f"Bad segment ID for {evidence_id}: {segment}")
        if interview_ids and interview not in interview_ids:
            errors.append(f"{evidence_id} references unknown interview: {interview}")
        if episode_ids and episode not in episode_ids:
            errors.append(f"{evidence_id} references unknown episode: {episode}")
        if episode_owner and episode_owner.get(episode) != interview:
            errors.append(f"{evidence_id} episode {episode} belongs to another interview")
        if segment_keys and (interview, segment) not in segment_keys:
            errors.append(f"{evidence_id} references unknown segment: {interview}/{segment}")
        for column in ("source", "source_location", "speaker", "verbatim_excerpt"):
            if not _nonempty(row[column]):
                errors.append(f"{evidence_id} has an empty {column}")
        evidence_type = str(row["evidence_type"]).strip().lower()
        if evidence_type not in EVIDENCE_TYPES:
            errors.append(f"{evidence_id} has an invalid evidence_type: {evidence_type}")
        if source_root and _nonempty(row["source"]) and _nonempty(row["verbatim_excerpt"]):
            root = source_root.resolve()
            source_path = (root / str(row["source"])).resolve()
            if not source_path.is_relative_to(root):
                errors.append(f"{evidence_id} source escapes --source-root")
            elif not source_path.is_file():
                errors.append(f"{evidence_id} source file does not exist: {row['source']}")
            else:
                source_text = _normalized_source_text(source_path.read_text())
                excerpt = _normalized_source_text(row["verbatim_excerpt"])
                if excerpt not in source_text:
                    errors.append(f"{evidence_id} excerpt was not found in {row['source']}")
        evidence_owner[evidence_id] = (interview, episode)

    codebook_df = normalize_column_names(read_table(codebook))
    require_columns(codebook_df, ["code", "definition"], codebook)
    code_ids: set[str] = set()
    for _, row in codebook_df.iterrows():
        code = str(row["code"]).strip()
        kind = _id_kind(code)
        if kind not in {"a_code", "b_code"}:
            errors.append(f"Bad A/B code ID in {codebook}: {code}")
        if code in code_ids:
            errors.append(f"Duplicate code in {codebook}: {code}")
        code_ids.add(code)
        if not _nonempty(row["definition"]):
            errors.append(f"Code {code} has an empty definition")
        if "family" in codebook_df.columns and _nonempty(row.get("family")):
            expected = "A" if kind == "a_code" else "B"
            if str(row["family"]).strip().upper() != expected:
                errors.append(f"Code {code} has the wrong family value")

    mapping_df = normalize_column_names(read_table(mappings))
    require_columns(
        mapping_df,
        ["evidence", "interview", "episode", "a_codes", "b_codes"],
        mappings,
    )
    mapped_evidence: set[str] = set()
    for _, row in mapping_df.iterrows():
        evidence_id = str(row["evidence"]).strip()
        interview = str(row["interview"]).strip()
        episode = str(row["episode"]).strip()
        if evidence_id in mapped_evidence:
            errors.append(f"Duplicate mapping row for evidence: {evidence_id}")
        mapped_evidence.add(evidence_id)
        if evidence_id not in evidence_ids:
            errors.append(f"Mapping references missing evidence ID: {evidence_id}")
        elif evidence_owner[evidence_id] != (interview, episode):
            errors.append(
                f"Mapping owner mismatch for {evidence_id}: expected "
                f"{evidence_owner[evidence_id][0]}/{evidence_owner[evidence_id][1]}"
            )

        for column, kind, family in (
            ("a_codes", "a_code", "A"),
            ("b_codes", "b_code", "B"),
        ):
            for code in split_tokens(row[column]):
                if not validate_id(code, kind):
                    other_kind = "b_code" if kind == "a_code" else "a_code"
                    if validate_id(code, other_kind):
                        errors.append(f"Code {code} is in the wrong {family}-code column")
                    else:
                        errors.append(f"Bad {family}-code in {mappings}: {code}")
                elif code not in code_ids:
                    errors.append(f"Mapping references missing codebook code: {code}")

    if not allow_unmapped:
        for evidence_id in sorted(evidence_ids - mapped_evidence):
            errors.append(f"Evidence has no mapping row: {evidence_id}")

    if links:
        link_df = normalize_column_names(read_table(links))
        require_columns(
            link_df,
            ["link", "episode", "a_code", "b_code", "basis", "evidence", "rationale"],
            links,
        )
        link_ids: set[str] = set()
        link_pairs: set[tuple[str, str, str]] = set()
        for _, row in link_df.iterrows():
            link_id = str(row["link"]).strip()
            episode = str(row["episode"]).strip()
            a_code = str(row["a_code"]).strip()
            b_code = str(row["b_code"]).strip()
            basis = str(row["basis"]).strip().upper()
            if not validate_id(link_id, "link"):
                errors.append(f"Bad link ID in {links}: {link_id}")
            if link_id in link_ids:
                errors.append(f"Duplicate link ID in {links}: {link_id}")
            link_ids.add(link_id)
            if not validate_id(episode, "episode") or (episode_ids and episode not in episode_ids):
                errors.append(f"{link_id} references unknown episode: {episode}")
            if not validate_id(a_code, "a_code") or a_code not in code_ids:
                errors.append(f"{link_id} references unknown A-code: {a_code}")
            if not validate_id(b_code, "b_code") or b_code not in code_ids:
                errors.append(f"{link_id} references unknown B-code: {b_code}")
            if basis not in {"EXPLICIT", "INFERRED"}:
                errors.append(f"{link_id} has invalid basis: {basis}")
            pair = (episode, a_code, b_code)
            if pair in link_pairs:
                errors.append(
                    f"Duplicate episode A-to-B link in {links}: "
                    f"{episode}/{a_code}/{b_code}"
                )
            link_pairs.add(pair)
            if not _nonempty(row["rationale"]):
                errors.append(f"{link_id} has an empty rationale")
            for evidence_id in split_tokens(row["evidence"]):
                if evidence_id not in evidence_ids:
                    errors.append(f"{link_id} references missing evidence: {evidence_id}")
                elif evidence_owner[evidence_id][1] != episode:
                    errors.append(f"{link_id} evidence {evidence_id} belongs to another episode")

    cluster_ids: set[str] = set()
    if clusters:
        cluster_df = normalize_column_names(read_table(clusters))
        cluster_column = _first_present(cluster_df, ["cluster", "cluster_id"])
        if cluster_column is None:
            errors.append(f"{clusters} is missing cluster column")
        else:
            if unit_column not in cluster_df.columns:
                errors.append(f"{clusters} is missing {unit_column} column")
            else:
                units = cluster_df[unit_column].astype(str).str.strip()
                expected_units = episode_ids if unit_column == "episode" else interview_ids
                expected_kind = unit_column
                duplicates = units[units.duplicated()].unique()
                errors.extend(
                    f"Duplicate {unit_column} cluster assignment: {value}"
                    for value in duplicates
                )
                for unit in units:
                    if not validate_id(unit, expected_kind):
                        errors.append(f"Bad {unit_column} ID in {clusters}: {unit}")
                    elif expected_units and unit not in expected_units:
                        errors.append(
                            f"Cluster assignment references unknown {unit_column}: {unit}"
                        )
                if expected_units:
                    missing = sorted(expected_units - set(units))
                    errors.extend(
                        f"Missing cluster assignment for {unit_column}: {unit}" for unit in missing
                    )
            for cluster in cluster_df[cluster_column].astype(str).str.strip():
                if not validate_id(cluster, "cluster"):
                    errors.append(f"Bad cluster ID in {clusters}: {cluster}")
                cluster_ids.add(cluster)

    if aliases:
        alias_df = normalize_column_names(read_table(aliases))
        require_columns(alias_df, ["alias", "canonical"], aliases)
        alias_map: dict[str, str] = {}
        for _, row in alias_df.iterrows():
            alias = str(row["alias"]).strip()
            canonical = str(row["canonical"]).strip()
            alias_kind = _id_kind(alias)
            canonical_kind = _id_kind(canonical)
            if alias_kind is None or canonical_kind is None:
                errors.append(f"Bad alias mapping: {alias} -> {canonical}")
                continue
            if alias_kind != canonical_kind:
                errors.append(f"Alias changes ID family: {alias} -> {canonical}")
            if alias == canonical:
                errors.append(f"Self-referential alias: {alias}")
            if alias in alias_map:
                errors.append(f"Duplicate alias row: {alias}")
            alias_map[alias] = canonical
            if canonical_kind in {"a_code", "b_code"} and canonical not in code_ids:
                errors.append(f"Alias canonical code is not active: {canonical}")
            if canonical_kind == "cluster" and cluster_ids and canonical not in cluster_ids:
                errors.append(f"Alias canonical cluster is not active: {canonical}")

        for start in alias_map:
            seen: set[str] = set()
            current = start
            while current in alias_map:
                if current in seen:
                    errors.append(f"Alias cycle detected from: {start}")
                    break
                seen.add(current)
                current = alias_map[current]

    fail_if_errors(errors)
    console.print("Registry files are internally consistent.")


if __name__ == "__main__":
    app()
