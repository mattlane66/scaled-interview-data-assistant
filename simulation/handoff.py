"""Export the exact v0.1.0 file contract of the companion Behavioral Simulation skill.

The companion repository is methodology and a file-backed skill, not a stable Python API.
No code is executed from the companion repository. An explicit contract version is pinned.
"""
from __future__ import annotations

import json
from typing import Any

from simulation.core import SimulationError, sha256_text

PROTOCOL_COMMIT = "c11d29c8d121728306037dd799669bb0ef7cfabf"
PROTOCOL_SCHEMA_VERSION = "0.1.0"


def protocol_input(scenario: dict[str, Any]) -> dict[str, Any]:
    baseline = scenario["baseline"]
    intervention = scenario["intervention"]
    if not scenario["episode_refs"] or not scenario["evidence_refs"]:
        raise SimulationError("Handoff requires reviewed episode and evidence references")
    return {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "decision": scenario["decision"],
        "population": scenario["target"],
        "baseline": (
            f"Path Y: {baseline['path_y']}; observed result: {baseline['observed_result']}; "
            f"evidence: {', '.join(baseline['evidence_refs']) or 'UNKNOWN'}"
        ),
        "scenario": (
            f"Change {intervention['variable']} from {intervention['from']} "
            f"to {intervention['to']}; hold constant: "
            f"{', '.join(scenario['held_constant']) or 'none declared'}; "
            f"distance: {scenario['counterfactual_distance']}"
        ),
        "outcome_space": ", ".join(scenario["outcome_space"]),
        "mode": scenario["mode"],
        "target_grade": scenario["target_grade"],
        "time_context": scenario["time_context"],
        "consequence_if_wrong": scenario["consequence_if_wrong"],
        "input_provenance": {
            "decision": "USER_SUPPLIED",
            "population": "EXPLICITLY_PROVISIONAL",
            "baseline": (
                "USER_SUPPLIED" if baseline["evidence_refs"] else "EXPLICITLY_PROVISIONAL"
            ),
            "scenario": "USER_SUPPLIED",
            "outcome_space": "USER_SUPPLIED",
        },
    }


def protocol_runs(run: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    if (run.get("scenario_id") != scenario["scenario_id"]
            or run.get("scenario_sha256") != sha256_text(json.dumps(scenario, sort_keys=True))
            or run.get("evidence_type") != "SIMULATED_ESTIMATE"):
        raise SimulationError("Upstream handoff run is not bound to this scenario")
    evidence_refs = sorted({
        ref for item in run["responses"] for ref in item["evidence_refs"]
    })
    config = run["configuration"]
    seed = config.get("seed")
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, (int, str))):
        seed = str(seed)
    return {
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "entries": [{
            "id": run["run_id"],
            "ran_at": run["generated_at"],
            "mode": run["mode"],
            "model": run["model"],
            "model_version": run["model_version"],
            "configuration": json.dumps(config, sort_keys=True),
            "seed": seed,
            "sample_size": len(run["responses"]),
            "evidence_ids": evidence_refs,
            "estimate": {
                "evidence_type": "SIMULATED_ESTIMATE",
                "responses": run["responses"],
                "scenario_id": scenario["scenario_id"],
                "source_checkpoint_sha256": run["source_checkpoint_sha256"],
            },
            "notes": (
                "Source: Scaled Interview Data Assistant; grade: "
                f"{run['grade']}; source coverage: {run.get('source_coverage', ['UNKNOWN'])}. "
                "Not human observation or a calibrated population estimate."
            ),
        }],
    }
