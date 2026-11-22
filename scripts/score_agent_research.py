"""Score structural agent research artifacts against a separately maintained case key.

This audits method selection, claim provenance, known unknowns and prohibited
evidence promotion; only independent human review can establish substantive
claim relevance or interpretation quality.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

METHODS = {
    "A2B", "BEHAVIORAL_MECHANISM_MAP",
    "BEHAVIORAL_SIMULATION", "LEAD_USER_RESEARCH", "OTHER_METHOD",
}
CLAIM_KINDS = {"REPORTED", "INFERRED", "SPECULATIVE", "UNKNOWN", "SIMULATED_ESTIMATE"}
RUBRIC = (
    "source_accuracy", "chronology", "method_fidelity",
    "contradictions", "decision_usefulness",
)


def assess(reference: dict, artifact: dict, human_review: dict | None = None) -> dict:
    """Assess source ID consistency, not whether the cited text proves a claim."""
    errors: list[str] = []
    if reference.get("case_id") != artifact.get("case_id"):
        errors.append("CASE_ID_MISMATCH")
    expected = set(reference.get("expected_methods", []))
    actual = artifact.get("selected_methods", [])
    if len(set(actual)) != len(actual) or not set(actual) <= METHODS:
        errors.append("INVALID_METHOD_SET")
    if set(actual) != expected:
        errors.append("METHOD_SELECTION_MISMATCH")
    allowed_refs = set(reference.get("allowed_source_refs", []))
    for i, claim in enumerate(artifact.get("claims", [])):
        kind = claim.get("kind")
        refs = claim.get("evidence_refs", [])
        if kind not in CLAIM_KINDS:
            errors.append(f"INVALID_CLAIM_KIND:{i}")
        if not isinstance(refs, list) or any(ref not in allowed_refs for ref in refs):
            errors.append(f"FOREIGN_SOURCE_REF:{i}")
        if kind in {"REPORTED", "INFERRED"} and not refs:
            errors.append(f"UNSUPPORTED_MATERIAL_CLAIM:{i}")
        if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
            errors.append(f"EMPTY_CLAIM:{i}")
    for tag in reference.get("required_unknowns", []):
        if tag not in artifact.get("unknowns", []):
            errors.append(f"OMITTED_CRITICAL_UNKNOWN:{tag}")
    if artifact.get("human_review_claimed") and not reference.get(
        "human_review_authorized", False
    ):
        errors.append("UNAUTHORIZED_HUMAN_REVIEW_CLAIM")
    if artifact.get("qualified_lead_users_claimed") and not reference.get(
        "qualified_lead_users_authorized", False
    ):
        errors.append("UNSUPPORTED_LEAD_USER_QUALIFICATION")
    if artifact.get("validated_prediction_claimed") and not reference.get(
        "validated_prediction_authorized", False
    ):
        errors.append("UNSUPPORTED_PREDICTIVE_VALIDATION")
    if not artifact.get("next_research_move"):
        errors.append("MISSING_NEXT_RESEARCH_MOVE")
    reviewer_result = "NOT_RUN"
    scores = None
    if human_review is not None:
        if human_review.get("case_id") != reference.get("case_id"):
            errors.append("REVIEW_CASE_MISMATCH")
        if not human_review.get("reviewer"):
            errors.append("MISSING_REVIEWER")
        scores = human_review.get("scores") or {}
        if set(scores) != set(RUBRIC) or any(
            not isinstance(scores[key], int) or isinstance(scores[key], bool)
            or not 0 <= scores[key] <= 4 for key in RUBRIC if key in scores
        ):
            errors.append("INVALID_HUMAN_RUBRIC")
        else:
            reviewer_result = "REVIEW_SUBMITTED_INDEPENDENCE_NOT_VERIFIED"
    return {
        "case_id": reference.get("case_id"),
        "structural_status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "semantic_accuracy": "HUMAN_REVIEW_REQUIRED",
        "human_scoring": reviewer_result,
        "human_scores": scores,
        "independent_blind_agent_execution": "NOT_ESTABLISHED_BY_THIS_SCORER",
        "note": (
            "Correct reference IDs and rubric values do not independently "
            "prove source interpretation, study completeness or model validity."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--human-review", type=Path)
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    review = (json.loads(args.human_review.read_text(encoding="utf-8"))
              if args.human_review else None)
    result = assess(reference, artifact, review)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["structural_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
