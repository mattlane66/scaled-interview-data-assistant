"""Audit the real-source canonical mattress casebook without certifying interpretations.

This checks ownership, provenance, evidentiary status, and actual recorded SSR
arithmetic. It DOES NOT verify the truth of public self-reports, complete human
research review, causal effects, or predictive validity. Run from any cwd.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "canonical-mattress"
EXT = BASE / "empirical-extension"
STATUSES = {"ALIGNS", "COUNTEREXAMPLE", "AMBIGUOUS", "UNASSESSED"}


def read(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def audit() -> dict:
    ledger = read(EXT / "source-ledger.json")
    casebook = read(EXT / "casebook.json")
    original_evidence = read(BASE / "evidence_bank.json")
    original_checkpoint = read(BASE / "results" / "CHECKPOINT.json")
    expected = read(BASE / "reference" / "expected-analysis.json")
    recode = read(EXT / "proposed-core-recode.json")
    original_codes = read(BASE / "codebook.json")
    original_links = read(BASE / "links.json")
    assert recode["status"] == "PROPOSED_NOT_APPLIED"
    assert recode["human_evidence_review"] == "NOT_DONE"
    assert {row["code"] for row in recode["code_proposals"]} == {
        row["code"] for row in original_codes
    }
    assert {row["link"] for row in recode["link_proposals"]} == {
        row["link"] for row in original_links
    }
    assert recode["distinct_roles"]["actual_result"].startswith("UNKNOWN")

    assert expected["status"] == "AI_AUDITED_CANDIDATE_PENDING_HUMAN_ADJUDICATION"
    assert ledger["execution_level"] == "DESK_RESEARCH"
    assert ledger["human_review"] == "NOT_REVIEWED"
    assert ledger["independently_conducted_interviews"] == 0
    assert ledger["human_holdouts"] == 0
    assert ledger["verified_behavioral_outcomes"] == 0
    assert ledger["main_interview_checkpoint_policy"] == "UNCHANGED"
    assert casebook["review_status"] == "NOT_HUMAN_REVIEWED"
    assert casebook["methods"]["mechanism_map"]["reviewed_compiler_run"] is False
    assert casebook["methods"]["simulation_ssr"]["human_holdout_present"] is False
    assert casebook["methods"]["lead_user"]["qualified_episodes"] == 0
    assert casebook["methods"]["lead_user"]["completed_field_interviews"] == 0
    assert casebook["methods"]["lead_user"]["evidence_freeze"] == "NOT_PERFORMED"
    assert casebook["integrated_research_decision"]["authorized_product_choice"] == "NONE"
    assert original_checkpoint and expected["source_grain"]["interviews"] == 1
    assert len(original_evidence) == 28

    sources = {s["id"]: s for s in ledger["sources"]}
    assert len(sources) == len(ledger["sources"]) >= 12
    assert all(s["url"].startswith("https://") and s["locator"] for s in sources.values())
    assert sources["P12"]["kind"] == "ORIGINAL_INDUSTRY_ASSOCIATION_SURVEY_REPORT"
    accounts = {p["id"]: p for p in ledger["public_accounts"]}
    assert len(accounts) == len(ledger["public_accounts"]) == 7
    evidence_owner: dict[str, str] = {}
    for p in accounts.values():
        assert p["source_id"] in sources
        assert p["lead_user_qualification"] != "QUALIFIED"
        for claim in p["observations"]:
            ref = claim["id"]
            assert ref.startswith("RE") and ref not in evidence_owner
            assert claim["kind"].startswith("REPORTED_")
            evidence_owner[ref] = p["id"]

    source_evidence = {e["evidence"] for e in original_evidence}
    assert len(source_evidence) == 28
    episodes = {e["id"]: e for e in casebook["episodes"]}
    assert len(episodes) == len(casebook["episodes"]) == 8
    assert sum(e["account_id"] == "CORE" for e in episodes.values()) == 1
    assert {e["account_id"] for e in episodes.values()} == {"CORE"} | set(accounts)
    for e in episodes.values():
        assert e["source_id"] == (
            "P01" if e["account_id"] == "CORE" else accounts[e["account_id"]]["source_id"]
        )
        assert e["analyst_status"] == "PROVISIONAL_INTERPRETATION"
        assert e["desired_progress"] and e["reported_outcome"] and e["unresolved"]
        for ref in e["evidence_refs"]:
            if e["account_id"] == "CORE":
                assert ref in source_evidence
            else:
                assert evidence_owner[ref] == e["account_id"]

    mechanisms = {m["id"]: m for m in casebook["mechanisms"]}
    assert len(mechanisms) == len(casebook["mechanisms"]) == 4
    matrix = {}
    for m in mechanisms.values():
        assert m["rival"] and m["falsifier"] and m["minimal_test"]
        assert m["status"].startswith("PROVISIONAL")
        records = {row["episode_id"]: row for row in m["case_assessments"]}
        assert len(records) == len(m["case_assessments"]) == len(episodes)
        assert set(records) == set(episodes)
        assert len({row["reason"] for row in records.values()}) >= 6
        for eid, row in records.items():
            assert row["relationship"] in STATUSES
            assert row["reason"] and set(row["evidence_refs"]) <= set(
                episodes[eid]["evidence_refs"]
            )
        matrix[m["id"]] = dict(sorted(Counter(
            row["relationship"] for row in records.values()
        ).items()))

    lead = casebook["lead_user_scout"]
    assert lead["evidence_freeze"] == "NOT_PERFORMED"
    assert lead["decision_status"] != "QUALIFIED"
    assert len(lead["candidates"]) >= 3
    for t in lead["trend_candidates"]:
        assert t["status"] != "PROVEN_FORECAST"
        assert set(t["source_ids"]) <= set(sources)
    for c in lead["candidates"]:
        assert c["status"] == "UNQUALIFIED"
        assert c["account_id"] in accounts
        assert c["episode_id"] in episodes
        assert episodes[c["episode_id"]]["account_id"] == c["account_id"]
        assert c["lu1"] and c["lu2"]
    assert all(c["status"] != "SUPPORTED" for c in lead["transfer_hypotheses"])

    measures = []
    for scenario in casebook["model_challenge"]["counterfactuals"]:
        assert scenario["text_origin"] == "TWO_AUTHORED_L0_RESPONSES"
        measurement = read((EXT / scenario["ssr_path"]).resolve())
        assert measurement["evidence_type"] == "SIMULATED_ESTIMATE"
        assert measurement["anchor_set_count"] == 6
        assert len(measurement["per_response"]) == 2
        assert measurement["embedding_model"] == "BAAI/bge-small-en-v1.5"
        p = measurement["aggregate"]
        assert len(p) == 5 and all(0 <= x <= 1 for x in p)
        assert math.isclose(sum(p), 1.0, abs_tol=1e-9)
        score = math.fsum((i + 1) * value for i, value in enumerate(p))
        assert all(c["episode_id"] in episodes for c in scenario["human_challenges"])
        measures.append({"scenario": scenario["id"], "ordinal_text_mean": round(score, 6),
                         "generated_response_count": len(measurement["per_response"])})
    assert casebook["model_challenge"]["validation_design"][
        "actual_holdout_observations"
    ] == 0
    assert casebook["model_challenge"]["validation_design"][
        "validation_status"
    ] == "NOT_VALIDATED"
    assert math.isclose(measures[0]["ordinal_text_mean"], 3.201355, abs_tol=1e-5)
    assert math.isclose(measures[1]["ordinal_text_mean"], 2.979906, abs_tol=1e-5)

    return {
        "structural_audit": "PASSED",
        "substantive_human_review": "NOT_DONE",
        "source_self_reports_independently_verified": False,
        "original_checkpoint_unchanged": True,
        "account_histories": len(episodes),
        "external_account_histories": len(accounts),
        "source_records": len(sources),
        "cross_case_hypotheses": matrix,
        "ssr": measures,
        "human_holdouts": 0,
        "qualified_lead_user_episodes": 0,
        "predictive_or_causal_validation": "NOT_DONE",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
