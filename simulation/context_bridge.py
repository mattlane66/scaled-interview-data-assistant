"""Optional, evidence-traceable route to upstream Lead User Research.

This is an adapter and provenance contract, NOT a second Lead User engine.
A sparse interview corpus does not justify inventing present conditions,
Lead User qualifications, prevalence or a selected product outcome.
"""

from __future__ import annotations

import json
from typing import Any

from simulation.core import SimulationError, schema_check, sha256_text

METHOD_REPO = (
    "https://github.com/mattlane66/planning-skills-for-agents-and-humans/"
    "tree/main/lead-user-research"
)
EVIDENCE_MODES = {
    "DESK_RESEARCH", "FIELDWORK_ENRICHED", "FULL_LEAD_USER_PROJECT",
}


def _source_scope(checkpoint: dict | None, request: dict) -> None:
    if checkpoint is None:
        if request["episode_refs"] or request["evidence_refs"]:
            raise SimulationError("No checkpoint: original E/D references must be empty")
        return
    episodes = {row["episode"] for row in checkpoint["episode_index"]}
    evidence = {row["evidence"]: row for row in checkpoint["evidence_bank"]}
    chosen = set(request["episode_refs"])
    if not chosen <= episodes:
        raise SimulationError("Context route cites an unknown decision episode")
    refs = set(request["evidence_refs"])
    if not refs <= evidence:
        raise SimulationError("Context route cites an unknown source evidence ID")
    if any(evidence[ref]["episode"] not in chosen for ref in refs):
        raise SimulationError("Context route evidence belongs outside the chosen episodes")
    if refs and not chosen:
        raise SimulationError("Context evidence must identify its decision episode")


def triage_context_gap(
    checkpoint: dict | None, digest: str | None, request: dict[str, Any]
) -> dict[str, Any]:
    """Propose the smallest evidence move, without executing future-facing research."""
    schema_check(request, "context-route.schema.json")
    _source_scope(checkpoint, request)

    future = request["future_facing"]
    advance = all(
        isinstance(future[field], str) and future[field].strip()
        for field in ("trend_candidate", "advanced_user_signal", "high_expected_benefit_signal")
    )
    if not request["material_to_decision"]:
        route, reason = (
            "DEFER", "The gap is not currently consequential to the decision."
        )
    elif request["observability"] == "TRACE_OBSERVABLE":
        route, reason = (
            "TRACE_RESEARCH",
            "The missing variable can be investigated through existing behavioral traces.",
        )
    elif request["observability"] == "UNKNOWN":
        route, reason = (
            "CHECK_OBSERVABILITY",
            "Determine what can be observed before choosing interviews or future-facing work.",
        )
    elif advance:
        route, reason = (
            "LEAD_USER_RESEARCH",
            "Advanced user and trend candidates justify an optional upstream search, "
            "NOT a qualified Lead User or evidence of population propagation.",
        )
    else:
        route, reason = (
            "TARGETED_CURRENT_RESEARCH",
            "A material current-state gap is not yet grounded in an important trend "
            "and high-benefit advanced-user candidate.",
        )
    fingerprint = sha256_text(json.dumps(
        {"checkpoint": digest, "request": request}, sort_keys=True,
        ensure_ascii=False, allow_nan=False,
    ))
    output = {
        "bridge_version": "1.0",
        "route_id": "CUR-" + fingerprint.removeprefix("sha256:")[:12],
        "source_checkpoint_sha256": digest,
        "status": "PROPOSED",
        "route": route,
        "reason": reason,
        "question": request,
        "source_lineage": {
            "episode_refs": request["episode_refs"],
            "evidence_refs": request["evidence_refs"],
            "coverage": request["coverage"],
            "not_a_finding": True,
        },
        "upstream_method": METHOD_REPO if route == "LEAD_USER_RESEARCH" else None,
        "lead_user_research_brief": (
            {
                "Research Domain / Problem Space": request["domain"],
                "Target Market": request["target_population"],
                "What do we want to understand?": request["uncertainty"],
                "What human decision should this research help inform?": request["decision"],
                "Mode": "STANDARD",
                "Optional hypotheses": [future["trend_candidate"]],
                "qualification_claim": "NOT_EVALUATED_LU1_OR_LU2",
                "evidence_grade": "PROVISIONAL_ROUTING_SIGNAL",
            }
            if route == "LEAD_USER_RESEARCH" else None
        ),
        "human_authority": "RESEARCH_ROUTE_NOT_ACCEPTED",
        "x_current_situation": "UNCHANGED",
        "evidence_status": "GAP_NOT_RESOLVED",
    }
    return output


