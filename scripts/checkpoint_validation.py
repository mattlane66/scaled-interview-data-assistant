"""Schema and referential-integrity validation for synthesis checkpoints."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "checkpoint.schema.json"
ID_PATTERNS = {
    "source_id": re.compile(r"^SRC\d{2,}$"),
    "interview": re.compile(r"^I\d{2,}$"),
    "episode": re.compile(r"^D\d{2,}$"),
    "segment": re.compile(r"^S\d{2,}$"),
    "evidence": re.compile(r"^E\d{3,}$"),
    "code": re.compile(r"^[AB]\d{2,}$"),
    "link": re.compile(r"^L\d{3,}$"),
    "cluster": re.compile(r"^C\d{2,}$"),
}


class CheckpointValidationError(ValueError):
    pass


def _tokens(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in re.split(r"[,;/\n]+", str(value)) if part.strip()]


def migrate_version_1(data: dict[str, Any]) -> dict[str, Any]:
    """Fill additive v1.1 fields without pretending old coverage or evidence types are known."""
    migrated = copy.deepcopy(data)
    evidence = migrated.setdefault("evidence_bank", [])
    sources = migrated.setdefault("source_index", [])
    if not sources:
        source_ids: dict[str, str] = {}
        for row in evidence:
            source = str(row.get("source", "")).strip()
            if source and source not in source_ids:
                source_id = f"SRC{len(source_ids) + 1:02d}"
                source_ids[source] = source_id
                sources.append(
                    {
                        "source_id": source_id,
                        "source": source,
                        "coverage": "UNKNOWN",
                        "notes": "Migrated from a pre-1.1 checkpoint.",
                    }
                )
            row.setdefault("source_id", source_ids.get(source, "SRC00"))
            row.setdefault("speaker", "UNKNOWN")
            row.setdefault("evidence_type", "unknown")
    migrated.setdefault("a_to_b_links", [])
    clusters = migrated.setdefault("clusters", [])
    computation = migrated.setdefault("computation", {})
    computation.setdefault("a_to_b_association", "unknown")
    computation.setdefault("clustering_method", "unknown")
    computation.setdefault(
        "cluster_count", len({row.get("cluster") for row in clusters})
    )
    migrated.setdefault("decision_log", "")
    migrated.setdefault("latest_diff_log", "")
    return migrated


def _unique_ids(
    rows: list[dict[str, Any]], field: str, pattern: str, errors: list[str]
) -> set[str]:
    values: set[str] = set()
    regex = ID_PATTERNS[pattern]
    for row in rows:
        value = str(row.get(field, "")).strip()
        if not regex.fullmatch(value):
            errors.append(f"Malformed {field}: {value or '<missing>'}")
        if value in values:
            errors.append(f"Duplicate {field}: {value}")
        values.add(value)
    return values


def _validate_relations(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sources = data["source_index"]
    interviews = data["interview_index"]
    episodes = data["episode_index"]
    segments = data["segment_index"]
    evidence = data["evidence_bank"]
    codebook = data["codebook"]
    mappings = data["evidence_to_code_mappings"]
    links = data["a_to_b_links"]
    clusters = data["clusters"]

    source_ids = _unique_ids(sources, "source_id", "source_id", errors)
    interview_ids = _unique_ids(interviews, "interview", "interview", errors)
    episode_ids = _unique_ids(episodes, "episode", "episode", errors)
    evidence_ids = _unique_ids(evidence, "evidence", "evidence", errors)
    code_ids = _unique_ids(codebook, "code", "code", errors)
    _unique_ids(links, "link", "link", errors)

    source_by_id: dict[str, str] = {}
    source_paths: set[str] = set()
    for row in sources:
        source_id = str(row["source_id"])
        source = str(row["source"])
        if source in source_paths:
            errors.append(f"Duplicate source path: {source}")
        source_paths.add(source)
        source_by_id[source_id] = source

    episode_owner: dict[str, str] = {}
    for row in episodes:
        episode = str(row["episode"])
        interview = str(row["interview"])
        if interview not in interview_ids:
            errors.append(f"Episode {episode} references unknown interview {interview}")
        episode_owner[episode] = interview

    segment_keys: set[tuple[str, str]] = set()
    for row in segments:
        interview = str(row.get("interview", ""))
        segment = str(row.get("segment", ""))
        if interview not in interview_ids:
            errors.append(f"Segment {segment} references unknown interview {interview}")
        if not ID_PATTERNS["segment"].fullmatch(segment):
            errors.append(f"Malformed segment: {segment}")
        key = (interview, segment)
        if key in segment_keys:
            errors.append(f"Duplicate segment: {interview}/{segment}")
        segment_keys.add(key)

    evidence_owner: dict[str, tuple[str, str]] = {}
    for row in evidence:
        evidence_id = str(row["evidence"])
        source_id = str(row["source_id"])
        interview = str(row["interview"])
        episode = str(row["episode"])
        segment = str(row["segment"])
        if source_id not in source_ids:
            errors.append(f"{evidence_id} references unknown source {source_id}")
        elif str(row["source"]) != source_by_id[source_id]:
            errors.append(f"{evidence_id} source path does not match {source_id}")
        if interview not in interview_ids:
            errors.append(f"{evidence_id} references unknown interview {interview}")
        if episode not in episode_ids:
            errors.append(f"{evidence_id} references unknown episode {episode}")
        elif episode_owner.get(episode) != interview:
            errors.append(f"{evidence_id} episode belongs to another interview")
        if segment_keys and (interview, segment) not in segment_keys:
            errors.append(f"{evidence_id} references unknown segment {interview}/{segment}")
        evidence_owner[evidence_id] = (interview, episode)

    mapped: set[str] = set()
    episode_codes: dict[str, set[str]] = {}
    for row in mappings:
        evidence_id = str(row["evidence"])
        owner = (str(row["interview"]), str(row["episode"]))
        if evidence_id in mapped:
            errors.append(f"Duplicate evidence mapping: {evidence_id}")
        mapped.add(evidence_id)
        if evidence_id not in evidence_ids:
            errors.append(f"Mapping references unknown evidence {evidence_id}")
        elif evidence_owner[evidence_id] != owner:
            errors.append(f"Mapping owner mismatch for {evidence_id}")
        for field, prefix in (("a_codes", "A"), ("b_codes", "B")):
            for code in _tokens(row.get(field)):
                if not code.startswith(prefix) or code not in code_ids:
                    errors.append(f"Mapping references invalid {prefix}-code {code}")
                else:
                    episode_codes.setdefault(owner[1], set()).add(code)

    for evidence_id in sorted(evidence_ids - mapped):
        errors.append(f"Evidence has no mapping row: {evidence_id}")

    link_pairs: set[tuple[str, str, str]] = set()
    for row in links:
        link = str(row["link"])
        episode = str(row["episode"])
        a_code = str(row["a_code"])
        b_code = str(row["b_code"])
        if episode not in episode_ids:
            errors.append(f"{link} references unknown episode {episode}")
        if a_code not in code_ids or not a_code.startswith("A"):
            errors.append(f"{link} references invalid A-code {a_code}")
        if b_code not in code_ids or not b_code.startswith("B"):
            errors.append(f"{link} references invalid B-code {b_code}")
        pair = (episode, a_code, b_code)
        if pair in link_pairs:
            errors.append(f"Duplicate episode A-to-B link: {episode}/{a_code}/{b_code}")
        link_pairs.add(pair)
        if a_code not in episode_codes.get(episode, set()):
            errors.append(f"{link} A-code {a_code} is not mapped in episode {episode}")
        if b_code not in episode_codes.get(episode, set()):
            errors.append(f"{link} B-code {b_code} is not mapped in episode {episode}")
        link_evidence = _tokens(row.get("evidence"))
        if not link_evidence:
            errors.append(f"{link} has no supporting evidence")
        for evidence_id in link_evidence:
            if evidence_id not in evidence_ids:
                errors.append(f"{link} references unknown evidence {evidence_id}")
            elif evidence_owner[evidence_id][1] != episode:
                errors.append(f"{link} evidence {evidence_id} belongs to another episode")

    unit_field = data["analysis_unit"]
    expected_units = episode_ids if unit_field == "episode" else interview_ids
    assigned: set[str] = set()
    for row in clusters:
        unit = str(row.get(unit_field, ""))
        cluster = str(row.get("cluster", ""))
        if unit not in expected_units:
            errors.append(f"Cluster assignment references unknown {unit_field} {unit}")
        if unit in assigned:
            errors.append(f"Duplicate cluster assignment for {unit_field} {unit}")
        assigned.add(unit)
        if not ID_PATTERNS["cluster"].fullmatch(cluster):
            errors.append(f"Malformed cluster: {cluster}")
    if clusters and assigned != expected_units:
        for unit in sorted(expected_units - assigned):
            errors.append(f"Missing cluster assignment for {unit_field} {unit}")

    actual_cluster_count = len({str(row.get("cluster", "")) for row in clusters})
    recorded_cluster_count = data["computation"].get("cluster_count")
    if recorded_cluster_count != actual_cluster_count:
        errors.append(
            "Checkpoint cluster_count does not match distinct assignments: "
            f"{recorded_cluster_count} != {actual_cluster_count}"
        )

    aliases: dict[str, str] = {}
    active_clusters = {str(row.get("cluster", "")) for row in clusters}
    for row in data["alias_map"]:
        alias = str(row.get("alias", ""))
        canonical = str(row.get("canonical", ""))
        if alias in aliases:
            errors.append(f"Duplicate alias: {alias}")
        aliases[alias] = canonical
        if alias == canonical:
            errors.append(f"Self-referential alias: {alias}")
        if alias[:1] != canonical[:1]:
            errors.append(f"Alias changes ID family: {alias} -> {canonical}")
        if canonical.startswith(("A", "B")) and canonical not in code_ids:
            errors.append(f"Alias canonical code is not active: {canonical}")
        if canonical.startswith("C") and active_clusters and canonical not in active_clusters:
            errors.append(f"Alias canonical cluster is not active: {canonical}")
    for start in aliases:
        seen: set[str] = set()
        current = start
        while current in aliases:
            if current in seen:
                errors.append(f"Alias cycle detected from {start}")
                break
            seen.add(current)
            current = aliases[current]
    return errors


def validate_checkpoint_document(data: object) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise CheckpointValidationError("Checkpoint must be a JSON object.")
    version = str(data.get("checkpoint_version", ""))
    if not version.startswith("1."):
        raise CheckpointValidationError(f"Unsupported checkpoint version: {version or 'missing'}")

    migrated = migrate_version_1(data)
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = sorted(validator.iter_errors(migrated), key=lambda error: list(error.path))
    messages = [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in schema_errors
    ]
    messages.extend(_validate_relations(migrated))
    if messages:
        raise CheckpointValidationError("\n".join(f"- {message}" for message in messages))
    return migrated
