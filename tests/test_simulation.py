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

from simulation.counterfactual import build_brief, compare_briefs, render_brief
from simulation.core import (
    SimulationError,
    ensure_run_matches,
    initialize,
    inspect_scenario,
    load_checkpoint,
    prepare,
    record,
    schema_check,
    sha256_text,
)
from simulation.evaluation import assess, ks_similarity, tvd
from simulation.handoff import protocol_input, protocol_runs
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
    scenario["measurement"] = {
        "construct": "stated_switching_intent",
        "question": "How likely would you switch if migration were assisted?",
        "scale": "FIVE_POINT_LIKERT",
        "anchor_version": "fixture-1",
    }
    scenario["decision_owner"] = "Example analyst"
    scenario["consequence_if_wrong"] = "We could prioritize the wrong migration experiment."
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
        "question": "How likely would you switch if migration were assisted?",
        "holdout_group_ids": ["I99", "I98", "I97"],
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


def test_counterfactual_must_change_one_condition(source):
    _, data, digest, scenario = source
    bad = copy.deepcopy(scenario)
    bad["intervention"]["to"] = bad["intervention"]["from"]
    with pytest.raises(SimulationError, match="must change"):
        inspect_scenario(data, digest, bad)
    bad = copy.deepcopy(scenario)
    bad["held_constant"] = ["switching_effort"]
    with pytest.raises(SimulationError, match="held constant"):
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
    forged = copy.deepcopy(run)
    forged["grade"] = "L4_DECISION_CALIBRATED"
    with pytest.raises(SimulationError, match="does not match"):
        ensure_run_matches(forged, scenario, digest)
    with pytest.raises(SimulationError, match="cannot promote"):
        render(scenario, forged)
    wrong_measurement = copy.deepcopy(run)
    wrong_measurement["measurement"]["question"] = "A different question"
    with pytest.raises(SimulationError, match="does not match"):
        ensure_run_matches(wrong_measurement, scenario, digest)


def test_privacy_defaults_are_closed(source):
    _, data, digest, scenario = source
    packet = prepare(data, digest, scenario)
    assert all("verbatim_excerpt" not in item for item in packet["evidence"])
    assert "review" not in packet["scenario"]
    scenario["review"]["processing_permitted"] = False
    with pytest.raises(SimulationError, match="not approved"):
        prepare(data, digest, scenario, include_verbatim=True)


def test_ssr_validates_vectors_and_rating_mass(source):
    run = generated(source)
    output = measure(run, vectors_for(run))
    assert output["evidence_type"] == "SIMULATED_ESTIMATE"
    assert math.isclose(sum(output["aggregate"]), 1.0, abs_tol=1e-12)
    assert output["anchor_set_count"] == 2
    no_question = copy.deepcopy(run)
    no_question["measurement"] = None
    with pytest.raises(SimulationError, match="predeclared"):
        measure(no_question, vectors_for(no_question))
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
    assert evaluation["scenario_sha256"] == run["scenario_sha256"]
    assert evaluation["run_sha256"] == sha256_text(json.dumps(run, sort_keys=True))
    assert evaluation["measurement_sha256"] == sha256_text(
        json.dumps(measurement, sort_keys=True)
    )
    bad = holdout(run)
    bad["question"] = "Would you buy a totally different product?"
    with pytest.raises(SimulationError, match="question"):
        assess(data, scenario, run, measurement, bad)
    assert 0 <= evaluation["tvd"] <= 1
    assert 0 <= evaluation["ks_similarity"] <= 1
    assert math.isclose(tvd([0.2] * 5, [0.2] * 5), 0)
    assert math.isclose(ks_similarity([0.2] * 5, [0.2] * 5), 1)
    bad = holdout(run)
    bad["holdout_group_ids"] = ["I01", "I98", "I97"]
    with pytest.raises(SimulationError, match="overlap"):
        assess(data, scenario, run, measurement, bad)
    bad = holdout(run)
    bad["holdout_group_ids"] = ["I99"]
    with pytest.raises(SimulationError, match="one response"):
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
    with pytest.raises(SimulationError, match="without its SSR measurement"):
        render(scenario, run, None, result)
    forged = copy.deepcopy(result)
    forged["measurement_sha256"] = sha256_text("other valid-looking measurement")
    with pytest.raises(SimulationError, match="does not belong"):
        render(scenario, run, measurement, forged)
    forged = copy.deepcopy(result)
    forged["grade_after_validation"] = "L4_DECISION_CALIBRATED"
    with pytest.raises(SimulationError, match="does not belong"):
        render(scenario, run, measurement, forged)



