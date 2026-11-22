"""Structural safeguards for cross-episode behavioral mechanism maps.

The fixture interviews are synthetic; no test establishes empirical causal validity.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from simulation.core import SimulationError, load_checkpoint, schema_check
from simulation.mechanism_map import (
    compile_map,
    inventory,
    make_study,
    planning_handoff,
    render_map,
    resolve_scope,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture()
def source(tmp_path: Path):
    checkpoint = tmp_path / "CHECKPOINT.json"
    cmd = [
        sys.executable, str(ROOT / "scripts" / "export_checkpoint.py"),
        "--evidence", str(FIXTURES / "evidence_bank.json"),
        "--sources", str(FIXTURES / "sources.json"),
        "--codebook", str(FIXTURES / "codebook.json"),
        "--mappings", str(FIXTURES / "evidence_mappings.json"),
        "--interviews", str(FIXTURES / "interviews.json"),
        "--episodes", str(FIXTURES / "episodes.json"),
        "--segments", str(FIXTURES / "segments.json"),
        "--links", str(FIXTURES / "links.json"),
        "--clusters", str(FIXTURES / "clusters.json"),
        "--output", str(checkpoint),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    data, digest = load_checkpoint(checkpoint)
    return checkpoint, data, digest


def reviewed_study(source):
    _, data, digest = source
    study = make_study(data, digest, {"kind": "CLUSTER", "cluster_id": "C02"})
    study["research_question"] = "What distinguishes sustained synthesis from ad hoc reports?"
    study["review"].update({
        "reviewer": "Synthetic test analyst",
        "reviewed_at": "2026-11-22T00:00:00+00:00",
        "evidence_reviewed": True,
        "a_to_b_links_reviewed": True,
        "cluster_interpretation_reviewed": True,
        "contrasting_cases_reviewed": True,
    })
    study["mechanisms"] = [{
        "mechanism_id": "BM01",
        "condition": "Increasing research volume and coordination requirements",
        "hypothesized_relationship": (
            "Higher coordination demands may make repeatable synthesis more valuable."
        ),
        "rival_explanation": "Shared ownership may matter more than volume.",
        "counterfactual_condition_change": "Vary coordination while keeping volume fixed.",
        "disconfirming_observation": (
            "Changing coordination does not affect attempts to reuse the codebook."
        ),
        "discriminating_human_test": (
            "Observe decisions on comparable work with different coordination demands."
        ),
        "revisit_when": "The team structure, interview process, or tooling changes.",
        "observations": [
            {
                "episode": "D02",
                "stance": "ALIGNS",
                "evidence_refs": ["E003", "E004"],
                "link_refs": ["L002"],
                "interpretation": "The interview mentions scale and codebook reuse.",
            },
            {
                "episode": "D03",
                "stance": "AMBIGUOUS",
                "evidence_refs": ["E005"],
                "link_refs": ["L003"],
                "interpretation": "The participant emphasizes pattern visibility.",
            },
        ],
    }]
    return study


def test_cluster_inventory_is_read_only_and_keeps_evidence_provenance(source):
    checkpoint, data, digest = source
    original = checkpoint.read_bytes()
    study = make_study(data, digest, {"kind": "CLUSTER", "cluster_id": "C02"})
    schema_check(study, "mechanism-study.schema.json")
    assert not study["review"]["evidence_reviewed"]
    assert study["review"]["reviewed_at"] is None
    assert study["mechanisms"] == []
    index = inventory(data, digest, study)
    assert [r["episode"] for r in index["episodes"]] == ["D02", "D03"]
    assert index["distinct_interviews"] == 2
    assert index["review_status"] == "NOT_ATTESTED"
    assert index["episodes"][0]["a_to_b_links"][0]["link"] == "L002"
    assert index["episodes"][1]["evidence_types"]["E005"]["type"] == "interpretation"
    assert "verbatim_excerpt" not in json.dumps(index)
    assert checkpoint.read_bytes() == original


def test_compiled_map_records_variation_and_planning_handoff(source):
    _, data, digest = source
    study = reviewed_study(source)
    result = compile_map(data, digest, study)
    mechanism = result["mechanisms"][0]
    assert result["status"] == "PROVISIONAL"
    assert result["cross_person_comparison_possible"]
    assert result["source_inventory"]["review_status"].startswith("HUMAN_REVIEW")
    assert mechanism["distinct_interviews_by_stance"]["ALIGNS"] == ["I02"]
    assert mechanism["distinct_interviews_by_stance"]["AMBIGUOUS"] == ["I03"]
    assert mechanism["distinct_interviews_by_stance"]["COUNTEREXAMPLE"] == []
    assert mechanism["observations"][0]["evidence_types"] == [
        "aspiration", "generalization"
    ]
    assert not mechanism["observations"][0]["behavior_observed_in_sources"]
    text = render_map(result)
    assert "L002 (INFERRED)" in text
    assert "COUNTEREXAMPLE" not in text or "not causal" in text.lower()
    assert "No population prevalence" in text
    handoff = planning_handoff(result)
    assert handoff["status"] == "PROPOSED"
    assert handoff["acceptance_gate"] == "HUMAN_ACCEPTANCE_REQUIRED"
    assert handoff["f_solution_variable"] == "UNSPECIFIED"
    assert handoff["M_operating_model"]["authority"] == "PROPOSED"
    assert handoff["M_operating_model"]["conditions_and_hypotheses"][0][
        "source_evidence_refs"
    ] == ["SID:BMST001:E003", "SID:BMST001:E004", "SID:BMST001:E005"]
    cases = handoff["M_operating_model"]["conditions_and_hypotheses"][0]["case_evidence"]
    assert [(row["episode_ref"], row["stance"]) for row in cases] == [
        ("SID:BMST001:D02", "ALIGNS"),
        ("SID:BMST001:D03", "AMBIGUOUS"),
    ]
    assert cases[0]["a_to_b_link_refs"] == ["SID:BMST001:L002"]
    assert cases[0]["source_type_indicates_reported_behavior"] is False
    assert handoff["M_operating_model"]["conditions_and_hypotheses"][0][
        "discriminating_human_test"
    ].startswith("Observe decisions")
    assert "selected_shape" not in json.dumps(handoff)
    assert "accepted_requirement" not in json.dumps(handoff)


def test_assessments_have_explicit_unassessed_not_negative_cases(source):
    _, data, digest = source
    study = reviewed_study(source)
    study["mechanisms"][0]["observations"].pop()
    result = compile_map(data, digest, study)
    row = result["mechanisms"][0]
    assert row["unassessed_episode_ids"] == ["D03"]
    assert row["distinct_interviews_by_stance"]["UNASSESSED"] == ["I03"]
    assert row["distinct_interviews_by_stance"]["COUNTEREXAMPLE"] == []
    assert row["observations"][1]["evidence_refs"] == []
    assert "absence is not a counterexample" in row["observations"][1]["interpretation"]


def test_wrong_episode_and_wrong_link_references_are_rejected(source):
    _, data, digest = source
    study = reviewed_study(source)
    bad = copy.deepcopy(study)
    bad["mechanisms"][0]["observations"][0]["evidence_refs"] = ["E001"]
    with pytest.raises(SimulationError, match="belongs to another episode"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["mechanisms"][0]["observations"][0]["link_refs"] = ["L001"]
    with pytest.raises(SimulationError, match="link belongs to another episode"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["mechanisms"][0]["observations"][0]["episode"] = "D01"
    with pytest.raises(SimulationError, match="out-of-scope"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["mechanisms"][0]["observations"].append(
        copy.deepcopy(bad["mechanisms"][0]["observations"][0])
    )
    with pytest.raises(SimulationError, match="Repeated episode"):
        compile_map(data, digest, bad)


def test_unassessed_never_cites_evidence_and_review_is_required(source):
    _, data, digest = source
    study = reviewed_study(source)
    bad = copy.deepcopy(study)
    bad["mechanisms"][0]["observations"][0]["stance"] = "UNASSESSED"
    with pytest.raises(SimulationError, match="must not cite"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["review"]["contrasting_cases_reviewed"] = False
    with pytest.raises(SimulationError, match="contrasting-case"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["review"]["cluster_interpretation_reviewed"] = False
    with pytest.raises(SimulationError, match="Cluster interpretation"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["source_checkpoint_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(SimulationError, match="different checkpoint"):
        compile_map(data, digest, bad)
    bad = copy.deepcopy(study)
    bad["mechanisms"].append(copy.deepcopy(bad["mechanisms"][0]))
    with pytest.raises(SimulationError, match="must be unique"):
        compile_map(data, digest, bad)


def test_single_interview_cluster_does_not_claim_cross_person_effect(source):
    _, data, digest = source
    study = reviewed_study(source)
    study["scope"] = {"kind": "CLUSTER", "cluster_id": "C01"}
    study["mechanisms"][0]["observations"] = [{
        "episode": "D01", "stance": "AMBIGUOUS",
        "evidence_refs": ["E001"], "link_refs": ["L001"],
        "interpretation": "Only one coded interview is available.",
    }]
    result = compile_map(data, digest, study)
    assert not result["cross_person_comparison_possible"]
    assert any("Only one interview" in line for line in result["limitations"])


def test_explicit_scope_and_interview_grain_clusters(source):
    _, data, digest = source
    study = make_study(data, digest, {
        "kind": "EPISODES", "episode_ids": ["D02", "D03"]
    })
    assert len(inventory(data, digest, study)["episodes"]) == 2
    bad = copy.deepcopy(data)
    bad["clusters"] = [
        {"interview": "I01", "cluster": "C01"},
        {"interview": "I02", "cluster": "C02"},
        {"interview": "I03", "cluster": "C02"},
    ]
    bad["analysis_unit"] = "interview"
    selected = resolve_scope(bad, {"kind": "CLUSTER", "cluster_id": "C02"})
    assert selected == ["D02", "D03"]
    no_clusters = copy.deepcopy(data)
    no_clusters["clusters"] = []
    no_clusters["computation"]["cluster_count"] = 0
    with pytest.raises(SimulationError, match="No accepted cluster"):
        resolve_scope(no_clusters, {"kind": "CLUSTER", "cluster_id": "C02"})
    assert resolve_scope(no_clusters, study["scope"]) == ["D02", "D03"]


def test_cli_end_to_end_and_no_automatic_approval(source, tmp_path):
    checkpoint, data, _ = source
    cli = [sys.executable, str(ROOT / "scripts" / "mechanism_map_cli.py")]
    draft = tmp_path / "study.json"
    evidence_inventory = tmp_path / "inventory.json"
    cmd = ["--checkpoint", str(checkpoint)]
    subprocess.run(
        cli + ["init", *cmd, "--cluster", "C02", "--output", str(draft)],
        check=True, capture_output=True,
    )
    initialized = json.loads(draft.read_text())
    assert initialized["review"]["reviewed_at"] is None
    subprocess.run(
        cli + ["inventory", *cmd, "--study", str(draft),
               "--output", str(evidence_inventory)],
        check=True, capture_output=True,
    )
    assert len(json.loads(evidence_inventory.read_text())["episodes"]) == 2
    map_file = tmp_path / "map.json"
    fail = subprocess.run(
        cli + ["compile", *cmd, "--study", str(draft), "--output", str(map_file)],
        capture_output=True, text=True,
    )
    assert fail.returncode != 0
    assert not map_file.exists()
    reviewed = reviewed_study(source)
    draft.write_text(json.dumps(reviewed))
    report = tmp_path / "map.md"
    handoff = tmp_path / "proposed-planning.json"
    original = checkpoint.read_bytes()
    subprocess.run(
        cli + [
            "compile", *cmd, "--study", str(draft), "--output", str(map_file),
            "--report", str(report), "--planning-handoff", str(handoff),
        ], check=True, capture_output=True,
    )
    assert json.loads(map_file.read_text())["status"] == "PROVISIONAL"
    assert json.loads(handoff.read_text())["status"] == "PROPOSED"
    assert "Behavioral Mechanism Map" in report.read_text()
    assert checkpoint.read_bytes() == original


def test_partial_coverage_and_zero_link_episodes_are_not_hidden(source):
    _, data, digest = source
    copied = copy.deepcopy(data)
    copied["a_to_b_links"] = [
        row for row in copied["a_to_b_links"] if row["episode"] != "D03"
    ]
    for row in copied["source_index"]:
        if row["source_id"] == "SRC03":
            row["coverage"] = "PARTIAL"
    study = reviewed_study(source)
    study["mechanisms"][0]["observations"][1]["link_refs"] = []
    result = compile_map(copied, digest, study)
    assert "D03" in [row["episode"] for row in result["source_inventory"]["episodes"]]
    assert any("Source coverage is not complete" in line for line in result["limitations"])
    report = render_map(result)
    assert "Episodes without a reviewed A→B link" in report
    assert "D03 (I03)" in report
    assert "PARTIAL" in report
