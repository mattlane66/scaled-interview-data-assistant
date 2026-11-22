"""Audit a real published-source research pilot without certifying the findings.

The published full transcripts are not reproduced here. Source-located
paraphrases support an authored A->B pilot, not a blind evaluation or human
evidence adjudication.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.score_agent_research import assess

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "evals" / "real-source-pilot"


def load(name: str) -> dict:
    return json.loads((PILOT / name).read_text(encoding="utf-8"))


def evaluate() -> dict:
    manifest = load("manifest.json")
    ledger = load("evidence-ledger.json")
    analyses = load("case-analyses.json")
    keys = load("provisional-keys.json")
    outputs = load("candidate-agent-outputs.json")
    assessment = load("method-assessment.json")

    assert manifest["status"] == "CURRENT_GPT6_ANALYST_PILOT_NOT_BLIND_OR_INDEPENDENT"
    assert manifest["independent_native_codex_runs"] == 0
    assert manifest["independent_native_claude_runs"] == 0
    assert manifest["independent_human_adjudications"] == 0
    assert manifest["validated_simulation_holdouts"] == 0
    assert manifest["qualified_lead_users"] == 0
    assert manifest["source_material_republished"] is False
    assert manifest["source_coverage"].startswith("PARTIAL")
    assert len(manifest["sources"]) == 2

    sources = {source["id"]: source for source in manifest["sources"]}
    assert len(sources) == 2
    assert len({s["url"] for s in sources.values()}) == 2
    assert all(s["url"].startswith("https://") for s in sources.values())
    assert all("copyright" in s["licensing"].lower() for s in sources.values())

    rows = {row["id"]: row for row in ledger["evidence"]}
    assert len(rows) == len(ledger["evidence"]) >= 20
    for row in rows.values():
        assert row["source_id"] in sources
        assert row["evidence_basis"] == "REPORTED_HUMAN_STATEMENT"
        assert row["source_authentication"].startswith("PUBLISHED_SOURCE_EXISTENCE")
        assert row["participant_paraphrase"].strip()
        assert row["locator"]["web_render_line_start"] > 0
        assert row["locator"]["web_render_line_end"] >= (
            row["locator"]["web_render_line_start"]
        )

    cases = {case["id"]: case for case in analyses["cases"]}
    references = {key["case_id"]: key for key in keys["references"]}
    artifacts = {art["case_id"]: art for art in outputs["outputs"]}
    assert len(cases) == len(references) == len(artifacts) == 2
    assert set(cases) == set(references) == set(artifacts)

    checks = []
    for cid, case in cases.items():
        assert case["status"] == "PROVISIONAL_PARTIAL_SOURCE_REVIEW"
        assert case["source"] in sources
        assert case["method"] == "A2B"
        assert case["a"] and case["path_y"] and case["baseline"]
        assert case["tipping"] and case["path_x"] and case["desired_b"]
        assert case["reported_result"] and case["unknowns"]
        assert case["contradictions"]
        assert set(case["forces"]) == {"push", "pull", "anxiety", "inertia"}
        own = {
            eid for eid, row in rows.items()
            if row["source_id"] == case["source"]
        }
        assert set(case["evidence_refs"]) <= own
        for force in case["forces"].values():
            assert force["summary"]
            assert force["evidence_refs"]
            assert set(force["evidence_refs"]) <= own
        ref = references[cid]
        assert not ref["independent_human_gold_standard"]
        assert not ref["human_review_authorized"]
        assert set(ref["allowed_source_refs"]) <= own
        assert set(ref["required_unknowns"]) == set(case["unknowns"])
        for claim in artifacts[cid]["claims"]:
            assert set(claim["evidence_refs"]) <= own
        scored = assess(ref, artifacts[cid])
        assert scored["structural_status"] == "PASS", scored["errors"]
        assert scored["semantic_accuracy"] == "HUMAN_REVIEW_REQUIRED"
        checks.append({
            "case_id": cid,
            "score_kind": "STRUCTURAL_ONLY",
            "passed": True,
            "semantic_independent_review": "NOT_RUN",
        })
    status = {item["method"]: item["status"] for item in assessment["methods"]}
    assert status["A2B"].startswith("PROVISIONAL")
    assert status["BEHAVIORAL_MECHANISM_MAP"] == (
        "NOT_ELIGIBLE_AS_REVIEWED_SAME_JOB_MAP"
    )
    assert status["BEHAVIORAL_SIMULATION"] == "NOT_EXECUTED"
    assert status["LEAD_USER_RESEARCH"] == "NOT_EXECUTED"

    return {
        "status": "SOURCE_LINKED_SELF_PILOT_STRUCTURALLY_CHECKED",
        "cases": len(cases),
        "source_evidence_rows": len(rows),
        "structural_passed": len(checks),
        "independent_human_verification": "NOT_DONE",
        "native_codex_qualitative_evaluation": "NOT_RUN",
        "native_claude_qualitative_evaluation": "NOT_RUN",
        "methods_executed": ["A2B_PROVISIONAL"],
        "results": checks,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