def test_companion_behavioral_simulation_handoff_matches_pinned_contract(source):
    _, _, _, scenario = source
    run = generated(source)
    upstream_input = protocol_input(scenario)
    upstream_runs = protocol_runs(run, scenario)
    schema_check(upstream_input, "behavioral-input-v0.1.0.schema.json")
    schema_check(upstream_runs, "behavioral-runs-v0.1.0.schema.json")
    assert upstream_input["mode"] == "PLAUSIBILITY_SPACE"
    assert upstream_runs["entries"][0]["estimate"]["evidence_type"] == "SIMULATED_ESTIMATE"
    assert upstream_runs["entries"][0]["evidence_ids"] == ["E001"]


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
    vectors_path = tmp_path / "vectors.json"
    measurement_path = tmp_path / "measurement.json"
    vectors_path.write_text(json.dumps(vectors_for(run)))
    subprocess.run(cli + [
        "ssr", "--checkpoint", str(checkpoint), "--scenario", str(scenario_path),
        "--run", str(output_path), "--vectors", str(vectors_path),
        "--output", str(measurement_path),
    ], check=True, capture_output=True)
    assert json.loads(measurement_path.read_text())["run_id"] == "R001"
    corrupted = copy.deepcopy(run)
    corrupted["measurement"]["question"] = "Wrong question"
    corrupt_path = tmp_path / "invalid-run.json"
    corrupt_path.write_text(json.dumps(corrupted))
    bad_result = subprocess.run(cli + [
        "ssr", "--checkpoint", str(checkpoint), "--scenario", str(scenario_path),
        "--run", str(corrupt_path), "--vectors", str(vectors_path),
        "--output", str(measurement_path),
    ], capture_output=True, text=True)
    assert bad_result.returncode != 0
    assert "does not match" in bad_result.stderr
    handoff = tmp_path / "upstream"
    subprocess.run(cli + [
        "handoff", "--checkpoint", str(checkpoint), "--scenario", str(scenario_path),
        "--run", str(output_path), "--output-dir", str(handoff),
    ], check=True, capture_output=True)
    assert (handoff / "input.json").exists()
    assert (handoff / "runs.json").exists()


def design_hypothesis():
    return {
        "product_change": "Assisted migration instead of more reporting features",
        "critical_assumption": "Manual migration effort is the primary switching barrier.",
        "predicted_behavior": "People attempt migration rather than defer.",
        "disconfirming_observation": (
            "People offered assisted migration still decline due to security concerns."
        ),
        "if_disconfirmed": "Test reversible migration and trust assurances instead.",
    }


def test_counterfactual_brief_grounds_a_to_b_and_separates_claims(source):
    checkpoint, data, digest, scenario = source
    scenario["design_hypothesis"] = design_hypothesis()
    run = record(data, digest, scenario, model_response())
    original = checkpoint.read_bytes()
    brief = build_brief(data, digest, scenario, run)
    schema_check(brief, "counterfactual-brief.schema.json")
    assert brief["validation_status"] == "NOT_VALIDATED"
    assert brief["decision_status"] == "TEST_BEFORE_BUILD"
    assert brief["evidence_grade"] == "L0_ROLEPLAY"
    assert brief["reviewed_a_to_b_links"][0]["link"] == "L001"
    assert brief["reviewed_a_to_b_links"][0]["a_definition"].startswith(
        "Manual synthesis"
    )
    assert brief["reviewed_a_to_b_links"][0]["b_code"] == "B01"
    assert brief["simulated_hypotheses"][0]["evidence_type"] == "SIMULATED_ESTIMATE"
    assert brief["simulated_hypotheses"][0]["source_evidence_refs"] == ["E001"]
    text = render_brief(brief)
    assert "Reviewed" not in brief["simulated_hypotheses"][0]["generated_statement"]
    assert "L001 / INFERRED / E001, E002" in text
    assert "TEST BEFORE BUILD" in text
    assert "SIMULATED, NOT OBSERVED" in text
    assert "Disconfirming observation" in text
    assert checkpoint.read_bytes() == original


