"""Decision-facing counterfactual briefs grounded in reviewed A-to-B evidence.

The output separates human-source interpretations, analyst design hypotheses, and
external model simulations. It makes no causal or adoption estimates.
"""
from __future__ import annotations

import json
import re
from typing import Any

from simulation.core import (
    SimulationError,
    ensure_run_matches,
    inspect_scenario,
    schema_check,
    sha256_text,
)


def _evidence_ids(cell: object) -> set[str]:
    return {token for token in re.split(r"[,;/\s]+", str(cell or ""))
            if re.fullmatch(r"E[0-9]{3,}", token)}


def build_brief(
    checkpoint: dict[str, Any], digest: str,
    scenario: dict[str, Any], run: dict[str, Any],
) -> dict[str, Any]:
    """Create a provenance-bound brief; do not mutate human registries."""
    info = inspect_scenario(checkpoint, digest, scenario)
    ensure_run_matches(run, scenario, digest)
    if "design_hypothesis" not in scenario:
        raise SimulationError(
            "Declare design_hypothesis before approving the scenario and generating its run"
        )
    codes = {row["code"]: row["definition"] for row in checkpoint["codebook"]}
    chosen_episodes = set(scenario["episode_refs"])
    chosen_evidence = set(scenario["evidence_refs"])
    linked = []
    omitted = []
    for row in checkpoint["a_to_b_links"]:
        if row["episode"] not in chosen_episodes:
            continue
        refs = _evidence_ids(row.get("evidence"))
        if not refs <= chosen_evidence:
            omitted.append(row["link"])
            continue
        linked.append({
            "link": row["link"], "episode": row["episode"],
            "a_code": row["a_code"], "a_definition": codes[row["a_code"]],
            "b_code": row["b_code"], "b_definition": codes[row["b_code"]],
            "interpretation_basis": row.get("basis", "UNKNOWN"),
            "evidence_refs": sorted(refs),
            "rationale": row.get("rationale") or "UNKNOWN",
            "contradictions": row.get("contradictions") or "NONE RECORDED",
        })
    if not linked:
        raise SimulationError(
            "No reviewed A-to-B links have complete support in the selected evidence; "
            "extend the scenario evidence set or review a different episode"
        )
    cases = [{
        "episode": episode,
        "interview": info["episodes"][episode]["interview"],
        "descriptor": info["episodes"][episode].get("descriptor") or "UNKNOWN",
    } for episode in scenario["episode_refs"]]
    hypotheses = [{
        "candidate": i,
        "evidence_type": "SIMULATED_ESTIMATE",
        "generated_statement": response["text"],
        "hypothesized_mechanism": response["mechanism"],
        "source_evidence_refs": response["evidence_refs"],
        "objections": response["objections"],
        "proposed_human_test": response["next_test"],
    } for i, response in enumerate(run["responses"], start=1)]
    return {
        "schema_version": "1.0",
        "artifact_type": "COUNTERFACTUAL_DECISION_BRIEF",
        "scenario_id": scenario["scenario_id"], "run_id": run["run_id"],
        "source_checkpoint_sha256": digest,
        "scenario_sha256": sha256_text(json.dumps(scenario, sort_keys=True)),
        "run_sha256": sha256_text(json.dumps(run, sort_keys=True)),
        "evidence_type": "ANALYST_HYPOTHESIS_AND_SIMULATED_ESTIMATE",
        "evidence_grade": run["grade"],
        "decision": scenario["decision"],
        "decision_owner": scenario["decision_owner"],
        "consequence_if_wrong": scenario["consequence_if_wrong"],
        "target": scenario["target"],
        "episodes": cases,
        "evidence_refs": scenario["evidence_refs"],
        "coverage": info["coverage"],
        "reviewed_a_to_b_links": linked,
        "omitted_links_outside_scope": omitted,
        "baseline": scenario["baseline"],
        "intervention": scenario["intervention"],
        "held_constant": scenario["held_constant"],
        "outcome_space": scenario["outcome_space"],
        "counterfactual_distance": scenario["counterfactual_distance"],
        "design_hypothesis": scenario["design_hypothesis"],
        "analyst_assumptions": scenario["assumptions"],
        "simulated_hypotheses": hypotheses,
        "decision_status": "TEST_BEFORE_BUILD",
        "validation_status": "NOT_VALIDATED",
        "boundaries": [
            "A-to-B links are reviewed interpretations of human-source evidence, not causal proof.",
            "The product design hypothesis is analyst-supplied, not observed customer behavior.",
            "Simulated responses suggest rival explanations and tests, not intervention effects.",
            "No prevalence, calibrated probability, product ranking, or build recommendation.",
        ],
    }


def _inline(value: Any) -> str:
    """Keep data inside a Markdown table cell instead of creating new table rows."""
    return " ".join(str(value).replace("|", "\\|").split())


