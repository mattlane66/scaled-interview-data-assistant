"""Create a decision-facing report without promoting synthetic claims to human evidence."""
from __future__ import annotations

import json
from typing import Any

from simulation.core import SimulationError, sha256_text


def render(
    scenario: dict[str, Any],
    run: dict[str, Any],
    measurement: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
) -> str:
    if run.get("scenario_id") != scenario["scenario_id"]:
        raise SimulationError("Report scenario/run mismatch")
    if run.get("scenario_sha256") != sha256_text(json.dumps(scenario, sort_keys=True)):
        raise SimulationError("The approved scenario has changed since this run")
    if run.get("evidence_type") != "SIMULATED_ESTIMATE":
        raise SimulationError("Run does not declare generated estimate evidence type")
    if run.get("mode") != scenario["mode"] or run.get("grade") != scenario["target_grade"]:
        raise SimulationError("Report cannot promote or alter simulation mode or evidence grade")
    if measurement and measurement.get("run_sha256") != sha256_text(
        json.dumps(run, sort_keys=True)
    ):
        raise SimulationError("SSR measurement belongs to another run")
    if validation and validation.get("run_id") != run.get("run_id"):
        raise SimulationError("Validation belongs to another run")

    lines = [
        "# Evidence-grounded simulation report",
        "",
        f"**Scenario:** {scenario['scenario_id']} | **Run:** {run['run_id']}",
        f"**Question:** {scenario['decision']}",
        f"**Owner:** {scenario['decision_owner']}",
        f"**Mode:** {run['mode']} | **Evidence grade:** {run['grade']}",
        "**Source type:** SIMULATED_ESTIMATE (never OBSERVED_HUMAN)",
        "",
        "## Observed grounding and assumptions",
        "",
        f"- Read-only checkpoint: `{scenario['source_checkpoint_sha256']}`",
        f"- Human episode references: {', '.join(scenario['episode_refs'])}",
        f"- Source evidence IDs: {', '.join(scenario['evidence_refs'])}",
        f"- Coverage: {', '.join(run.get('source_coverage', ['UNKNOWN']))}"
        + (" (**LIMITED**)" if run.get("coverage_limited", True) else ""),
        f"- Baseline evidence IDs: "
        f"{', '.join(scenario['baseline']['evidence_refs']) or 'NONE — ASSUMPTION'}",
        f"- Baseline Path Y: {scenario['baseline']['path_y']}",
        f"- Observed Path X result: {scenario['baseline']['observed_result']}",
        f"- Changed: {scenario['intervention']['variable']} "
        f"({scenario['intervention']['from']} → {scenario['intervention']['to']})",
        f"- Held constant: {', '.join(scenario['held_constant']) or 'NONE DECLARED'}",
        f"- Counterfactual distance: {scenario['counterfactual_distance']}",
        "- Assumptions: " + ("; ".join(scenario["assumptions"]) or "NONE LISTED"),
        "",
        "## Simulated possibilities (not actual customer responses)",
        "",
    ]
    for i, item in enumerate(run["responses"], start=1):
        lines.extend([
            f"### Candidate {i}",
            "",
            "**Generated statement:**",
            *["> " + line for line in item["text"].replace("\r", "").split("\n")],
            "",
            f"**Hypothesized mechanism:** {item['mechanism']}",
            f"**Grounding cited:** {', '.join(item['evidence_refs']) or 'NONE'}",
            f"**Objections:** {'; '.join(item['objections']) or 'NONE'}",
            f"**Next human test:** {item['next_test']}",
            "",
        ])
    lines += ["## Quantitative measurement", ""]
    if measurement:
        lines += [
            f"Predeclared question: {scenario['measurement']['question']}",
            f"Construct: {measurement['construct']}; externally supplied embeddings: "
            f"{measurement['embedding_model']}; anchors: {measurement['anchor_version']}.",
            "",
            "Generated-response ordinal rating distribution (1–5): "
            + ", ".join(f"{p:.4f}" for p in measurement["aggregate"]),
            "",
            "**Not** a calibrated population adoption or switching probability.",
        ]
    else:
        lines.append("Not measured. SSR is optional and requires externally generated embeddings.")
    lines += ["", "## Held-out validation", ""]
    if validation:
        lines += [
            f"Status: {validation['validation_status']}",
            f"Person-grouped n={validation['holdout_size']}; TVD={validation['tvd']:.4f}; "
            f"naive baseline TVD={validation['baseline_tvd']:.4f}; "
            f"KS similarity={validation['ks_similarity']:.4f}.",
            "**This comparison does not automatically authorize L3 or decision-grade confidence.**",
        ]
    else:
        lines.append("NOT VALIDATED: no real held-out outcomes evaluated.")
    lines += [
        "", "## Decision boundary", "",
        "Use these outputs to select a real interview, prototype, or experiment; "
        "not as new A/B codes, observed switching facts, population prevalence, "
        "causal treatment effects, willingness to pay, or a business decision.",
        "",
        "Human evidence establishes what happened; simulation explores what might happen; "
        "independent validation is needed to establish predictive performance.",
        "",
    ]
    return "\n".join(lines)
