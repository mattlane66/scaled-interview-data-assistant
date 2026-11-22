"""Evidence-grounded cross-episode mechanism maps.

Human-coded patterns are provisional interpretations, not identified causal effects.
Never edits a checkpoint or assigns synthetic statements to observed evidence IDs.
"""

from __future__ import annotations

import json
import re
from typing import Any

from simulation.core import SimulationError, schema_check, sha256_text

STRONG_SOURCE_TYPES = {"concrete_event_or_behavior", "current_state", "observation"}


def _tokens(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [x.strip() for x in re.split(r"[,;/\n]+", str(value or "")) if x.strip()]


def resolve_scope(checkpoint: dict[str, Any], scope: dict[str, Any]) -> list[str]:
    """Resolve exactly one cluster or an explicitly named episode set."""
    episodes = {r["episode"]: r for r in checkpoint["episode_index"]}
    if scope["kind"] == "EPISODES":
        ids = scope["episode_ids"]
        if not set(ids) <= episodes.keys():
            raise SimulationError("Explicit scope contains unknown episode IDs")
        return sorted(ids)
    cluster = scope["cluster_id"]
    if not checkpoint["clusters"]:
        raise SimulationError("No accepted cluster assignments to inspect; use EPISODES scope")
    if cluster not in {r["cluster"] for r in checkpoint["clusters"]}:
        raise SimulationError(f"Unknown cluster: {cluster}")
    unit = checkpoint["analysis_unit"]
    members = {r[unit] for r in checkpoint["clusters"] if r["cluster"] == cluster}
    chosen = (
        [eid for eid in episodes if eid in members]
        if unit == "episode" else
        [eid for eid, row in episodes.items() if row["interview"] in members]
    )
    if not chosen:
        raise SimulationError(f"Cluster {cluster} has no decision episodes")
    return sorted(chosen)


def make_study(checkpoint: dict[str, Any], digest: str,
               scope: dict[str, Any]) -> dict[str, Any]:
    # Validate the selection before creating even an unapproved draft.
    schema_check(scope, "mechanism-scope.schema.json")
    resolve_scope(checkpoint, scope)
    return {
        "schema_version": "1.0",
        "study_id": "BMST001",
        "source_checkpoint_sha256": digest,
        "scope": scope,
        "research_question": "REPLACE: what conditions appear to distinguish decisions?",
        "review": {
            "reviewer": "",
            "reviewed_at": None,
            "approved_checkpoint_sha256": digest,
            "evidence_reviewed": False,
            "a_to_b_links_reviewed": False,
            "cluster_interpretation_reviewed": False,
            "contrasting_cases_reviewed": False,
        },
        "mechanisms": [],
    }


def inventory(checkpoint: dict[str, Any], digest: str,
              study: dict[str, Any]) -> dict[str, Any]:
    schema_check(study, "mechanism-study.schema.json")
    if study["source_checkpoint_sha256"] != digest:
        raise SimulationError("Mechanism study references a different checkpoint")
    selected = resolve_scope(checkpoint, study["scope"])
    episodes = {row["episode"]: row for row in checkpoint["episode_index"]}
    evidence = {row["evidence"]: row for row in checkpoint["evidence_bank"]}
    codebook = {row["code"]: row["definition"] for row in checkpoint["codebook"]}
    source_index = {row["source_id"]: row for row in checkpoint["source_index"]}
    rows = []
    for eid in selected:
        ref = episodes[eid]
        excerpts = sorted(
            (row for row in evidence.values() if row["episode"] == eid),
            key=lambda r: r["evidence"],
        )
        refs = [row["evidence"] for row in excerpts]
        coverage = sorted({source_index[row["source_id"]]["coverage"] for row in excerpts})
        links = []
        for row in checkpoint["a_to_b_links"]:
            if row["episode"] != eid:
                continue
            links.append({
                "link": row["link"], "episode": eid,
                "a_code": row["a_code"], "a_definition": codebook[row["a_code"]],
                "b_code": row["b_code"], "b_definition": codebook[row["b_code"]],
                "basis": row["basis"], "evidence_refs": _tokens(row["evidence"]),
                "rationale": row["rationale"],
                "contradictions": row.get("contradictions") or "NONE RECORDED",
            })
        rows.append({
            "episode": eid, "interview": ref["interview"],
            "descriptor": ref.get("descriptor") or "UNKNOWN",
            "source_coverage": coverage or ["UNKNOWN"],
            "evidence_refs": refs,
            "evidence_types": {
                row["evidence"]: {
                    "type": row["evidence_type"],
                    "source_id": row["source_id"],
                    "location": row["source_location"],
                } for row in excerpts
            },
            "a_to_b_links": links,
        })
    return {
        "schema_version": "1.0",
        "artifact_type": "RESEARCH_EPISODE_INVENTORY",
        "study_id": study["study_id"],
        "source_checkpoint_sha256": digest,
        "scope": study["scope"],
        "analysis_unit": checkpoint["analysis_unit"],
        "episodes": rows,
        "distinct_interviews": len({row["interview"] for row in rows}),
        "review_status": "NOT_ATTESTED",
        "limitations": [
            "A-to-B relationships are reviewed interpretations, not causal edges.",
            "Cluster membership is exploratory, not proof of a common job or mechanism.",
            "Evidence excerpts are not exported; use authorized sources for inspection.",
        ],
    }


def compile_map(checkpoint: dict[str, Any], digest: str,
                study: dict[str, Any]) -> dict[str, Any]:
    """Validate human-coded claims against a read-only checkpoint."""
    index = inventory(checkpoint, digest, study)
    review = study["review"]
    if review["approved_checkpoint_sha256"] != digest:
        raise SimulationError("Human review attestation refers to another checkpoint")
    if not review["reviewer"].strip() or review["reviewed_at"] is None:
        raise SimulationError("Named human reviewer and actual review date required")
    if not all(review[k] for k in (
        "evidence_reviewed", "a_to_b_links_reviewed", "contrasting_cases_reviewed"
    )):
        raise SimulationError("Evidence, A-to-B, and contrasting-case review required")
    if study["scope"]["kind"] == "CLUSTER" and not review["cluster_interpretation_reviewed"]:
        raise SimulationError("Cluster interpretation review required")
    if any("UNREADABLE" in row["source_coverage"] for row in index["episodes"]):
        raise SimulationError("Cannot compile mechanisms from unreadable source material")
    if not study["mechanisms"]:
        raise SimulationError("Declare at least one reviewed, provisional mechanism hypothesis")
    ids = [m["mechanism_id"] for m in study["mechanisms"]]
    if len(ids) != len(set(ids)):
        raise SimulationError("Mechanism IDs must be unique")
    if study["research_question"].strip().upper().startswith("REPLACE"):
        raise SimulationError("Complete the research question")

    episodes = {row["episode"]: row for row in index["episodes"]}
    all_evidence = {
        eid: row["evidence_types"][eid] for row in index["episodes"]
        for eid in row["evidence_refs"]
    }
    links = {
        row["link"]: row for episode in index["episodes"]
        for row in episode["a_to_b_links"]
    }
    outputs = []
    for mechanism in study["mechanisms"]:
        assigned = set()
        observations = []
        for annotation in mechanism["observations"]:
            eid = annotation["episode"]
            if eid not in episodes:
                raise SimulationError(
                    f"{mechanism['mechanism_id']}: observation references out-of-scope {eid}"
                )
            if eid in assigned:
                raise SimulationError(f"Repeated episode annotation: {eid}")
            assigned.add(eid)
            refs = annotation["evidence_refs"]
            lrefs = annotation["link_refs"]
            if not set(refs) <= set(episodes[eid]["evidence_refs"]):
                raise SimulationError(
                    f"{mechanism['mechanism_id']}: evidence belongs to another episode"
                )
            if not set(lrefs) <= {r["link"] for r in episodes[eid]["a_to_b_links"]}:
                raise SimulationError(
                    f"{mechanism['mechanism_id']}: A-to-B link belongs to another episode"
                )
            if annotation["stance"] == "UNASSESSED":
                if refs or lrefs:
                    raise SimulationError("UNASSESSED must not cite evidence or A-to-B links")
            elif not refs:
                raise SimulationError("Evidence required for any assessed episode classification")
            if not annotation["interpretation"].strip():
                raise SimulationError("Each annotation needs a reason or explicit unknown")
            observations.append({
                "episode": eid,
                "interview": episodes[eid]["interview"],
                "stance": annotation["stance"],
                "evidence_refs": refs,
                "link_refs": lrefs,
                "interpretation": annotation["interpretation"],
                "evidence_types": sorted({all_evidence[r]["type"] for r in refs}),
                "behavior_observed_in_sources": any(
                    all_evidence[r]["type"] in STRONG_SOURCE_TYPES for r in refs
                ),
            })
        for eid in sorted(set(episodes) - assigned):
            observations.append({
                "episode": eid, "interview": episodes[eid]["interview"],
                "stance": "UNASSESSED", "evidence_refs": [], "link_refs": [],
                "interpretation": "NOT ASSESSED — absence is not a counterexample",
                "evidence_types": [], "behavior_observed_in_sources": False,
            })
        observations.sort(key=lambda row: row["episode"])
        stances = {
            stance: sorted({row["interview"] for row in observations
                            if row["stance"] == stance})
            for stance in ("ALIGNS", "COUNTEREXAMPLE", "AMBIGUOUS", "UNASSESSED")
        }
        outputs.append({
            "mechanism_id": mechanism["mechanism_id"],
            "status": "PROVISIONAL",
            "condition": mechanism["condition"],
            "hypothesized_relationship": mechanism["hypothesized_relationship"],
            "rival_explanation": mechanism["rival_explanation"],
            "counterfactual_condition_change": mechanism["counterfactual_condition_change"],
            "disconfirming_observation": mechanism["disconfirming_observation"],
            "discriminating_human_test": mechanism["discriminating_human_test"],
            "revisit_when": mechanism["revisit_when"],
            "observations": observations,
            "distinct_interviews_by_stance": stances,
            "within_interview_conflicts": sorted(
                set(stances["ALIGNS"]) & set(stances["COUNTEREXAMPLE"])
            ),
            "unassessed_episode_ids": [
                row["episode"] for row in observations if row["stance"] == "UNASSESSED"
            ],
            "cautions": [
                "Classifications are analyst judgments, not causal effects.",
                "Absence of a counterexample in coded material is not evidence of absence.",
            ],
        })
    no_cross_person = index["distinct_interviews"] < 2
    index["review_status"] = "HUMAN_REVIEW_ATTESTED_NOT_INDEPENDENTLY_VERIFIED"
    return {
        "schema_version": "1.0",
        "artifact_type": "BEHAVIORAL_MECHANISM_MAP",
        "status": "PROVISIONAL",
        "study_id": study["study_id"],
        "source_checkpoint_sha256": digest,
        "study_sha256": sha256_text(json.dumps(study, sort_keys=True)),
        "scope": study["scope"],
        "research_question": study["research_question"],
        "reviewer_attestation": {
            "reviewer": review["reviewer"],
            "reviewed_at": review["reviewed_at"],
            "verified_independently": False,
        },
        "source_inventory": index,
        "mechanisms": outputs,
        "cross_person_comparison_possible": not no_cross_person,
        "limitations": [
            "Research coding and clusters are provisional and not causal proof.",
            "Counts describe this selected sample; they do not estimate prevalence.",
            "Multiple episodes from one interview are not independent people.",
            "Unassessed cases are not negative evidence.",
            "Claims without concrete event/observation evidence are weaker than observed behavior.",
            "Reviewer flags are attestations, not independent verification.",
            "Counterfactual effects require real-world identification or validation.",
        ] + ([
            "Only one interview contributes; no cross-person pattern can be inferred."
        ] if no_cross_person else []),
    }


def _clean(value: Any) -> str:
    return " ".join(str(value).replace("|", "\\|").split())


def render_map(mapped: dict[str, Any]) -> str:
    if mapped.get("artifact_type") != "BEHAVIORAL_MECHANISM_MAP":
        raise SimulationError("Expected compiled behavioral mechanism map")
    lines = [
        "# Behavioral Mechanism Map", "",
        f"**Study:** {mapped['study_id']} — PROVISIONAL",
        f"**Research question:** {mapped['research_question']}",
        f"**Source checkpoint:** {mapped['source_checkpoint_sha256']}",
        f"**Episodes:** {', '.join(x['episode'] for x in mapped['source_inventory']['episodes'])}",
        f"**Distinct interviews:** {mapped['source_inventory']['distinct_interviews']}",
        "**No population prevalence or identified causal effects.**", "",
        "## Human-source A→B relationships", "",
        "| Episode | Struggle (A) | Progress (B) | Link | Source IDs |",
        "|---|---|---|---|---|",
    ]
    for row in mapped["source_inventory"]["episodes"]:
        for link in row["a_to_b_links"]:
            lines.append(
                f"| {row['episode']} | {_clean(link['a_definition'])} | "
                f"{_clean(link['b_definition'])} | "
                f"{link['link']} ({link['basis']}) | "
                f"{', '.join(link['evidence_refs'])} |"
            )
    lines += ["", "## Provisional behavioral mechanism hypotheses", ""]
    for mechanism in mapped["mechanisms"]:
        lines += [
            f"### {mechanism['mechanism_id']}: {_clean(mechanism['condition'])}",
            "",
            f"**Hypothesis:** {mechanism['hypothesized_relationship']}",
            f"**Rival:** {mechanism['rival_explanation']}",
            f"**Change the condition:** {mechanism['counterfactual_condition_change']}",
            "",
            "| Episode | Interpretation | Human evidence | Caveat |",
            "|---|---|---|---|",
        ]
        for obs in mechanism["observations"]:
            caveat = (
                "Includes reported behavior/observation"
                if obs["behavior_observed_in_sources"] else
                "No concrete-behavior source type in cited evidence"
            ) if obs["stance"] != "UNASSESSED" else "Not assessed, not negative"
            lines.append(
                f"| {obs['episode']} | {obs['stance']}: "
                f"{_clean(obs['interpretation'])} | "
                f"{', '.join(obs['evidence_refs']) or '—'} | "
                f"{_clean(caveat)} |"
            )
        lines += [
            "", f"**Disconfirming observation:** {mechanism['disconfirming_observation']}",
            f"**Smallest discriminating human test:** {mechanism['discriminating_human_test']}",
            f"**Revisit when:** {mechanism['revisit_when']}", "",
        ]
    lines += [
        "## Research and inference boundaries", "",
    ]
    lines.extend(f"- {line}" for line in mapped["limitations"])
    lines += [
        "", "Use the proposed Planning Skills handoff only after explicit human acceptance. "
        "It may inform Working x, y, and operating model M; it cannot set accepted "
        "requirements, select a shape, or authorize a build.", "",
    ]
    return "\n".join(lines)


def planning_handoff(mapped: dict[str, Any]) -> dict[str, Any]:
    """Produce a proposed x/y/M research handoff, not an accepted planning artifact."""
    if mapped.get("artifact_type") != "BEHAVIORAL_MECHANISM_MAP":
        raise SimulationError("Expected compiled behavioral mechanism map")
    links = [
        link for ep in mapped["source_inventory"]["episodes"]
        for link in ep["a_to_b_links"]
    ]
    conditions = []
    for mechanism in mapped["mechanisms"]:
        cited = sorted({
            eid for obs in mechanism["observations"]
            for eid in obs["evidence_refs"]
        })
        conditions.append({
            "research_ref": f"SID:{mapped['study_id']}:{mechanism['mechanism_id']}",
            "authority": "PROPOSED",
            "claim_type": "HYPOTHESIZED_OPERATING_RELATIONSHIP",
            "condition": mechanism["condition"],
            "hypothesis": mechanism["hypothesized_relationship"],
            "rival": mechanism["rival_explanation"],
            "source_evidence_refs": [
                f"SID:{mapped['study_id']}:{eid}" for eid in cited
            ],
            "disconfirming_observation": mechanism["disconfirming_observation"],
            "revisit_when": mechanism["revisit_when"],
        })
    return {
        "schema_version": "1.0",
        "handoff_type": "RESEARCH_TO_PLANNING_PROPOSAL",
        "status": "PROPOSED",
        "acceptance_gate": "HUMAN_ACCEPTANCE_REQUIRED",
        "source_checkpoint_sha256": mapped["source_checkpoint_sha256"],
        "source_study": mapped["study_id"],
        "source_map_sha256": sha256_text(json.dumps(mapped, sort_keys=True)),
        "x_current_struggles_candidates": sorted({
            link["a_definition"] for link in links
        }),
        "y_desired_progress_candidates": sorted({
            link["b_definition"] for link in links
        }),
        "f_solution_variable": "UNSPECIFIED",
        "M_operating_model": {
            "authority": "PROPOSED",
            "conditions_and_hypotheses": conditions,
        },
        "uncertainties": [
            "Researcher annotations and A-to-B links require planning-level review.",
            "No behavior model is an established causal law.",
        ] + mapped["limitations"],
        "next_move_after_acceptance": (
            "Use framing-doc to establish x/y if unclear; otherwise use collaborative "
            "shaping to consider these as Working x, y and M inputs. "
            "No auto-selection or build authorization."
        ),
    }
