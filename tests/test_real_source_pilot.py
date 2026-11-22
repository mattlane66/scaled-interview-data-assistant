"""Pilot on two published real transcripts, with no false independent validation."""

from __future__ import annotations

import json
from pathlib import Path

from plugin_runtime.research_router import route_research
from scripts.evaluate_real_source_pilot import evaluate

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals" / "real-source-pilot"


def test_two_real_source_case_analyses_have_bounded_evidence():
    result = evaluate()
    assert result["status"] == "SOURCE_LINKED_SELF_PILOT_STRUCTURALLY_CHECKED"
    assert result["cases"] == result["structural_passed"] == 2
    assert result["source_evidence_rows"] >= 20
    assert result["independent_human_verification"] == "NOT_DONE"
    assert result["native_codex_qualitative_evaluation"] == "NOT_RUN"
    assert result["native_claude_qualitative_evaluation"] == "NOT_RUN"
    assert result["methods_executed"] == ["A2B_PROVISIONAL"]


def test_real_source_method_router_stops_on_missing_evidence_and_different_jobs():
    requests = json.loads((BASE / "routing-requests.json").read_text())
    assert len(requests["requests"]) >= 3
    for record in requests["requests"]:
        result = route_research(record["request"])
        statuses = [route["readiness"] for route in result["routes"]]
        assert statuses == record["expected_readiness"], record["id"]
        assert all(route["execution"] == "NOT_EXECUTED_BY_ROUTER"
                   for route in result["routes"])
        assert result["source_basis"] == "AGENT_DECLARATION_NOT_INDEPENDENTLY_CHECKED"
    assert requests["requests"][-1]["expected_readiness"] == ["STOP_DIFFERENT_JOBS"]


def test_pilot_does_not_materialize_restricted_transcript_text():
    manifest = json.loads((BASE / "manifest.json").read_text())
    assert manifest["source_material_republished"] is False
    for source in manifest["sources"]:
        assert source["url"].startswith("https://jobstobedone.org/")
        assert "copyright" in source["licensing"].lower()
    actual_files = {p.name for p in BASE.iterdir() if p.is_file()}
    assert not any(name.startswith("full-transcript") for name in actual_files)


def test_pilot_blocks_unauthorized_review_or_prediction_claims():
    keys = json.loads((BASE / "provisional-keys.json").read_text())
    for reference in keys["references"]:
        assert reference["reference_status"] == "SELF_BUILT_PROVISIONAL_NOT_INDEPENDENT_GOLD"
        assert reference["independent_human_gold_standard"] is False
        assert reference["human_review_authorized"] is False
        assert reference["validated_prediction_authorized"] is False
        assert reference["qualified_lead_users_authorized"] is False
