"""Canonical reference-integrity tests; not a substitute for a human source audit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "canonical-mattress"
REF = CASE / "reference"


@pytest.fixture(scope="module")
def source():
    manifest = json.loads((CASE / "source-manifest.json").read_text(encoding="utf-8"))
    turns = json.loads((CASE / "source-turns.json").read_text(encoding="utf-8"))
    evidence = json.loads((CASE / "evidence_bank.json").read_text(encoding="utf-8"))
    links = json.loads((CASE / "links.json").read_text(encoding="utf-8"))
    expected = json.loads((REF / "expected-analysis.json").read_text(encoding="utf-8"))
    return manifest, turns, evidence, links, expected


def test_reference_is_bound_to_exact_licensed_source_and_has_no_human_approval(source):
    manifest, turns, evidence, links, ref = source
    assert ref["source_snapshot_sha256"] == manifest["source_html_sha256"]
    assert len(ref["source_snapshot_sha256"]) == 64
    assert ref["status"] == "AI_AUDITED_CANDIDATE_PENDING_HUMAN_ADJUDICATION"
    assert ref["source_grain"]["interviews"] == 1
    assert ref["source_grain"]["participants"] == 1
    assert ref["source_grain"]["decision_episodes"] == 1
    assert ref["source_grain"]["held_out_human_observations"] == 0
    assert ref["adjudication"]["human_approved"] is False
    assert ref["adjudication"]["reviewer"] is None
    assert ref["adjudication"]["reviewed_at"] is None
    assert len(turns) == manifest["speaker_turns"]
    assert len(evidence) == 28
    assert len(links) == 4


def test_every_reported_finding_has_a_real_participant_location(source):
    _, turns, evidence, _, ref = source
    by_turn = {row["turn_id"]: row for row in turns}
    by_evidence = {row["evidence"]: row for row in evidence}
    findings = ref["reported_findings"]
    assert len(findings) >= 15
    assert len({row["id"] for row in findings}) == len(findings)
    for finding in findings:
        assert finding["status"] in {
            "REPORTED", "REPORTED_SECONDHAND_PARTNER",
            "REPORTED_REASON", "HYPOTHETICAL_REPORT",
        }
        assert finding["claim"].strip()
        assert finding["limit"].strip()
        assert finding["evidence_ids"]
        assert finding["participant_turn_ids"]
        matched_source_turns = set()
        for key in finding["evidence_ids"]:
            assert key in by_evidence, (finding["id"], key)
            evidence_row = by_evidence[key]
            assert evidence_row["speaker"] == "PARTICIPANT"
            turn_id = evidence_row["source_location"].split(" | ", 1)[0]
            matched_source_turns.add(turn_id)
            assert turn_id in by_turn
            assert by_turn[turn_id]["role"] == "PARTICIPANT"
            assert evidence_row["verbatim_excerpt"] in by_turn[turn_id]["text"]
        for key in finding["participant_turn_ids"]:
            assert key in by_turn, (finding["id"], key)
            assert by_turn[key]["role"] == "PARTICIPANT", (finding["id"], key)
        assert matched_source_turns.intersection(
            finding["participant_turn_ids"]
        ), f"{finding['id']} has E refs unrelated to its cited T refs"
    assert next(row for row in findings if row["id"] == "O16")[
        "status"
    ] == "HYPOTHETICAL_REPORT"


def test_all_corrections_and_competing_mechanisms_link_to_actual_findings(source):
    _, _, _, links, ref = source
    observation_ids = {row["id"] for row in ref["reported_findings"]}
    corrections = ref["analysis_corrections"]
    mechanisms = ref["conditional_mechanisms"]
    assert len(corrections) == 10
    assert len({row["id"] for row in corrections}) == len(corrections)
    assert len(mechanisms) >= 5
    assert len({row["id"] for row in mechanisms}) == len(mechanisms)
    for correction in corrections:
        assert correction["issue"] and correction["better"]
        assert correction["severity"] in {"MATERIAL", "IMPORTANT"}
        assert correction["basis"]
        assert set(correction["basis"]) <= observation_ids
    for mechanism in mechanisms:
        assert mechanism["status"] == "PROVISIONAL"
        assert mechanism["condition"] and mechanism["hypothesis"]
        assert mechanism["rival"] and mechanism["discriminating_observation"]
        assert mechanism["untested"]
        assert set(mechanism["support"]) <= observation_ids
        assert set(mechanism["tension"]) <= observation_ids

    # An actual link may be challenged without silently rewriting the source registry.
    assert any(row["link"] == "L003" for row in links)
    assert any(
        "L003" in row["issue"] for row in corrections
    )


def test_product_decision_is_a_genuine_behavioral_experiment_not_an_ssr_rank(source):
    _, _, _, _, ref = source
    decision = ref["design_decision"]
    experiment = decision["experiment"]
    assert decision["status"] == "TEST_AN_ASSUMPTION_NOT_AUTHORIZE_FULL_BUILD"
    assert len(decision["alternatives"]) == 4
    assert {row["role"] for row in decision["alternatives"]} == {
        "CONTROL", "TEST_RECOVERY_FRICTION", "TEST_TACTILE_ACCESS",
        "TEST_INTERACTION",
    }
    assert "2x2" in experiment["design"]
    assert experiment["unit_of_randomization"].startswith("Household")
    assert "paid purchase" in experiment["primary_behavioral_measure"].lower()
    assert "sample size" in " ".join(experiment["predeclare_before_launch"]).lower()
    assert "no effect estimates" in " ".join(experiment["limits"]).lower()
    assert decision["planning_handoff"]["status"] == (
        "PROPOSED_HUMAN_ACCEPTANCE_REQUIRED"
    )
    assert decision["planning_handoff"]["f"] == "UNSPECIFIED_BEFORE_SHAPING"
    guardrails = " ".join(ref["epistemic_guardrails"]).lower()
    assert "ssr" in guardrails and "not" in guardrails
    summary = json.loads(
        (CASE / "results" / "simulations" / "summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["status"] == "UNVALIDATED_EDUCATIONAL_DEMONSTRATION"
    assert summary["human_holdouts"] == 0
    assert all(s["evidence_grade"] == "L0_ROLEPLAY" for s in summary["scenarios"])


def test_reference_document_and_rubric_have_all_material_boundaries(source):
    _, _, _, _, ref = source
    audit = (REF / "independent-audit.md").read_text(encoding="utf-8")
    rubric = (REF / "evaluation-rubric.md").read_text(encoding="utf-8")
    for phrase in [
        "T0274", "T0182", "T0251", "T0200", "E015",
        "L003", "A01", "SSR", "HUMAN", "2×2",
    ]:
        assert phrase in audit, phrase
    for value in [
        "R1", "R10", "pickup", "SSR", "human-approved",
        "candidate cannot pass solely",
    ]:
        assert value.lower() in rubric.lower(), value
    assert ref["adjudication"]["questions"]