def test_counterfactual_requires_predeclared_hypothesis_and_reviewed_link(source):
    _, data, digest, scenario = source
    run = generated(source)
    with pytest.raises(SimulationError, match="Declare design_hypothesis"):
        build_brief(data, digest, scenario, run)
    scenario["design_hypothesis"] = design_hypothesis()
    run = record(data, digest, scenario, model_response())
    scenario["evidence_refs"] = ["E001"]
    scenario["baseline"]["evidence_refs"] = ["E001"]
    scenario["source_checkpoint_sha256"] = digest
    with pytest.raises(SimulationError, match="approved scenario"):
        build_brief(data, digest, scenario, run)
    fresh = record(data, digest, scenario, model_response())
    with pytest.raises(SimulationError, match="No reviewed A-to-B links"):
        build_brief(data, digest, scenario, fresh)


def test_counterfactual_rejects_placeholder_design_and_invalid_comparison(source):
    _, data, digest, scenario = source
    scenario["design_hypothesis"] = design_hypothesis()
    scenario["design_hypothesis"]["product_change"] = "REPLACE"
    with pytest.raises(SimulationError, match="Complete design_hypothesis"):
        inspect_scenario(data, digest, scenario)
    scenario["design_hypothesis"] = design_hypothesis()
    run = record(data, digest, scenario, model_response())
    first = build_brief(data, digest, scenario, run)
    other = copy.deepcopy(scenario)
    other["scenario_id"] = "SIM002"
    other["intervention"]["to"] = "automatic"
    other["design_hypothesis"]["product_change"] = "Automatic migration"
    second_run = record(data, digest, other, model_response(), run_id="R002")
    second = build_brief(data, digest, other, second_run)
    comparison = compare_briefs([first, second])
    assert "SIM001" in comparison and "SIM002" in comparison
    assert "not measured" in comparison
    with pytest.raises(SimulationError, match="distinct"):
        compare_briefs([first, first])
    other["baseline"]["path_y"] = "Not the same baseline"
    third = record(data, digest, other, model_response(), run_id="R003")
    wrong = build_brief(data, digest, other, third)
    with pytest.raises(SimulationError, match="identical human evidence"):
        compare_briefs([first, wrong])


def test_counterfactual_cli_brief_and_compare(source, tmp_path):
    checkpoint, data, digest, scenario = source
    scenario["design_hypothesis"] = design_hypothesis()
    run = record(data, digest, scenario, model_response())
    scenario_path = tmp_path / "scenario.json"
    run_path = tmp_path / "run.json"
    scenario_path.write_text(json.dumps(scenario))
    run_path.write_text(json.dumps(run))
    cli = [sys.executable, str(ROOT / "scripts" / "simulation_cli.py")]
    markdown = tmp_path / "brief.md"
    output_json = tmp_path / "brief.json"
    subprocess.run(cli + [
        "counterfactual", "--checkpoint", str(checkpoint),
        "--scenario", str(scenario_path), "--run", str(run_path),
        "--output", str(markdown), "--json-output", str(output_json),
    ], check=True, capture_output=True)
    assert "Manual synthesis" in markdown.read_text()
    assert json.loads(output_json.read_text())["validation_status"] == "NOT_VALIDATED"

    second = copy.deepcopy(scenario)
    second["scenario_id"] = "SIM002"
    second["intervention"]["to"] = "one-click"
    second["design_hypothesis"]["product_change"] = "One-click migration"
    second_run = record(data, digest, second, model_response(), run_id="R002")
    second_path = tmp_path / "second.json"
    second_run_path = tmp_path / "second-run.json"
    second_path.write_text(json.dumps(second))
    second_run_path.write_text(json.dumps(second_run))
    comparison = tmp_path / "compare.md"
    subprocess.run(cli + [
        "compare", "--checkpoint", str(checkpoint),
        "--scenario", str(scenario_path), "--run", str(run_path),
        "--scenario", str(second_path), "--run", str(second_run_path),
        "--output", str(comparison),
    ], check=True, capture_output=True)
    assert "SIM001" in comparison.read_text()
    assert "SIM002" in comparison.read_text()
