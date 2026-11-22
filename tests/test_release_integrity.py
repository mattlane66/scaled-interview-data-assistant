"""Release consistency: docs references, schemas, plugin identity, and safe source paths."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import unquote

import pytest
from jsonschema import Draft202012Validator

from plugin_runtime.operations import run_study_pipeline
from scripts.build_plugin import validated_package

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "canonical-mattress"


def test_all_relative_markdown_file_references_exist():
    """Check cross-file links, including plugin onboarding and method handoffs."""
    missing = []
    link = re.compile(r"\]\(([^)\n]+)\)")
    for source in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv", "dist", "build"} for part in source.parts):
            continue
        raw = source.read_text(encoding="utf-8")
        for match in link.finditer(raw):
            candidate = match.group(1).strip()
            if candidate.startswith("<") and candidate.endswith(">"):
                candidate = candidate[1:-1]
            candidate = candidate.split("#", 1)[0].split("?", 1)[0]
            if not candidate or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", candidate):
                continue
            # Local Markdown links may target a file or directory. Never read
            # the target data: we only check that the reference resolves.
            relative = unquote(candidate)
            if not (source.parent / relative).exists():
                missing.append((source.relative_to(ROOT).as_posix(), relative))
    assert not missing, f"Broken local document references: {missing}"


def test_every_json_schema_is_a_valid_draft_2020_12_schema():
    schemas = list((ROOT / "schemas").glob("*.schema.json"))
    schemas += list((ROOT / "simulation" / "schemas").glob("*.schema.json"))
    assert len(schemas) >= 12
    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_plugin_manifest_matches_repo_release_and_onboarding():
    manifest, files = validated_package()
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match and match.group(1) == manifest["version"]
    assert manifest["extensions"]["com.openai"]["onboardingSkill"] == (
        "./skills/get-started/SKILL.md"
    )
    assert len(files) == 5


def test_source_text_cannot_be_overwritten_by_generated_synthesis_report():
    names = (
        "sources", "interviews", "episodes", "segments", "evidence_bank",
        "codebook", "evidence_mappings", "links",
    )
    bundle = {
        name: json.loads((CASE / f"{name}.json").read_text(encoding="utf-8"))
        for name in names
    }
    bundle["source_files"] = {
        "synthesis_report.md": "distinct participant source, never overwritable"
    }
    # Replace references to the renamed source to get past normal path checks.
    for row in bundle["sources"]:
        row["source"] = "synthesis_report.md"
    for row in bundle["evidence_bank"]:
        row["source"] = "synthesis_report.md"
    bundle["report"] = "This is an unrelated computed report, not a transcript."
    with pytest.raises(ValueError, match="reserved|overwritten"):
        run_study_pipeline(bundle)


def test_canonical_link_registry_is_not_falsely_human_approved():
    import csv

    matrix_path = CASE / "results" / "matrices" / "a_to_b_associations.csv"
    with matrix_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {row["link_registry_status"] for row in rows} == {
        "PROVIDED_UNATTESTED"
    }
    # Existence of four interpretive source links is not a review attestation.
    assert any(int(row["linked_units"]) > 0 for row in rows)
    assert "human_approved" in (
        CASE / "reference" / "expected-analysis.json"
    ).read_text(encoding="utf-8")
    ref = json.loads(
        (CASE / "reference" / "expected-analysis.json").read_text(encoding="utf-8")
    )
    assert ref["adjudication"]["human_approved"] is False
