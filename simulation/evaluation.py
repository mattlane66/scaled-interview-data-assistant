"""Conservative held-out SSR assessment; metrics do not automatically promote a grade."""
from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any

from simulation.core import SimulationError, schema_check, sha256_text


def _normalize(values: list[float]) -> list[float]:
    if (len(values) != 5 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                or not math.isfinite(v) or v < 0 for v in values)):
        raise SimulationError("Rating distribution must contain five finite nonnegative values")
    total = math.fsum(values)
    if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-6):
        raise SimulationError("Input distribution must sum to one")
    return [float(v) / total for v in values]


def tvd(a: list[float], b: list[float]) -> float:
    p, q = _normalize(a), _normalize(b)
    return 0.5 * math.fsum(abs(x - y) for x, y in zip(p, q, strict=True))


def ks_similarity(a: list[float], b: list[float]) -> float:
    p, q = _normalize(a), _normalize(b)
    ap = bp = 0.0
    dist = 0.0
    for x, y in zip(p, q, strict=True):
        ap += x
        bp += y
        dist = max(dist, abs(ap - bp))
    return 1 - dist


def assess(
    checkpoint: dict[str, Any], scenario: dict[str, Any],
    run: dict[str, Any], measurement: dict[str, Any],
    holdout: dict[str, Any],
) -> dict[str, Any]:
    schema_check(holdout, "holdout.schema.json")
    if (holdout["run_id"] != run.get("run_id")
            or measurement.get("run_id") != run.get("run_id")
            or measurement.get("run_sha256") != sha256_text(json.dumps(run, sort_keys=True))):
        raise SimulationError("Holdout or measurement is bound to a different run")
    if holdout["construct"] != measurement.get("construct"):
        raise SimulationError("Validation construct does not match SSR measurement")
    if not holdout["collection_and_use_permitted"] or not holdout["held_out_attested"]:
        raise SimulationError("Human holdout permission and isolation must be attested")
    if datetime.fromisoformat(holdout["predeclared_at"].replace("Z", "+00:00")) >= (
        datetime.fromisoformat(run["generated_at"].replace("Z", "+00:00"))
    ):
        raise SimulationError("The holdout method must be declared before generation")
    if holdout["split_unit"] != "PERSON":
        raise SimulationError("v1 supports PERSON-grouped holdouts only")
    # Block overlap with the *whole* input checkpoint, not just selected scenario episodes.
    grounded = {r["interview"] for r in checkpoint["interview_index"]}
    held_out = set(holdout["holdout_group_ids"])
    if len(holdout["holdout_group_ids"]) != len(holdout["observed_ratings"]):
        raise SimulationError("Provide exactly one response per person-group ID")
    if grounded & held_out:
        raise SimulationError("Holdout participants overlap source checkpoint interviews")
    observed = [holdout["observed_ratings"].count(i) / len(holdout["observed_ratings"])
                for i in range(1, 6)]
    predicted = _normalize(measurement["aggregate"])
    baseline = _normalize(holdout["baseline_distribution"])
    return {
        "schema_version": "1.0",
        "validation_id": holdout["validation_id"], "run_id": run["run_id"],
        "scenario_id": scenario["scenario_id"],
        "construct": holdout["construct"], "correctness_unit": "DISTRIBUTION",
        "split_unit": "PERSON", "holdout_size": len(holdout["observed_ratings"]),
        "split_group_count": len(held_out),
        "source": holdout["source"], "predeclared_at": holdout["predeclared_at"],
        "actual": observed, "predicted": predicted, "baseline": baseline,
        "tvd": tvd(predicted, observed),
        "baseline_tvd": tvd(baseline, observed),
        "ks_similarity": ks_similarity(predicted, observed),
        "baseline_ks_similarity": ks_similarity(baseline, observed),
        "validation_status": "HOLDOUT_ATTESTED_NOT_INDEPENDENTLY_VERIFIED",
        "grade_after_validation": run["grade"],
        "limitations": [
            "External holdout independence and response provenance are attested, not proven.",
            "Distributional fidelity does not establish individual accuracy or behavior change.",
            "No L3/L4 promotion without independently checked leakage, baseline, subgroup, "
            "model freeze, decision threshold, and calibration where applicable.",
        ],
    }