def import_lead_user_context(
    checkpoint: dict | None,
    digest: str | None,
    route: dict,
    source_handoff: dict,
) -> dict[str, Any]:
    """Validate research lineage and return a *proposed* x extension sidecar.

    This checks internal provenance consistency, not the external study's factual
    correctness, LU1/LU2 review, or the actual existence of referenced web pages.
    """
    if not isinstance(route, dict) or "question" not in route:
        raise SimulationError("Expected a previously generated context-route document")
    expected = triage_context_gap(checkpoint, digest, route["question"])
    if route != expected:
        raise SimulationError("Context route has changed or belongs to another checkpoint")
    if route["route"] != "LEAD_USER_RESEARCH":
        raise SimulationError("Lead User return is not eligible for this context route")
    schema_check(source_handoff, "context-return.schema.json")
    if (source_handoff["route_id"] != route["route_id"]
            or source_handoff["source_checkpoint_sha256"] != digest):
        raise SimulationError("Lead User return is not bound to this original route/checkpoint")
    ws = source_handoff["workspace"]
    evidence = {}
    for e in source_handoff["external_evidence"]:
        if e["ref"] in evidence:
            raise SimulationError("Duplicate upstream evidence ID")
        evidence[e["ref"]] = e
    lead_episodes = {}
    for ep in source_handoff["lead_user_episodes"]:
        if ep["ref"] in lead_episodes:
            raise SimulationError("Duplicate upstream Lead User episode ID")
        for key in ("lu1_evidence_refs", "lu2_evidence_refs"):
            if not ep[key] or not set(ep[key]) <= evidence.keys():
                raise SimulationError(f"Upstream {key} must resolve to source-located evidence")
        lead_episodes[ep["ref"]] = ep
    by_id = set()
    emerging, hypothesized = [], []
    for item in source_handoff["x_candidates"]:
        if item["id"] in by_id:
            raise SimulationError("Duplicate imported x candidate ID")
        by_id.add(item["id"])
        if not set(item["source_evidence_refs"]) <= evidence.keys():
            raise SimulationError("x candidate cites missing upstream source evidence")
        if not set(item["source_lu_refs"]) <= lead_episodes.keys():
            raise SimulationError("x candidate cites missing Lead User episode")
        if any(
            lead_episodes[ref]["qualification_status"] != "QUALIFIED_IN_SOURCE"
            for ref in item["source_lu_refs"]
        ):
            raise SimulationError(
                "Qualified x evidence requires explicit source-declared LU1/LU2 qualification"
            )
        if item["classification"] == "EMERGING_USER_CONTEXT" and not any(
            evidence[ref]["evidence_kind"] in {"OBSERVED", "STATED"}
            for ref in item["source_evidence_refs"]
        ):
            raise SimulationError(
                "Emerging x requires an observed or stated source, not interpretation alone"
            )
        origin = [
            {
                "ref": f"LUR:{ws}:{ref}",
                "source_locator": evidence[ref]["source_locator"],
                "evidence_kind": evidence[ref]["evidence_kind"],
            }
            for ref in item["source_evidence_refs"]
        ]
        candidate = {
            "id": f"LUR:{ws}:{item['id']}",
            "statement": item["statement"],
            "source_evidence": origin,
            "source_lead_user_episodes": [
                f"LUR:{ws}:{ref}" for ref in item["source_lu_refs"]
            ],
            "classification": item["classification"],
            "transferability": item["transferability"],
            "transferability_rationale": item["transferability_rationale"],
            "limits": item["limits"],
            "source_qualification": "SOURCE_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        }
        if item["classification"] == "EMERGING_USER_CONTEXT":
            emerging.append(candidate)
        else:
            hypothesized.append(candidate)

    return {
        "bridge_version": "1.0",
        "type": "OPTIONAL_CONTEXT_EVIDENCE_EXTENSION",
        "status": "PROPOSED_HUMAN_REVIEW_REQUIRED",
        "source_route_id": route["route_id"],
        "source_checkpoint_sha256": digest,
        "original_interview_evidence_refs": route["source_lineage"]["evidence_refs"],
        "original_decision_episode_refs": route["source_lineage"]["episode_refs"],
        "source_handoff_ref": source_handoff["source_handoff_ref"],
        "source_handoff_fingerprint": sha256_text(json.dumps(
            source_handoff, sort_keys=True, ensure_ascii=False, allow_nan=False,
        )),
        "method": METHOD_REPO,
        "research_workspace": ws,
        "research_mode": source_handoff["mode"],
        "upstream_study_status": source_handoff["study_status"],
        "lead_user_qualification": "SOURCE_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "x_observed_in_original_interviews": "UNCHANGED",
        "emerging_x_from_lead_user_sources": emerging,
        "hypothesized_transfer_x": hypothesized,
        "contradictions": source_handoff["contradictions"],
        "mainstream_prevalence": "NOT_ESTABLISHED",
        "mainstream_behavior": "NOT_ESTABLISHED",
        "planning_y": "NOT_SELECTED",
        "planning_f": "UNSPECIFIED",
        "promoted_to_mainstream_x": False,
        "review_gate": (
            "Human must inspect original Lead User evidence, LU1/LU2 qualification, "
            "independence, trend validity, contrasts and transferability before "
            "any planning promotion. This adapter never runs Lead User Research."
        ),
    }
