"""Check the deterministic router on declared positive and adversarial cases.

Does not run an agent on a transcript or establish substantive human review.
"""

from __future__ import annotations

import json
from pathlib import Path

from plugin_runtime.research_router import route_research

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "routing-cases.json"


def evaluate(path: Path = CASES) -> dict:
    source = json.loads(path.read_text(encoding="utf-8"))
    assert source["corpus_status"] == (
        "ROUTING_METADATA_FIXTURES_NOT_BLIND_HUMAN_EVALUATION"
    )
    outcomes = []
    for case in source["cases"]:
        result = route_research(case["request"])
        routes = result["routes"]
        actual = [[r["method"], r["readiness"]] for r in routes]
        passed = actual == case["expected"] and all(
            r["execution"] == "NOT_EXECUTED_BY_ROUTER" for r in routes
        )
        outcomes.append({
            "case_id": case["id"],
            "passed": passed,
            "expected": case["expected"],
            "actual": actual,
        })
    return {
        "evaluation_kind": "DETERMINISTIC_ROUTER_FIXTURES",
        "model_agent_execution": "NOT_RUN",
        "real_unseen_human_transcript_scores": "NOT_AVAILABLE",
        "total": len(outcomes),
        "passed": sum(row["passed"] for row in outcomes),
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] == result["total"] else 1)
