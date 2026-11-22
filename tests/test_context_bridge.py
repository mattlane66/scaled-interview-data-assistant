"""Conservative, source-traceable optional handoff to upstream Lead User Research."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from plugin_runtime.operations import (
    propose_context_research_route,
    validate_lead_user_research_return,
)
from simulation.context_bridge import import_lead_user_context, triage_context_gap
from simulation.core import SimulationError, load_checkpoint, schema_check

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "canonical-mattress"


def checkpoint():
    path = CASE / "results" / "CHECKPOINT.json"
    return load_checkpoint(path)


def question(**overrides):
    result = {
        "domain": "Mattress replacement",
        "decision": "Which unknown conditions should we investigate before shaping?",
        "target_population": "Households struggling to replace an inadequate mattress",
        "uncertainty": "How does changing delivery/return infrastructure affect x?",
        "material_to_decision": True,
        "episode_refs": ["D01"],
        "evidence_refs": ["E010", "E014"],
        "coverage": "PARTIAL",
        "observability": "PARTIALLY_OBSERVABLE",
        "future_facing": {
            "trend_candidate": "Possible future shift in home return infrastructure",
            "advanced_user_signal": "Candidate people already managing many trial returns",
            "high_expected_benefit_signal": "Potentially high cost of repeated returns",
        },
    }
    result.update(overrides)
    return result


def sample_return(route):
    return {
        "return_version": "1.0",
        "route_id": route["route_id"],
        "source_checkpoint_sha256": route["source_checkpoint_sha256"],
        "workspace": "trial_future_2026",
        "mode": "DESK_RESEARCH",
        "study_status": "DRAFT",
        "source_handoff_ref": "LUR:trial_future_2026:research-to-planning-v1",
        "external_evidence": [
            {
                "ref": "E1", "lead_user_episode_ref": "LU1",
                "source_locator": "Public field notes, section 1",
                "evidence_kind": "OBSERVED",
            },
            {
                "ref": "E2", "lead_user_episode_ref": "LU1",
                "source_locator": "Public interview, turn 3",
                "evidence_kind": "STATED",
            },
            {
                "ref": "E3", "lead_user_episode_ref": "LU1",
                "source_locator": "Public field notes, section 5",
                "evidence_kind": "OBSERVED",
            },
        ],
        "lead_user_episodes": [{
            "ref": "LU1",
            "lu1_evidence_refs": ["E1"],
            "lu2_evidence_refs": ["E2"],
            "advancement_indicator": "Source describes unusually advanced return conditions",
            "benefit_signal": "Source reports strong economic benefit from resolving the need",
            "qualification_status": "QUALIFIED_IN_SOURCE",
            "qualification_caveats": "Source declaration not independently adjudicated.",
        }],
        "x_candidates": [
            {
                "id": "LX001",
                "statement": "Some advanced users report different recovery arrangements.",
                "source_evidence_refs": ["E3"],
                "source_lu_refs": ["LU1"],
                "classification": "EMERGING_USER_CONTEXT",
                "transferability": "UNKNOWN",
                "transferability_rationale": "No comparable mainstream observations.",
                "limits": "One bounded source episode, no population extrapolation.",
            },
            {
                "id": "LX002",
                "statement": "A similar friction may emerge for mainstream buyers later.",
                "source_evidence_refs": ["E3"],
                "source_lu_refs": ["LU1"],
                "classification": "HYPOTHESIZED_MAINSTREAM_TRANSFER",
                "transferability": "PLAUSIBLE",
                "transferability_rationale": "A parallel consumer constraint is suspected.",
                "limits": "No validation of incidence, direction, timing, or propagation.",
            },
        ],
        "contradictions": ["Mainstream user conditions were not measured."],
    }


def test_gap_routes_do_not_turn_sparsity_into_lead_user_qualification():
    data, digest = checkpoint()
    route = triage_context_gap(data, digest, question())
    assert route["route"] == "LEAD_USER_RESEARCH"
    assert route["status"] == "PROPOSED"
    assert route["human_authority"] == "RESEARCH_ROUTE_NOT_ACCEPTED"
    assert route["evidence_status"] == "GAP_NOT_RESOLVED"
    assert route["source_checkpoint_sha256"] == digest
    assert route["lead_user_research_brief"]["Mode"] == "STANDARD"
    assert route["lead_user_research_brief"]["qualification_claim"] == (
        "NOT_EVALUATED_LU1_OR_LU2"
    )
    assert route["source_lineage"]["evidence_refs"] == ["E010", "E014"]

    no_lu2 = copy.deepcopy(question())
    no_lu2["future_facing"]["high_expected_benefit_signal"] = ""
    assert triage_context_gap(data, digest, no_lu2)["route"] == "TARGETED_CURRENT_RESEARCH"
    assert triage_context_gap(data, digest, question(
        observability="TRACE_OBSERVABLE"
    ))["route"] == "TRACE_RESEARCH"
    assert triage_context_gap(data, digest, question(
        observability="UNKNOWN"
    ))["route"] == "CHECK_OBSERVABILITY"
    assert triage_context_gap(data, digest, question(
        material_to_decision=False
    ))["route"] == "DEFER"
    assert triage_context_gap(data, digest, question(
        coverage="MISSING"
    ))["route"] == "LEAD_USER_RESEARCH"


def test_empty_interview_dataset_can_route_without_fabricated_episode_ids():
    request = question(episode_refs=[], evidence_refs=[], coverage="MISSING")
    route = triage_context_gap(None, None, request)
    assert route["route"] == "LEAD_USER_RESEARCH"
    assert route["source_checkpoint_sha256"] is None
    via_tool = propose_context_research_route(request)
    assert via_tool == route
    with pytest.raises(SimulationError, match="No checkpoint"):
        triage_context_gap(None, None, question())
    fake = question(episode_refs=["D08"], evidence_refs=[])
    assert fake["episode_refs"]
    with pytest.raises(SimulationError, match="unknown decision episode"):
        data, digest = checkpoint()
        triage_context_gap(data, digest, fake)


def test_context_route_evidence_references_must_match_real_episodes():
    data, digest = checkpoint()
    with pytest.raises(SimulationError, match="unknown source evidence"):
        triage_context_gap(data, digest, question(evidence_refs=["E999"]))
    changed = copy.deepcopy(data)
    changed["episode_index"].append({
        "episode": "D02", "interview": "I01", "descriptor": "Other",
    })
    with pytest.raises(SimulationError, match="outside the chosen episodes"):
        triage_context_gap(changed, digest, question(episode_refs=["D02"]))
    bad = question()
    bad["future_facing"]["trend_candidate"] = {"injected": "not text"}
    with pytest.raises(SimulationError):
        triage_context_gap(data, digest, bad)


def test_lead_user_return_is_source_traceable_and_never_changes_current_x():
    data, digest = checkpoint()
    route = triage_context_gap(data, digest, question())
    evidence = sample_return(route)
    result = import_lead_user_context(data, digest, route, evidence)
    assert result["status"] == "PROPOSED_HUMAN_REVIEW_REQUIRED"
    assert result["x_observed_in_original_interviews"] == "UNCHANGED"
    assert result["planning_y"] == "NOT_SELECTED"
    assert result["planning_f"] == "UNSPECIFIED"
    assert result["promoted_to_mainstream_x"] is False
    assert result["mainstream_prevalence"] == "NOT_ESTABLISHED"
    assert result["source_checkpoint_sha256"] == digest
    assert result["original_interview_evidence_refs"] == ["E010", "E014"]
    assert result["source_handoff_fingerprint"].startswith("sha256:")
    assert result["lead_user_qualification"] == (
        "SOURCE_DECLARED_NOT_INDEPENDENTLY_VERIFIED"
    )
    assert result["emerging_x_from_lead_user_sources"][0][
        "source_evidence"
    ][0]["ref"] == "LUR:trial_future_2026:E3"
    assert result["hypothesized_transfer_x"][0]["transferability"] == "PLAUSIBLE"
    assert result["research_mode"] == "DESK_RESEARCH"
    assert result["upstream_study_status"] == "DRAFT"
    schema_check(evidence, "context-return.schema.json")


def test_return_rejects_forged_route_or_missing_lu1_lu2_evidence():
    data, digest = checkpoint()
    route = triage_context_gap(data, digest, question())
    returned = sample_return(route)

    changed = copy.deepcopy(route)
    changed["route"] = "DEFER"
    with pytest.raises(SimulationError, match="changed"):
        import_lead_user_context(data, digest, changed, returned)

    changed = copy.deepcopy(returned)
    changed["route_id"] = "CUR-000000000000"
    with pytest.raises(SimulationError, match="not bound"):
        import_lead_user_context(data, digest, route, changed)

    changed = copy.deepcopy(returned)
    changed["lead_user_episodes"][0]["lu2_evidence_refs"] = ["E999"]
    with pytest.raises(SimulationError, match="lu2_evidence_refs"):
        import_lead_user_context(data, digest, route, changed)

    changed = copy.deepcopy(returned)
    changed["lead_user_episodes"][0]["qualification_status"] = "PROVISIONAL"
    with pytest.raises(SimulationError, match="qualification"):
        import_lead_user_context(data, digest, route, changed)

    changed = copy.deepcopy(returned)
    changed["external_evidence"][2]["lead_user_episode_ref"] = "LU2"
    with pytest.raises(SimulationError, match="unknown Lead User episode"):
        import_lead_user_context(data, digest, route, changed)

    changed = copy.deepcopy(returned)
    changed["x_candidates"][0]["source_evidence_refs"] = ["E99"]
    with pytest.raises(SimulationError, match="missing upstream"):
        import_lead_user_context(data, digest, route, changed)


def test_lead_user_return_does_not_treat_ai_inference_as_observed_x():
    data, digest = checkpoint()
    route = triage_context_gap(data, digest, question())
    changed = sample_return(route)
    changed["external_evidence"][2]["evidence_kind"] = "INFERRED"
    with pytest.raises(SimulationError, match="observed or stated"):
        import_lead_user_context(data, digest, route, changed)

    changed = sample_return(route)
    changed["x_candidates"][0]["transferability"] = "LEAD_USER_BOUND"
    proposed = import_lead_user_context(data, digest, route, changed)
    assert proposed["emerging_x_from_lead_user_sources"][0]["transferability"] == (
        "LEAD_USER_BOUND"
    )
    assert proposed["promoted_to_mainstream_x"] is False


def test_import_cannot_run_on_trace_or_current_interview_route():
    data, digest = checkpoint()
    route = triage_context_gap(data, digest, question(observability="TRACE_OBSERVABLE"))
    with pytest.raises(SimulationError, match="not eligible"):
        import_lead_user_context(data, digest, route, sample_return(route))


def test_mcp_adapter_enforces_hash_and_does_not_store_or_auto_accept():
    checkpoint_raw = (CASE / "results" / "CHECKPOINT.json").read_text(encoding="utf-8")
    route = propose_context_research_route(question(), checkpoint_json=checkpoint_raw)
    returned = validate_lead_user_research_return(
        route, sample_return(route), checkpoint_json=checkpoint_raw
    )
    assert returned["status"] == "PROPOSED_HUMAN_REVIEW_REQUIRED"
    assert returned["x_observed_in_original_interviews"] == "UNCHANGED"
    with pytest.raises(SimulationError, match="not bound"):
        wrong = sample_return(route)
        wrong["source_checkpoint_sha256"] = None
        validate_lead_user_research_return(
            route, wrong, checkpoint_json=checkpoint_raw
        )
