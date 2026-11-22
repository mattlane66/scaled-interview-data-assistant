"""Research-side boundaries for outcome evidence and proposed design inputs.

Evidence can inform a representation of x, reported human intent and hypotheses
for M. It cannot choose y or establish the effect of an untested candidate.
"""

from __future__ import annotations

from typing import Any

from simulation.core import SimulationError

STAGES = ("adoption", "use", "progress")
UNKNOWN_ASSESSMENT = {
    "status": "UNKNOWN",
    "evidence_refs": [],
    "interpretation": "NOT ASSESSED; absence of an assessment is not a negative result.",
}


def _namespaced(study: str, identifiers: list[str] | set[str]) -> list[str]:
    return [f"SID:{study}:{identifier}" for identifier in sorted(identifiers)]


def assess_outcomes(index: dict[str, Any], study: dict[str, Any]) -> list[dict[str, Any]]:
    """Check each analyst judgment against real evidence from the same episode.

    The absence of a follow-up always produces UNKNOWN, never no improvement.
    A self-report may document progress but cannot identify an intervention effect.
    """
    episodes = {row["episode"]: row for row in index["episodes"]}
    supplied = {}
    any_assessed = False
    for case in study.get("outcome_assessments", []):
        episode = case["episode"]
        if episode not in episodes:
            raise SimulationError(f"Outcome assessment references out-of-scope episode {episode}")
        if episode in supplied:
            raise SimulationError(f"Duplicate outcome assessment for episode {episode}")
        source_refs = set(episodes[episode]["evidence_refs"])
        for stage in STAGES:
            assessment = case[stage]
            refs = assessment["evidence_refs"]
            status = assessment["status"]
            if not set(refs) <= source_refs:
                raise SimulationError(
                    f"Outcome {stage} cites evidence outside episode {episode}"
                )
            if status == "UNKNOWN":
                if refs:
                    raise SimulationError(
                        f"Outcome {stage} UNKNOWN must not cite evidence as a result"
                    )
            else:
                any_assessed = True
                if not refs or not assessment["interpretation"].strip():
                    raise SimulationError(
                        f"Outcome {stage} assessed status requires evidence and interpretation"
                    )
        supplied[episode] = case
    if any_assessed and not study["review"].get("outcomes_reviewed", False):
        raise SimulationError("Outcome evidence must be reviewed by a named human analyst")

    results = []
    for eid, episode in sorted(episodes.items()):
        provided = supplied.get(eid)
        stages = {
            stage: (
                {
                    "status": provided[stage]["status"],
                    "evidence_refs": sorted(provided[stage]["evidence_refs"]),
                    "interpretation": provided[stage]["interpretation"],
                }
                if provided else dict(UNKNOWN_ASSESSMENT)
            )
            for stage in STAGES
        }
        results.append({
            "episode": eid,
            "interview": episode["interview"],
            "adoption": stages["adoption"],
            "use": stages["use"],
            "progress": stages["progress"],
            "attribution": {
                "status": "NOT_ESTABLISHED",
                "basis": (
                    "An interview may report actions, use, or progress; it cannot "
                    "alone identify the effect attributable to an intervention."
                ),
            },
            "not_a_causal_estimate": True,
        })
    return results


def frame_candidates(index: dict[str, Any], study_id: str) -> dict[str, Any]:
    """Group interpreted A/B codes with their original sources, never select y."""
    situations: dict[str, dict[str, Any]] = {}
    progress: dict[str, dict[str, Any]] = {}
    for episode in index["episodes"]:
        for link in episode["a_to_b_links"]:
            for destination, prefix, suffix in (
                (situations, "a", "CURRENT_SITUATION"),
                (progress, "b", "REPORTED_OR_INFERRED_PROGRESS"),
            ):
                code = link[f"{prefix}_code"]
                entry = destination.setdefault(code, {
                    "code": code,
                    "description": link[f"{prefix}_definition"],
                    "claim_type": "INTERPRETED_A_TO_B_CODE",
                    "candidate_role": suffix,
                    "authority": "PROPOSED_RESEARCH_INTERPRETATION",
                    "episode_refs": set(),
                    "evidence_refs": set(),
                    "link_refs": set(),
                    "interpretation_bases": set(),
                })
                entry["episode_refs"].add(episode["episode"])
                entry["evidence_refs"].update(link["evidence_refs"])
                entry["link_refs"].add(link["link"])
                entry["interpretation_bases"].add(link["basis"])

    def normalize(groups: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return [{
            **{k: v for k, v in entry.items()
               if k not in {"episode_refs", "evidence_refs", "link_refs",
                            "interpretation_bases"}},
            "episode_refs": _namespaced(study_id, entry["episode_refs"]),
            "source_evidence_refs": _namespaced(study_id, entry["evidence_refs"]),
            "link_refs": _namespaced(study_id, entry["link_refs"]),
            "interpretation_bases": sorted(entry["interpretation_bases"]),
        } for _, entry in sorted(groups.items())]

    interviews = sorted({row["interview"] for row in index["episodes"]})
    return {
        "x_current_situation": {
            "authority": "PROPOSED",
            "source": "REVIEWED_SOURCE_LINK_INTERPRETATIONS",
            "representations": normalize(situations),
            "not_direct_world_verification": True,
        },
        "human_intent": {
            "whose_account": "INTERVIEWED_PEOPLE",
            "interview_refs": _namespaced(study_id, interviews),
            "progress_candidates": normalize(progress),
            "competing_party_priorities": "NOT_RECONCILED",
            "not_a_product_team_priority_decision": True,
        },
        "y_selected_outcome": {
            "status": "NOT_SELECTED",
            "authority": "NOT_GRANTED_BY_RESEARCH",
            "decision_owner": None,
            "priority_tradeoffs": "NOT_DECIDED",
            "selection_requires": (
                "A human design or product authority must choose whose outcomes "
                "count, weigh conflicting priorities, and state the accepted goal."
            ),
        },
    }


def handoff_outcomes(assessments: list[dict[str, Any]], study_id: str) -> list[dict]:
    """Keep the three evidence statuses and attribution distinct at handoff."""
    return [{
        "episode_ref": f"SID:{study_id}:{row['episode']}",
        "interview_ref": f"SID:{study_id}:{row['interview']}",
        **{
            stage: {
                **{k: v for k, v in row[stage].items() if k != "evidence_refs"},
                "source_evidence_refs": _namespaced(
                    study_id, row[stage]["evidence_refs"]
                ),
            } for stage in STAGES
        },
        "attribution": row["attribution"],
    } for row in assessments]
