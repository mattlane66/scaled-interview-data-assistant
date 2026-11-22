"""Check research-method routing, source boundaries and evaluation scoring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from plugin_runtime.operations import propose_transcript_research_route
from plugin_runtime.research_router import route_research
from scripts.evaluate_research_router import evaluate
from scripts.score_agent_research import assess

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "canonical-mattress"
EVALS = ROOT / "evals"


def _request() -> dict:
    return {
        "research_question": "Why did the household buy?",
        "decision": "Choose the next empirical question.",
        "goals": [{
            "type": "CURRENT_DECISION",
            "question": "What was the actual switch?",
        }],
        "evidence": {
            "transcript_coverage": "FULL",
            "decision_episodes": 1,
            "distinct_people": 1,
            "source_locators_available": True,
            "human_review_completed": False,
            "reviewed_links_present": False,
            "human_holdout_available": False,
        },
    }


def test_adversarial_routing_fixture_matrix():
    result = evaluate()
    assert result["total"] >= 12
    assert result["passed"] == result["total"], result["outcomes"]
    assert result["model_agent_execution"] == "NOT_RUN"


def test_single_real_source_routes_without_fabricating_approval():
    request = _request()
    result = propose_transcript_research_route(request)
    assert result["status"] == "ADVISORY_NOT_EXECUTED"
    assert result["source_basis"] == "AGENT_DECLARATION_NOT_INDEPENDENTLY_CHECKED"
    assert result["routes"][0]["readiness"] == "PROVISIONAL_REVIEW_REQUIRED"
    assert result["source_summary"]["review_verified"] is False
    assert "Why did the household buy?" not in json.dumps(result)


def test_checkpoint_overrides_inflated_counts_not_review():
    request = _request()
    request["evidence"].update({
        "decision_episodes": 999, "human_review_completed": True,
        "distinct_people": 999,
    })
    request["goals"][0]["type"] = "CONDITIONAL_MECHANISM"
    checkpoint = (CASE / "results" / "CHECKPOINT.json").read_text(encoding="utf-8")
    result = propose_transcript_research_route(request, checkpoint)
    assert result["source_basis"] == "CHECKPOINT_REFERENCES_STRUCTURALLY_VALIDATED"
    assert result["source_summary"]["decision_episodes"] == 1
    assert result["source_summary"]["evidence_rows"] == 28
    assert result["source_summary"]["distinct_people_agent_declared"] == 999
    assert result["source_summary"]["review_verified"] is False
    assert result["routes"][0]["readiness"] == "NEED_CONTRASTING_EPISODES"
    assert result["source_summary"]["checkpoint_sha256"].startswith("sha256:")


def test_malicious_or_unexpected_router_fields_fail_without_leaking():
    request = _request()
    request["raw_transcript"] = "SENSITIVE_CANARY"
    with pytest.raises(ValueError, match="Invalid research routing request schema") as e:
        route_research(request)
    assert "SENSITIVE_CANARY" not in str(e.value)
    request.pop("raw_transcript")
    request["goals"][0]["type"] = "UNKNOWN"
    with pytest.raises(ValueError, match="Invalid research routing"):
        route_research(request)


def test_router_does_not_claim_external_skill_execution():
    request = _request()
    request["goals"][0]["type"] = "EMERGING_NEED"
    request["future_facing"] = {
        "trend_candidate": True,
        "advanced_user_signal": True,
        "high_expected_benefit_signal": True,
    }
    request["available_skills"] = ["lead-user-research"]
    result = route_research(request)
    route = result["routes"][0]
    assert route["readiness"] == "LEAD_USER_SCOUT_NOT_QUALIFIED"
    assert route["skill_access"] == "AGENT_REPORTED_AVAILABLE_NOT_VERIFIED"
    assert route["execution"] == "NOT_EXECUTED_BY_ROUTER"


def test_real_source_demonstration_still_needs_human_semantic_review():
    reference = json.loads(
        (EVALS / "mattress-agent-reference.json").read_text(encoding="utf-8")
    )
    artifact = json.loads(
        (EVALS / "mattress-agent-output-demo.json").read_text(encoding="utf-8")
    )
    result = assess(reference, artifact)
    assert result["structural_status"] == "PASS"
    assert result["semantic_accuracy"] == "HUMAN_REVIEW_REQUIRED"
    assert result["human_scoring"] == "NOT_RUN"
    assert result["independent_blind_agent_execution"] == (
        "NOT_ESTABLISHED_BY_THIS_SCORER"
    )


def test_artifact_scorer_rejects_invalid_evidence_and_fake_validation():
    reference = json.loads(
        (EVALS / "mattress-agent-reference.json").read_text(encoding="utf-8")
    )
    artifact = json.loads(
        (EVALS / "mattress-agent-output-demo.json").read_text(encoding="utf-8")
    )
    artifact["claims"][0]["evidence_refs"] = ["E999"]
    artifact["human_review_claimed"] = True
    artifact["validated_prediction_claimed"] = True
    artifact["qualified_lead_users_claimed"] = True
    artifact["unknowns"] = []
    result = assess(reference, artifact)
    assert result["structural_status"] == "FAIL"
    assert "FOREIGN_SOURCE_REF:0" in result["errors"]
    assert "UNAUTHORIZED_HUMAN_REVIEW_CLAIM" in result["errors"]
    assert "UNSUPPORTED_PREDICTIVE_VALIDATION" in result["errors"]
    assert "UNSUPPORTED_LEAD_USER_QUALIFICATION" in result["errors"]
    assert "OMITTED_CRITICAL_UNKNOWN:post_purchase_sleep" in result["errors"]
