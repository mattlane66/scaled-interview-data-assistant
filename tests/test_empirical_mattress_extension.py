"""Guard the canonical extension against invented completion and source mixing."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "canonical-mattress" / "empirical-extension"


def test_empirical_scout_has_sources_without_fake_fieldwork():
    data = json.loads((BASE / "source-ledger.json").read_text(encoding="utf-8"))
    assert data["execution_level"] == "DESK_RESEARCH"
    assert data["human_review"] == "NOT_REVIEWED"
    assert data["independently_conducted_interviews"] == 0
    assert data["human_holdouts"] == 0
    assert data["verified_behavioral_outcomes"] == 0
    assert data["main_interview_checkpoint_policy"] == "UNCHANGED"
    assert data["methodology_guards"]["no_qualified_lead_users"] is True

    source_ids = {s["id"] for s in data["sources"]}
    assert len(source_ids) == len(data["sources"])
    assert len(source_ids) >= 7
    for source in data["sources"]:
        parsed = urlparse(source["url"])
        assert parsed.scheme == "https" and parsed.netloc and not parsed.username
        assert source["locator"].strip()
    for context in data["contextual_claims"]:
        assert context["source_id"] in source_ids
        assert context["limit"].strip()
    people = {a["id"] for a in data["public_accounts"]}
    assert len(people) == len(data["public_accounts"]) >= 4
    evidence = set()
    for account in data["public_accounts"]:
        assert account["source_id"] in source_ids
        assert account["lead_user_qualification"] != "QUALIFIED"
        assert account["source_locator"].strip()
        for item in account["observations"]:
            assert item["id"] not in evidence
            evidence.add(item["id"])
            assert item["kind"].startswith("REPORTED_")
            assert item["paraphrase"].strip()


def test_empirical_scout_keeps_canonical_core_unchanged_and_unapproved():
    actual = json.loads(
        (ROOT / "examples/canonical-mattress/reference/expected-analysis.json")
        .read_text(encoding="utf-8")
    )
    assert actual["status"] == "AI_AUDITED_CANDIDATE_PENDING_HUMAN_ADJUDICATION"
    assert actual["source_grain"]["interviews"] == 1
    assert actual["source_grain"]["held_out_human_observations"] == 0
    evidence = json.loads(
        (ROOT / "examples/canonical-mattress/evidence_bank.json")
        .read_text(encoding="utf-8")
    )
    assert len(evidence) == 28
    assert not any(item["source_id"].startswith("P") for item in evidence)
    docs = ((BASE / "README.md").read_text(encoding="utf-8")
            + (BASE / "next-stage-study.md").read_text(encoding="utf-8"))
    assert "not a completed Lead User project" in docs
    assert "zero qualified LU episodes" in docs
