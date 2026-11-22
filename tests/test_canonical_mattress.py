"""Canonical real-source regression tests: evidence integrity and synthetic boundaries."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from simulation.core import SimulationError, inspect_scenario, load_checkpoint
from simulation.ssr import measure

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "examples" / "canonical-mattress"


def _read(path: str):
    return json.loads((CANON / path).read_text(encoding="utf-8"))


def test_complete_source_has_distinct_roles_and_verbatim_participant_evidence():
    manifest = _read("source-manifest.json")
    turns = _read("source-turns.json")
    bank = _read("evidence_bank.json")
    assert manifest["coverage"] == "FULL_PUBLISHED_PAGE_NOT_ORIGINAL_AUDIO"
    assert len(turns) == manifest["speaker_turns"]
    assert sum(x["role"] == "PARTICIPANT" for x in turns) >= 75
    assert len(bank) == 28
    assert all(x["speaker"] == "PARTICIPANT" for x in bank)
    assert any(x["evidence_type"] == "hypothetical" for x in bank)
    assert any(x["evidence_type"] == "concrete_event_or_behavior" for x in bank)
    assert len(_read("interviews.json")) == 1
    assert len(_read("episodes.json")) == 1
    assert len(_read("links.json")) == 4
    sources = {row["turn_id"]: row for row in turns}
    for row in bank:
        turn_id = row["source_location"].split(" | ", 1)[0]
        source = sources[turn_id]
        assert source["role"] == "PARTICIPANT"
        assert row["verbatim_excerpt"] in source["text"]
    report = (CANON / "synthesis_report.md").read_text()
    assert "NOT HUMAN REVIEWED" in report
    assert "UNKNOWN" in report


def test_checkpoint_preserves_one_episode_and_no_cluster():
    checkpoint, digest = load_checkpoint(CANON / "results" / "CHECKPOINT.json")
    assert len(checkpoint["interview_index"]) == 1
    assert len(checkpoint["episode_index"]) == 1
    assert checkpoint["clusters"] == []
    assert checkpoint["computation"]["cluster_count"] == 0
    assert digest.startswith("sha256:")


def test_two_real_semantic_ssr_calculations_remain_uncalibrated():
    data, digest = load_checkpoint(CANON / "results" / "CHECKPOINT.json")
    summary = _read("results/simulations/summary.json")
    assert summary["human_participants"] == 1
    assert summary["human_holdouts"] == 0
    assert summary["status"] == "UNVALIDATED_EDUCATIONAL_DEMONSTRATION"
    assert summary["anchor_sets"] == 6
    assert len(summary["scenarios"]) == 2
    for key in ["SIM001", "SIM002"]:
        scenario = _read(f"results/simulations/{key}/scenario.json")
        run = _read(f"results/simulations/{key}/run.json")
        vectors = _read(f"results/simulations/{key}/ssr-vectors.json")
        result = _read(f"results/simulations/{key}/ssr.json")
        assert scenario["source_checkpoint_sha256"] == digest
        assert not scenario["review"]["evidence_reviewed"]
        assert not scenario["review"]["codebook_links_reviewed"]
        assert not scenario["review"]["reviewer"]
        assert run["grade"] == "L0_ROLEPLAY"
        assert run["review_status"] == "AI_CURATED_NOT_HUMAN_APPROVED"
        assert run["evidence_type"] == "SIMULATED_ESTIMATE"
        assert vectors["embedding_model"] == "BAAI/bge-small-en-v1.5"
        assert len(vectors["anchor_sets"]) == 6
        assert len(vectors["response_embeddings"]) == 2
        with pytest.raises(SimulationError, match="review"):
            inspect_scenario(data, digest, scenario)
        checked = measure(run, vectors)
        assert len(checked["aggregate"]) == 5
        assert math.isclose(sum(checked["aggregate"]), 1.0, abs_tol=1e-10)
        assert all(math.isfinite(x) and x >= 0 for x in checked["aggregate"])
        for actual, stored in zip(
            checked["aggregate"], result["aggregate"], strict=True
        ):
            assert math.isclose(actual, stored, abs_tol=1e-11)


def test_human_review_has_not_been_claimed_anywhere_in_generated_summary():
    summary = _read("results/simulations/summary.json")
    text = json.dumps(summary)
    assert "L3" not in text and "L4" not in text
    assert "UNVALIDATED" in text
    assert "human_holdouts" in text
