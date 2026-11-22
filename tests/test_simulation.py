"""The simulation adapter must not allow model outputs to masquerade as interviews."""
from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from simulation.core import (
    SimulationError,
    ensure_run_matches,
    initialize,
    inspect_scenario,
    load_checkpoint,
    prepare,
    record,
    sha256_text,
)
from simulation.evaluation import assess, ks_similarity, tvd
from simulation.report import render
from simulation.ssr import distribution, measure

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
        "--output", str(checkpoint),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    data, digest = load_checkpoint(checkpoint)
    scenario = initialize(checkpoint, ["D01"], ["E001", "E002"])
    scenario["review"].update({
        "reviewer": "Example analyst", "evidence_reviewed": True,
        "codebook_links_reviewed": True, "processing_permitted": True,
    })
    scenario["baseline"].update({
        "path_y": "An evidenced prior workaround",
        "observed_result": "UNKNOWN", "evidence_refs": ["E001"],
    })
    scenario["decision"] = "Which mechanism should be tested?"
    scenario["intervention"] = {
        "variable": "switching_effort", "from": "manual", "to": "assisted"
    }
    return checkpoint, data, digest, scenario


def model_response():
    return {
        "model": "test-fixture", "model_version": "0", "configuration": {"seed": 2},
        "responses": [{
            "text": "I might switch if transferring became easier.",
            "mechanism": "Lowered anticipated effort",
            "evidence_refs": ["E001"], "objections": ["Uncertain trust"],
            "next_test": "Offer assisted migration in a real trial.",
        }],
    }


def generated(source):
    _, data, digest, scenario = source
    return record(data, digest, scenario, model_response())


def vectors_for(run):
    vectors = []
    for i, row in enumerate(run["responses"]):
        vectors.append({
            "index": i, "text_sha256": sha256_text(row["text"]),
            "vector": [1.0, 0.5],
        })
    sets = []
    for set_id in range(2):
        sets.append({
            "id": f"anchors-{set_id}", "anchors": [{
                "rating": rating,
                "text": f"Rating {rating} statement",
                "vector": [math.cos(rating / 2), math.sin(rating / 2)],
            } for rating in range(1, 6)],
        })
    return {
        "schema_version": "1.0", "run_id": run["run_id"],
        "construct": "stated_switching_intent",
        "embedding_model": "test-vectors", "anchor_version": "fixture-1",
        "epsilon": 0.0, "temperature": 1.0,
        "anchor_sets": sets, "response_embeddings": vectors,
    }


def holdout(run):
    return {
        "schema_version": "1.0", "validation_id": "V001", "run_id": run["run_id"],
        "construct": "stated_switching_intent", "split_unit": "PERSON",
        "holdout_group_ids": ["I99", "I98"],
        "observed_ratings": [3, 4, 5], "baseline_distribution": [0.2] * 5,
        "source": "Illustrative external human response fixture",
        "predeclared_at": "2020-01-01T00:00:00+00:00",
        "collection_and_use_permitted": True, "held_out_attested": True,
    }


def test_read_only_checkpoint_boundaries(source):
    checkpoint, data, digest, scenario = source
    before = checkpoint.read_bytes()
    packet = prepare(data, digest, scenario, include_verbatim=True)
    assert packet["source_type"] == "OBSERVED_HUMAN"
    assert "verbatim_excerpt" in packet["evidence"][0]
    assert "SIMULATED_ESTIMATE" not in json.dumps(packet["evidence"])
    run = generated(source)
    assert run["grade"] == "L0_ROLEPLAY"
    assert run["evidence_type"] == "SIMULATED_ESTIMATE"
    ensure_run_matches(run, scenario, digest)
    assert checkpoint.read_bytes() == before
    assert set(data) == set(json.loads(before))


