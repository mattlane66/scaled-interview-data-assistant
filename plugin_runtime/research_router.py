"""Conservative, source-aware routing for transcript-first research.

Routing is advisory: it neither analyzes a transcript nor invokes external
skills. Semantic classification and source declarations are inputs supplied
by the research agent; only checkpoint counts/references can be checked here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "simulation" / "schemas" / "research-request.schema.json"
)
METHODS = {
    "CURRENT_DECISION": (
        "A2B",
        "plugins/scaled-interview-data-assistant/skills/analyze-interview/SKILL.md",
        None,
    ),
    "CONDITIONAL_MECHANISM": (
        "BEHAVIORAL_MECHANISM_MAP",
        "plugins/scaled-interview-data-assistant/skills/compare-mechanisms/SKILL.md",
        None,
    ),
    "COUNTERFACTUAL_RESPONSE": (
        "BEHAVIORAL_SIMULATION",
        "https://github.com/mattlane66/behavioral-simulation-for-agents-and-humans/"
        "blob/main/behavioral-simulation/SKILL.md",
        "behavioral-simulation",
    ),
    "EMERGING_NEED": (
        "LEAD_USER_RESEARCH",
        "https://github.com/mattlane66/planning-skills-for-agents-and-humans/"
        "blob/main/lead-user-research/SKILL.md",
        "lead-user-research",
    ),
    "OTHER": ("OTHER_METHOD", "", None),
}


def route_research(
    request: dict[str, Any],
    *, checkpoint: dict[str, Any] | None = None,
    checkpoint_sha256: str | None = None,
) -> dict[str, Any]:
    """Decide the smallest valid research move without executing research."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        Draft202012Validator(schema).validate(request)
    except ValidationError:
        raise ValueError("Invalid research routing request schema") from None

    evidence = request.get("evidence") or {}
    counterfactual = request.get("counterfactual") or {}
    future = request.get("future_facing") or {}
    available = set(request.get("available_skills") or [])

    episodes = evidence.get("decision_episodes", 0)
    people = evidence.get("distinct_people", 0)
    coverage = evidence.get("transcript_coverage", "UNKNOWN")
    has_locators = evidence.get("source_locators_available", False)
    source_basis = "AGENT_DECLARATION_NOT_INDEPENDENTLY_CHECKED"
    evidence_rows = None

    if checkpoint is not None:
        # The checkpoint is schema-checked upstream. Override only quantities
        # that can be determined; do not authenticate participants or reviews.
        episodes = len(checkpoint["episode_index"])
        evidence_rows = len(checkpoint["evidence_bank"])
        has_locators = evidence_rows > 0
        source_basis = "CHECKPOINT_REFERENCES_STRUCTURALLY_VALIDATED"
        if evidence_rows == 0:
            coverage = "UNKNOWN"

    results = []
    for i, goal in enumerate(request["goals"], start=1):
        category = goal["type"]
        method, protocol, skill = METHODS[category]
        needed: list[str] = []
        if goal.get("material_to_decision") is False:
            readiness = "DEFER_NOT_MATERIAL"
            step = "Defer this question until it could change the decision."
        elif category == "CURRENT_DECISION":
            if coverage == "NONE":
                readiness = "NEED_SOURCE"
                step = "Obtain a permitted real transcript or decision trace."
            elif not has_locators or episodes == 0:
                readiness = "EXTRACT_AND_LOCATE_EPISODES"
                needed = ["bounded past episode", "exact source locations"]
                step = "Segment the source and reconstruct a past episode provisionally."
            elif not evidence.get("human_review_completed", False):
                readiness = "PROVISIONAL_REVIEW_REQUIRED"
                needed = ["human evidence, code and link review"]
                step = "Produce source-linked A/Y/tipping/X/B/outcome and request review."
            else:
                readiness = "ELIGIBLE_FOR_A2B_ANALYSIS"
                step = "Reconstruct and audit source-linked decisions; do not assume success."
        elif category == "CONDITIONAL_MECHANISM":
            if episodes < 2:
                readiness = "NEED_CONTRASTING_EPISODES"
                needed = ["at least two real bounded decision episodes"]
                step = "Analyze current episode and seek contrasting real decisions."
            elif people < 2:
                readiness = "NEED_DISTINCT_PERSON_COVERAGE"
                needed = ["independently situated people or explicit within-person scope"]
                step = "Preserve within-person evidence and recruit/locate contrastive cases."
            elif not (evidence.get("human_review_completed", False)
                      and evidence.get("reviewed_links_present", False)):
                readiness = "PROVISIONAL_MECHANISMS_ONLY"
                needed = ["human-reviewed source evidence and A/B links"]
                step = "Draft rivals and falsifiers, then obtain required reviews."
            else:
                readiness = "ELIGIBLE_FOR_REVIEW_GATED_MAP"
                step = "Compare cases with ALIGNS/COUNTEREXAMPLE/AMBIGUOUS/UNASSESSED."
        elif category == "COUNTERFACTUAL_RESPONSE":
            if not all(counterfactual.get(f, False) for f in (
                "baseline_defined", "intervention_defined", "population_defined"
            )):
                readiness = "SPECIFY_COUNTERFACTUAL_FIRST"
                needed = ["baseline", "actual change", "target person or population"]
                step = "Define scenario, action space, time and intended decision."
            elif not evidence.get("human_holdout_available", False):
                readiness = "L0_EXPLORATION_NOT_PREDICTION"
                needed = ["independent matching human holdout for any predictive claim"]
                step = "Explore possible responses only; use the upstream protocol."
            else:
                readiness = "HOLDOUT_DESIGN_NOT_VALIDATED"
                needed = ["independent held-out evaluation and calibration"]
                step = "Run upstream simulation and measure error before predictions."
        elif category == "EMERGING_NEED":
            if not all(future.get(f, False) for f in (
                "trend_candidate", "advanced_user_signal", "high_expected_benefit_signal"
            )):
                readiness = "DISCOVER_TRENDS_AND_CANDIDATES"
                needed = ["important trend evidence", "advanced-user signal",
                          "unusually high expected benefit signal"]
                step = "Investigate trend first, then possible LU1/LU2 cases."
            else:
                readiness = "LEAD_USER_SCOUT_NOT_QUALIFIED"
                needed = ["independent LU1/LU2 evidence per real need episode"]
                step = "Invoke upstream SCOUT/phase protocol; do not infer qualification."
        else:
            readiness = "REFER_TO_OTHER_RESEARCH"
            step = "Choose an appropriate method outside these four."

        access = (
            "BUILT_IN_PROTOCOL" if skill is None else
            "AGENT_REPORTED_AVAILABLE_NOT_VERIFIED" if skill in available else
            "EXTERNAL_SKILL_REQUIRED"
        )
        results.append({
            "goal_id": f"Q{i:02d}",
            "method": method,
            "readiness": readiness,
            "next_move": step,
            "missing_evidence": needed,
            "protocol": protocol,
            "skill": skill,
            "skill_access": access,
            "execution": "NOT_EXECUTED_BY_ROUTER",
            "interpretation_status": "PROPOSED_UNREVIEWED",
        })

    return {
        "route_version": "1.0",
        "status": "ADVISORY_NOT_EXECUTED",
        "decision_authority": "HUMAN",
        "source_basis": source_basis,
        "source_summary": {
            "source_coverage": coverage,
            "decision_episodes": episodes,
            "distinct_people_agent_declared": people,
            "evidence_rows": evidence_rows,
            "checkpoint_sha256": checkpoint_sha256,
            "human_review_agent_declared": evidence.get("human_review_completed", False),
            "review_verified": False,
        },
        "routes": results,
        "guardrails": [
            "No synthetic responses become human evidence.",
            "Method selection does not establish source accuracy or human review.",
            "Only real, source-bound outcomes support descriptive behavioral claims.",
            "A single interview cannot establish independent population mechanisms.",
            "Lead User qualification requires verified LU1 and LU2 for a relevant trend.",
            "An available holdout is not a completed or calibrated validation.",
            "Do not change accepted y, requirements, or a selected shape.",
        ],
    }
