"""Stateless, bounded adapters over the existing research code.

No model calls, network fetches, source persistence, arbitrary paths, or approval
side effects. Raw transcripts are input data, never instructions.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from simulation.core import load_checkpoint
from simulation.counterfactual import build_brief
from simulation.mechanism_map import (
    compile_map,
    inventory,
    make_study,
    planning_handoff,
    render_map,
)

ROOT = Path(__file__).resolve().parents[1]
MAX_REQUEST_BYTES = 2_000_000
MAX_SOURCE_BYTES = 350_000
MAX_SOURCES = 20
MAX_RESULT_BYTES = 1_000_000
SOURCE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\.(?:txt|md)$")
REQUIRED = (
    "sources", "interviews", "episodes", "segments", "evidence_bank",
    "codebook", "evidence_mappings", "links",
)
FILES = {
    "sources": "sources.json",
    "interviews": "interviews.json",
    "episodes": "episodes.json",
    "segments": "segments.json",
    "evidence_bank": "evidence_bank.json",
    "codebook": "codebook.json",
    "evidence_mappings": "evidence_mappings.json",
    "links": "links.json",
}


def _bounded_json(value: object) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ValueError("Input must be valid finite JSON") from exc
    if len(encoded.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ValueError("Request exceeds the 2 MB processing limit")
    return encoded


def _bounded_result(value: dict[str, Any]) -> dict[str, Any]:
    if len(_bounded_json(value).encode("utf-8")) > MAX_RESULT_BYTES:
        raise ValueError("Result too large to return; narrow the study")
    return value


def _checkpoint(checkpoint_json: str, folder: Path) -> tuple[dict, str]:
    if not isinstance(checkpoint_json, str):
        raise ValueError("checkpoint_json must be an unmodified JSON string")
    if len(checkpoint_json.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ValueError("Checkpoint exceeds 2 MB")
    path = folder / "CHECKPOINT.json"
    path.write_text(checkpoint_json, encoding="utf-8")
    return load_checkpoint(path)


def checkpoint_summary(checkpoint_json: str) -> dict[str, Any]:
    """Validate a checkpoint; report only counts, coverage, and its exact file hash."""
    with tempfile.TemporaryDirectory(prefix="sida-check-") as temp:
        checkpoint, digest = _checkpoint(checkpoint_json, Path(temp))
        return {
            "valid": True,
            "checkpoint_sha256": digest,
            "interviews": len(checkpoint["interview_index"]),
            "decision_episodes": len(checkpoint["episode_index"]),
            "evidence_rows": len(checkpoint["evidence_bank"]),
            "a_to_b_links": len(checkpoint["a_to_b_links"]),
            "clusters": len(checkpoint["clusters"]),
            "analysis_unit": checkpoint["analysis_unit"],
            "caveat": "Schema validity does not establish source or interpretation quality.",
        }


def draft_mechanism_study(checkpoint_json: str, scope: dict) -> dict[str, Any]:
    """Create an UNAPPROVED mechanism study over explicit episodes or a cluster."""
    _bounded_json(scope)
    with tempfile.TemporaryDirectory(prefix="sida-draft-") as temp:
        checkpoint, digest = _checkpoint(checkpoint_json, Path(temp))
        study = make_study(checkpoint, digest, scope)
        return _bounded_result({"status": "UNREVIEWED_DRAFT", "study": study})


def inspect_mechanism_study(
    checkpoint_json: str, study: dict
) -> dict[str, Any]:
    """Inventory real cases and evidence coverage; never include raw excerpts."""
    _bounded_json(study)
    with tempfile.TemporaryDirectory(prefix="sida-inventory-") as temp:
        checkpoint, digest = _checkpoint(checkpoint_json, Path(temp))
        result = inventory(checkpoint, digest, study)
        return _bounded_result({
            "status": result["review_status"],
            "study_id": result["study_id"],
            "distinct_interviews": result["distinct_interviews"],
            "episodes": [{
                "episode": row["episode"],
                "interview": row["interview"],
                "source_coverage": row["source_coverage"],
                "evidence_refs": row["evidence_refs"],
                "links": [link["link"] for link in row["a_to_b_links"]],
            } for row in result["episodes"]],
            "limitations": result["limitations"],
        })


def compile_reviewed_mechanism_study(
    checkpoint_json: str, study: dict, *, include_report: bool = False
) -> dict[str, Any]:
    """Compile a human-ATTESTED study; never silently turn claims into facts."""
    _bounded_json(study)
    with tempfile.TemporaryDirectory(prefix="sida-map-") as temp:
        checkpoint, digest = _checkpoint(checkpoint_json, Path(temp))
        mapped = compile_map(checkpoint, digest, study)
        handoff = planning_handoff(mapped)
        result = {
            "status": mapped["status"],
            "review_attestation": mapped["reviewer_attestation"],
            "map": mapped,
            "planning_handoff": handoff,
            "warning": (
                "Reviewer attestation is self-reported, NOT independently verified. "
                "The handoff is PROPOSED, not accepted y, requirements, or a shape."
            ),
        }
        if include_report:
            result["report_markdown"] = render_map(mapped)
        return _bounded_result(result)


def reviewed_counterfactual_brief(
    checkpoint_json: str, scenario: dict
) -> dict[str, Any]:
    """Evidence-first design hypothesis (no simulation run or approval bypass)."""
    _bounded_json(scenario)
    with tempfile.TemporaryDirectory(prefix="sida-cf-") as temp:
        checkpoint, digest = _checkpoint(checkpoint_json, Path(temp))
        brief = build_brief(checkpoint, digest, scenario)
        return _bounded_result(brief)


def run_study_pipeline(
    bundle: dict[str, Any], *,
    clusters: str = "none", include_checkpoint: bool = False
) -> dict[str, Any]:
    """Run the exact deterministic CLI in an isolated temporary study directory.

    Source files are explicit inline text; all paths are server-generated.
    Never supply an arbitrary filesystem path or a URL for the server to read.
    """
    _bounded_json(bundle)
    if not isinstance(bundle, dict):
        raise ValueError("Expected a JSON object containing study registries")
    if any(name not in bundle or not isinstance(bundle[name], list) for name in REQUIRED):
        raise ValueError("Missing or invalid source/interview/episode/evidence registries")
    if any(len(bundle[name]) > 2500 for name in REQUIRED):
        raise ValueError("Study exceeds maximum of 2500 rows per registry")
    source_files = bundle.get("source_files")
    if not isinstance(source_files, dict) or not source_files:
        raise ValueError("source_files must map source filenames to full text")
    if len(source_files) > MAX_SOURCES:
        raise ValueError("Too many transcript source files")
    for name, content in source_files.items():
        if (not isinstance(name, str) or not SOURCE_NAME.fullmatch(name)
                or name in {".", ".."} or not isinstance(content, str)):
            raise ValueError("Source file names must be safe .txt or .md basenames")
        if len(content.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError("Source text exceeds per-file limit")
    if not isinstance(clusters, str) or not (
        clusters in {"none", "auto"}
        or (re.fullmatch(r"[1-9][0-9]?", clusters) and int(clusters) <= 20)
    ):
        raise ValueError("clusters must be none, auto, or an integer 1–20")
    # The validator reads filenames from the source registry as well as from
    # source_files. Check both fields before spawning any subprocess so an
    # adversarial registry can never request a file outside our temp root.
    declared_sources = set()
    for source in bundle["sources"]:
        if not isinstance(source, dict):
            raise ValueError("Every source registry row must be an object")
        name = source.get("source")
        if not isinstance(name, str) or name not in source_files:
            raise ValueError("Source registry must reference only supplied safe filenames")
        declared_sources.add(name)
    if declared_sources != set(source_files):
        raise ValueError("Every uploaded source must be registered exactly once")
    for row in bundle["evidence_bank"]:
        if not isinstance(row, dict) or row.get("source") not in declared_sources:
            raise ValueError("Evidence may reference only supplied registered sources")
    report = bundle.get("report")
    if report is not None and (not isinstance(report, str) or len(report) > 200_000):
        raise ValueError("report must be an optional bounded Markdown string")

    with tempfile.TemporaryDirectory(prefix="sida-pipeline-") as temp:
        folder = Path(temp)
        data = folder / "source"
        output = folder / "out"
        data.mkdir()
        for name, contents in source_files.items():
            (data / name).write_text(contents, encoding="utf-8")
        for key, filename in FILES.items():
            (data / filename).write_text(_bounded_json(bundle[key]), encoding="utf-8")
        cmd = [
            sys.executable, str(ROOT / "scripts" / "run_pipeline.py"),
            "--sources", str(data / FILES["sources"]),
            "--interviews", str(data / FILES["interviews"]),
            "--episodes", str(data / FILES["episodes"]),
            "--segments", str(data / FILES["segments"]),
            "--evidence", str(data / FILES["evidence_bank"]),
            "--codebook", str(data / FILES["codebook"]),
            "--mappings", str(data / FILES["evidence_mappings"]),
            "--links", str(data / FILES["links"]),
            "--source-root", str(data),
            "--clusters", clusters,
            "--output-dir", str(output),
        ]
        if report is not None:
            (data / "synthesis_report.md").write_text(report, encoding="utf-8")
            cmd += ["--report", str(data / "synthesis_report.md")]
        # Do not pass platform credentials or customer tokens into subprocesses.
        safe_env = {
            k: v for k, v in os.environ.items()
            if k in {"PATH", "LANG", "LC_ALL", "SYSTEMROOT", "HOME", "TMPDIR"}
        }
        try:
            completed = subprocess.run(
                cmd, cwd=ROOT, env=safe_env, capture_output=True, text=True,
                timeout=90, check=False,
            )
        except subprocess.TimeoutExpired:
            return {"valid": False, "error_code": "PROCESSING_TIMEOUT"}
        if completed.returncode:
            # Do NOT return unfiltered subprocess stderr: it may echo transcripts.
            return {
                "valid": False,
                "error_code": "STUDY_VALIDATION_FAILED",
                "guidance": (
                    "Check registry references, source-located verbatim excerpts "
                    "and report citations locally. No source data has been retained."
                ),
            }
        path = output / "CHECKPOINT.json"
        raw = path.read_text(encoding="utf-8")
        summary = checkpoint_summary(raw)
        summary["source_verification"] = "EXCERPTS_CHECKED_AGAINST_SUPPLIED_SOURCE_TEXT"
        summary["interpretation_review"] = "HUMAN_REVIEW_NOT_VERIFIED_BY_THIS_TOOL"
        if include_checkpoint:
            summary["checkpoint_json"] = raw
        return _bounded_result(summary)