def render_brief(brief: dict[str, Any]) -> str:
    schema_check(brief, "counterfactual-brief.schema.json")
    design = brief["design_hypothesis"]
    change = brief["intervention"]
    lines = [
        "# Counterfactual product decision brief", "",
        f"**Decision:** {brief['decision']}",
        f"**Owner:** {brief['decision_owner']}",
        f"**Status:** {brief['decision_status']} — {brief['validation_status']}",
        f"**Evidence grade:** {brief['evidence_grade']}", "",
        "## 1. What the human research supports", "",
        f"Evidence checkpoint: \\u0060{brief['source_checkpoint_sha256']}\\u0060",
        f"Episodes: {', '.join(row['episode'] for row in brief['episodes'])}",
        f"Coverage: {', '.join(brief['coverage'])}", "",
        "| Observed struggle (A) | Hoped-for progress (B) | Support |",
        "|---|---|---|",
    ]
    for link in brief["reviewed_a_to_b_links"]:
        lines.append(
            f"| {_inline(link['a_code'] + ': ' + link['a_definition'])} | "
            f"{_inline(link['b_code'] + ': ' + link['b_definition'])} | "
            f"{_inline(link['link'] + ' / ' + link['interpretation_basis'] + ' / ' + ', '.join(link['evidence_refs']))} |"
        )
    lines += [
        "",
        "The A-to-B relationships above are reviewed interview interpretations, not "
        "proven causal relations.",
        "",
        f"**Current Path Y:** {brief['baseline']['path_y']}",
        f"**Observed Path X result:** {brief['baseline']['observed_result']}",
        f"**Baseline evidence:** {', '.join(brief['baseline']['evidence_refs']) or 'NONE'}",
    ]
    if brief["omitted_links_outside_scope"]:
        lines.append(
            "**Links not evaluated (their support lies outside the selected evidence):** "
            + ", ".join(brief["omitted_links_outside_scope"])
        )
    lines += [
        "", "## 2. The proposed change", "",
        f"**Design move:** {design['product_change']}",
        f"**Changed condition:** {change['variable']}: "
        f"{change['from']} → {change['to']}",
        f"**Held constant:** {', '.join(brief['held_constant']) or 'NOT SPECIFIED'}",
        f"**Counterfactual distance:** {brief['counterfactual_distance']}",
        "",
        "## 3. The assumption that could change the product design", "",
        f"**Critical assumption (analyst hypothesis):** {design['critical_assumption']}",
        f"**Expected behavioral difference (not a prediction):** {design['predicted_behavior']}",
        f"**Disconfirming observation:** {design['disconfirming_observation']}",
        f"**If disconfirmed, change direction to:** {design['if_disconfirmed']}",
        "",
        "## 4. Rival explanations suggested by simulation", "",
    ]
    for item in brief["simulated_hypotheses"]:
        lines += [
            f"### Candidate {item['candidate']} — SIMULATED, NOT OBSERVED", "",
            f"**Proposed mechanism:** {item['hypothesized_mechanism']}",
            f"**Human evidence references supplied:** "
            f"{', '.join(item['source_evidence_refs']) or 'NONE'}",
            f"**Potential objections:** {'; '.join(item['objections']) or 'NONE'}",
            f"**Discriminating human test:** {item['proposed_human_test']}",
            "",
        ]
    lines += [
        "## 5. Decision rule", "",
        "**TEST BEFORE BUILD.** Investigate the critical assumption with human behavior. "
        "Do not infer a causal effect or choose the winning product from the generated text.",
        "",
        f"**Consequence if wrong:** {brief['consequence_if_wrong']}",
        "", "Grounding and all generated artifacts are bound to the source checkpoint, "
        "scenario, and run hashes. This does not make generated claims true.", "",
    ]
    return "\n".join(lines)


def compare_briefs(briefs: list[dict[str, Any]]) -> str:
    """Compare alternative design moves on one grounded decision, without rankings."""
    if len(briefs) < 2:
        raise SimulationError("Compare at least two counterfactual briefs")
    for brief in briefs:
        schema_check(brief, "counterfactual-brief.schema.json")
    first = briefs[0]
    ids = [brief["scenario_id"] for brief in briefs]
    if len(ids) != len(set(ids)):
        raise SimulationError("Counterfactuals must have distinct approved scenario IDs")
    invariant_fields = [
        "source_checkpoint_sha256", "decision", "target", "episodes",
        "evidence_refs", "baseline", "outcome_space",
    ]
    for brief in briefs[1:]:
        if any(brief[field] != first[field] for field in invariant_fields):
            raise SimulationError(
                "Alternative interventions must use identical human evidence, "
                "decision, baseline, and outcomes"
            )
    lines = [
        "# Product counterfactual comparison", "",
        f"**Decision:** {first['decision']}",
        f"**Grounded episodes:** {', '.join(x['episode'] for x in first['episodes'])}",
        "**Status:** COMPARATIVE HYPOTHESES — NOT VALIDATED", "",
        "| Design alternative | Changed condition | Critical assumption | Disconfirmation test |",
        "|---|---|---|---|",
    ]
    for brief in briefs:
        design = brief["design_hypothesis"]
        intervention = brief["intervention"]
        lines.append(
            f"| {_inline(brief['scenario_id'] + ': ' + design['product_change'])} | "
            f"{_inline(intervention['variable'] + ': ' + intervention['from'] + ' → ' + intervention['to'])} | "
            f"{_inline(design['critical_assumption'])} | "
            f"{_inline(design['disconfirming_observation'])} |"
        )
    constants = [brief["held_constant"] for brief in briefs]
    if any(value != constants[0] for value in constants[1:]):
        lines += [
            "", "**Comparability warning:** held-constant conditions differ between alternatives. "
            "Do not interpret contrasts as controlled causal effects."
        ]
    lines += [
        "", "These are separate, evidence-grounded design hypotheses, not measured",
        "treatment effects, forecasts, or an automatic product ranking.",
        "Choose the next human test by the consequence of a wrong assumption and",
        "whether the test can distinguish competing mechanisms—not simulated popularity.",
        "",
    ]
    return "\n".join(lines)