def test_missing_approval_and_checkpoint_revisions_fail(source):
    _, data, digest, scenario = source
    bad = copy.deepcopy(scenario)
    bad["review"]["evidence_reviewed"] = False
    with pytest.raises(SimulationError, match="review"):
        inspect_scenario(data, digest, bad)
    bad = copy.deepcopy(scenario)
    bad["source_checkpoint_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(SimulationError, match="different checkpoint"):
        inspect_scenario(data, digest, bad)


def test_invalid_evidence_and_episode_ownership_fail(source):
    _, data, digest, scenario = source
    bad = copy.deepcopy(scenario)
    bad["evidence_refs"].append("E006")
    with pytest.raises(SimulationError, match="belong"):
        inspect_scenario(data, digest, bad)
    bad = copy.deepcopy(scenario)
    bad["evidence_refs"].append("E900")
    with pytest.raises(SimulationError, match="Unknown source references"):
        inspect_scenario(data, digest, bad)


def test_individual_proxy_requires_one_person_and_grounding_review(source):
    _, data, digest, scenario = source
    bad = copy.deepcopy(scenario)
    bad["mode"] = "INDIVIDUAL_PROXY"
    bad["target_grade"] = "L1_PERSON_GROUNDED"
    with pytest.raises(SimulationError, match="one interview"):
        inspect_scenario(data, digest, bad)
    bad["review"]["person_grounding_reviewed"] = True
    assert inspect_scenario(data, digest, bad)["grounded_interviews"] == ["I01"]
    bad["episode_refs"].append("D02")
    with pytest.raises(SimulationError, match="one interview"):
        inspect_scenario(data, digest, bad)
    bad = copy.deepcopy(scenario)
    bad["mode"] = "POPULATION_PREDICTION"
    with pytest.raises(SimulationError):
        inspect_scenario(data, digest, bad)


def test_generated_content_cannot_forge_evidence(source):
    _, data, digest, scenario = source
    fake = model_response()
    fake["responses"][0]["evidence_refs"] = ["E999"]
    with pytest.raises(SimulationError, match="out-of-scope"):
        record(data, digest, scenario, fake)
    fake = model_response()
    fake["responses"][0]["evidence_refs"] = ["E003"]
    with pytest.raises(SimulationError, match="out-of-scope"):
        record(data, digest, scenario, fake)
    run = generated(source)
    edited = copy.deepcopy(scenario)
    edited["assumptions"].append("Changed after generation")
    with pytest.raises(SimulationError, match="does not match"):
        ensure_run_matches(run, edited, digest)


def test_privacy_defaults_are_closed(source):
    _, data, digest, scenario = source
    packet = prepare(data, digest, scenario)
    assert all("verbatim_excerpt" not in item for item in packet["evidence"])
    scenario["review"]["processing_permitted"] = False
    with pytest.raises(SimulationError, match="not approved"):
        prepare(data, digest, scenario, include_verbatim=True)


def test_ssr_validates_vectors_and_rating_mass(source):
    run = generated(source)
    output = measure(run, vectors_for(run))
    assert output["evidence_type"] == "SIMULATED_ESTIMATE"
    assert math.isclose(sum(output["aggregate"]), 1.0, abs_tol=1e-12)
    assert output["anchor_set_count"] == 2
    broken = vectors_for(run)
    broken["response_embeddings"][0]["text_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(SimulationError, match="does not match"):
        measure(run, broken)
    broken = vectors_for(run)
    broken["anchor_sets"][0]["anchors"][2]["rating"] = 1
    with pytest.raises(SimulationError, match="once"):
        measure(run, broken)
    with pytest.raises(SimulationError, match="degenerate"):
        distribution([1.0, 0.0], [[1.0, 0.0]] * 5)


def test_holdout_checks_leakage_and_never_promotes_grade(source):
    _, data, _, scenario = source
    run = generated(source)
    measurement = measure(run, vectors_for(run))
    evaluation = assess(data, scenario, run, measurement, holdout(run))
    assert evaluation["grade_after_validation"] == "L0_ROLEPLAY"
    assert 0 <= evaluation["tvd"] <= 1
    assert 0 <= evaluation["ks_similarity"] <= 1
    assert math.isclose(tvd([0.2] * 5, [0.2] * 5), 0)
    assert math.isclose(ks_similarity([0.2] * 5, [0.2] * 5), 1)
    bad = holdout(run)
    bad["holdout_group_ids"] = ["I01"]
    with pytest.raises(SimulationError, match="overlap"):
        assess(data, scenario, run, measurement, bad)
    bad = holdout(run)
    bad["predeclared_at"] = datetime.now(timezone.utc).replace(
        year=datetime.now(timezone.utc).year + 1
    ).isoformat()
    with pytest.raises(SimulationError, match="before generation"):
        assess(data, scenario, run, measurement, bad)


def test_report_is_explicitly_synthetic(source):
    _, data, _, scenario = source
    run = generated(source)
    measurement = measure(run, vectors_for(run))
    result = assess(data, scenario, run, measurement, holdout(run))
    report = render(scenario, run, measurement, result)
    assert "SIMULATED_ESTIMATE" in report
    assert "not actual customer responses" in report
    assert "not automatically authorize L3" in report


def test_cli_prepares_records_and_reports(source, tmp_path):
    checkpoint, _, _, scenario = source
    scenario_path = tmp_path / "scenario.json"
    raw_path = tmp_path / "model.json"
    output_path = tmp_path / "run.json"
    scenario_path.write_text(json.dumps(scenario))
    raw_path.write_text(json.dumps(model_response()))
    cli = [sys.executable, str(ROOT / "scripts" / "simulation_cli.py")]
    subprocess.run(cli + [
        "record", "--checkpoint", str(checkpoint), "--scenario", str(scenario_path),
        "--model-output", str(raw_path), "--output", str(output_path),
    ], check=True, capture_output=True)
    run = json.loads(output_path.read_text())
    assert run["run_id"] == "R001"
    report_path = tmp_path / "report.md"
    subprocess.run(cli + [
        "report", "--checkpoint", str(checkpoint), "--scenario", str(scenario_path),
        "--run", str(output_path), "--output", str(report_path),
    ], check=True, capture_output=True)
    assert "NOT VALIDATED" in report_path.read_text()
