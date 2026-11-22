"""Canonical educational simulation + semantic SSR; no human validation implied.

The hypothetical response statements were authored by GPT-6 within this task.
They are NOT independent stochastic samples or re-interviews. This worked case
does not bypass human review gates: it stores demonstrative L0 artifacts instead
of invoking review-gated record/prepare commands.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulation.core import (
    SimulationError, initialize, load_checkpoint, schema_check, sha256_text, write_json,
)
from simulation.handoff import protocol_input, protocol_runs
from simulation.report import render
from simulation.ssr import measure

MODEL = "BAAI/bge-small-en-v1.5"
ANCHOR_VERSION = "mattress-intent-anchors-v1"
CONSTRUCT = "hypothetical_stated_purchase_intent"
QUESTION = "Under the proposed conditions, how likely are you to attempt a mattress purchase?"
EVIDENCE_REFS = [
    "E002", "E006", "E008", "E014", "E015", "E018", "E019",
    "E020", "E021", "E023", "E024", "E025", "E027",
]
ANCHORS = [
    ["I definitely would not buy it.", "I probably would not buy it.",
     "I am undecided whether to buy it.", "I would probably buy it.",
     "I definitely would buy it."],
    ["I would certainly walk away without buying.", "I lean against purchasing.",
     "I could go either way about purchasing.", "I lean toward purchasing.",
     "I would certainly complete the purchase."],
    ["The proposed conditions leave me unwilling to buy.",
     "I am reluctant to buy under these conditions.",
     "I have mixed feelings about buying.",
     "I am willing to buy under these conditions.",
     "I would eagerly make the purchase."],
    ["There is no chance I would agree to the purchase.",
     "I see little reason to purchase yet.",
     "I still need to decide whether I would purchase.",
     "I can imagine buying this mattress.",
     "I am ready to commit to purchasing it."],
    ["I would reject the mattress offer.",
     "I would hesitate and likely decline the offer.",
     "I am genuinely on the fence about the offer.",
     "I would seriously consider accepting the offer.",
     "I would accept the offer without hesitation."],
    ["I would not consider buying in this situation.",
     "I would consider it but likely say no.",
     "I might buy or might not; I do not know.",
     "I would probably go ahead and buy.",
     "I would go ahead and buy for sure."],
]
CASES = [
    {
        "scenario": "SIM001", "run": "R001",
        "decision": "Would guaranteed home return pickup help overcome switching anxiety?",
        "intervention": {"variable": "return_logistics",
                         "from": "uncertain customer-organized return",
                         "to": "free home pickup after an unsatisfactory trial"},
        "design": "Offer guaranteed collection and refund if a mattress trial fails",
        "assumption": "Recovery logistics substantially contribute to purchase hesitation",
        "predicted": "An easier recovery path could make purchase attempts more likely",
        "disconfirm": "The customer rejects the offer despite verified pickup terms",
        "fallback": "Investigate trust in seller and whether spouses can assess the product",
        "responses": [
            {
                "text": "I would probably buy if someone reliably picked up the mattress "
                        "and refunded me if it did not work, but I would still check with my wife.",
                "mechanism": "Reduced anticipated loss or disposal burden",
                "evidence_refs": ["E014", "E019", "E020", "E027"],
                "objections": ["Seller credibility", "Spouse's agreement"],
                "next_test": "Offer an actual pickup-backed trial and observe paid attempts",
            },
            {
                "text": "I might consider it, but I am still unsure whether I trust an "
                        "unknown seller to honor the collection promise.",
                "mechanism": "Trust in the promise may matter as much as logistics",
                "evidence_refs": ["E014", "E020", "E027"],
                "objections": ["Unfamiliar company", "Potential noncompliance"],
                "next_test": "Hold pickup fixed and compare verified seller familiarity",
            },
        ],
    },
    {
        "scenario": "SIM002", "run": "R002",
        "decision": "Would an at-home foam sample enable a joint purchase decision?",
        "intervention": {"variable": "tactile_evaluation",
                         "from": "no shared tactile assessment of the offered foam",
                         "to": "both spouses can handle a take-home foam sample"},
        "design": "Provide a small mattress material sample before ordering",
        "assumption": "Jointly feeling unfamiliar foam is pivotal to commitment",
        "predicted": "An accessible physical sample could improve willingness to buy",
        "disconfirm": "Couples try the sample but still refuse because returns remain hard",
        "fallback": "Focus on seller assurance and reversibility rather than sampling",
        "responses": [
            {
                "text": "I would be more willing to buy if my wife and I could try a "
                        "material sample, but I would still want easy returns.",
                "mechanism": "Shared reassurance about unfamiliar material",
                "evidence_refs": ["E018", "E019", "E021", "E025"],
                "objections": ["Difficult return path"],
                "next_test": "Offer samples while holding the return policy fixed",
            },
            {
                "text": "I would probably not purchase right away if the return "
                        "process remained uncertain, even after feeling the sample.",
                "mechanism": "Tactile familiarity alone leaves reverse-logistics anxiety",
                "evidence_refs": ["E014", "E020", "E021"],
                "objections": ["Failure recovery uncertainty"],
                "next_test": "Keep sampling constant and test guaranteed returns",
            },
        ],
    },
]


def model_vectors(texts: list[str]) -> list[list[float]]:
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise SimulationError("Install fastembed to run the semantic SSR example") from exc
    embedding = TextEmbedding(model_name=MODEL)
    return [array.astype(float).tolist() for array in embedding.embed(texts)]


def scenario_for(checkpoint: Path, entry: dict) -> dict:
    scenario = initialize(checkpoint, ["D01"], EVIDENCE_REFS)
    scenario.update({
        "scenario_id": entry["scenario"],
        "decision": entry["decision"],
        "decision_owner": "Educational case; no product owner has reviewed the study",
        "consequence_if_wrong": "Team could optimize the wrong switching condition",
        "target": "A hypothetical one-person proxy, not a sampled population",
        "baseline": {
            "path_y": "Keep old mattress while experimenting with remedies and searching",
            "observed_result": "Costco purchase occurred; sleep improvement not established",
            "evidence_refs": ["E002", "E006", "E014", "E023"],
        },
        "intervention": entry["intervention"],
        "held_constant": ["Poor home sleep", "Buyer has a spouse", "Mattress price"],
        "outcome_space": ["attempt_purchase", "defer_or_reject"],
        "time_context": "Counterfactual period before the historic Costco purchase",
        "counterfactual_distance": "NEAR_OOD",
        "assumptions": [
            "Reconstructed hypothetical behavior is not directly observed",
            "The stated intent question is distinct from actual buying",
        ],
        "measurement": {
            "construct": CONSTRUCT, "question": QUESTION,
            "scale": "FIVE_POINT_LIKERT", "anchor_version": ANCHOR_VERSION,
        },
        "design_hypothesis": {
            "product_change": entry["design"],
            "critical_assumption": entry["assumption"],
            "predicted_behavior": entry["predicted"],
            "disconfirming_observation": entry["disconfirm"],
            "if_disconfirmed": entry["fallback"],
        },
    })
    # Human review flags remain False and reviewer remains blank.
    return scenario


def demo_run(digest: str, scenario: dict, entry: dict) -> dict:
    model = {
        "model": "GPT-6",
        "model_version": "GPT-6 authored text, not an independent API run",
        "configuration": {
            "origin": "AI-authored illustrative responses",
            "independent_sampling": False,
            "prompt_contract": "free text response to predeclared five-point question",
        },
        "responses": entry["responses"],
    }
    schema_check(model, "model-output.schema.json")
    if any(not set(row["evidence_refs"]) <= set(EVIDENCE_REFS)
           for row in model["responses"]):
        raise SimulationError("Out-of-scope source reference in demonstration")
    return {
        "schema_version": "1.0", "run_id": entry["run"],
        "scenario_id": scenario["scenario_id"],
        "source_checkpoint_sha256": digest,
        "scenario_sha256": sha256_text(json.dumps(scenario, sort_keys=True)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evidence_type": "SIMULATED_ESTIMATE",
        "mode": "PLAUSIBILITY_SPACE", "grade": "L0_ROLEPLAY",
        "measurement": scenario["measurement"],
        "model": model["model"], "model_version": model["model_version"],
        "configuration": model["configuration"],
        "responses": model["responses"], "source_coverage": ["FULL"],
        "coverage_limited": False, "review_status": "AI_CURATED_NOT_HUMAN_APPROVED",
        "limitations": [
            "Teaching artifact, not approved through formal human review-gated record command",
            "GPT-6 authored two variants, not independent samples of a human population",
            "Source interview is one person; no independent validation outcomes exist",
        ],
    }


def embed_document(run: dict, vectors: list[list[float]]) -> dict:
    n = len(run["responses"])
    if len(vectors) != n + 30:
        raise SimulationError("Expected vectors for every response and six times five anchors")
    sets = []
    i = n
    for index, anchors in enumerate(ANCHORS, start=1):
        rows = []
        for rating, phrase in enumerate(anchors, start=1):
            rows.append({"rating": rating, "text": phrase, "vector": vectors[i]})
            i += 1
        sets.append({"id": f"set-{index}", "anchors": rows})
    return {
        "schema_version": "1.0", "run_id": run["run_id"],
        "construct": CONSTRUCT, "embedding_model": MODEL,
        "anchor_version": ANCHOR_VERSION, "epsilon": 0, "temperature": 1,
        "anchor_sets": sets,
        "response_embeddings": [{
            "index": i, "text_sha256": sha256_text(row["text"]),
            "vector": vectors[i],
        } for i, row in enumerate(run["responses"])],
    }


def execute(checkpoint_path: Path, destination: Path) -> None:
    checkpoint, digest = load_checkpoint(checkpoint_path)
    if len(checkpoint["interview_index"]) != 1 or len(checkpoint["episode_index"]) != 1:
        raise SimulationError("The example requires one respondent and one decision episode")
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for entry in CASES:
        scenario = scenario_for(checkpoint_path, entry)
        run = demo_run(digest, scenario, entry)
        folder = destination / entry["scenario"]
        folder.mkdir(parents=True, exist_ok=True)
        write_json(folder / "scenario.json", scenario)
        write_json(folder / "run.json", run)
        output = {
            "model": run["model"], "model_version": run["model_version"],
            "configuration": run["configuration"], "responses": run["responses"],
        }
        write_json(folder / "model-output.json", output)
        input_doc = protocol_input(scenario)
        runs_doc = protocol_runs(run, scenario)
        schema_check(input_doc, "behavioral-input-v0.1.0.schema.json")
        schema_check(runs_doc, "behavioral-runs-v0.1.0.schema.json")
        write_json(folder / "behavioral-input.json", input_doc)
        write_json(folder / "behavioral-runs.json", runs_doc)

        phrases = [row["text"] for row in run["responses"]]
        for anchor_set in ANCHORS:
            phrases.extend(anchor_set)
        vectors = model_vectors(phrases)
        spec = embed_document(run, vectors)
        write_json(folder / "ssr-vectors.json", spec)
        outcome = measure(run, spec)
        write_json(folder / "ssr.json", outcome)
        (folder / "simulation-report.md").write_text(
            "# CANONICAL EDUCATIONAL DEMONSTRATION — NOT HUMAN REVIEWED\n\n"
            "These are synthetic GPT-6-authored statements, not simulated independent "
            "population samples. SSR used BAAI/bge-small-en-v1.5, not the paper's "
            "embedding model. No human holdout exists.\n\n"
            + render(scenario, run, outcome), encoding="utf-8"
        )
        expected = sum((i + 1) * p for i, p in enumerate(outcome["aggregate"]))
        results.append({
            "scenario": entry["scenario"], "run_id": run["run_id"],
            "five_rating_probabilities": outcome["aggregate"],
            "illustrative_mean_rating": expected,
            "model": "GPT-6 authored hypothetical text",
            "embedding_model": MODEL,
            "human_validation": "NONE",
            "evidence_grade": "L0_ROLEPLAY",
        })
    write_json(destination / "summary.json", {
        "status": "UNVALIDATED_EDUCATIONAL_DEMONSTRATION",
        "human_participants": 1, "human_holdouts": 0,
        "model": "GPT-6 authored illustrative alternative responses",
        "anchor_sets": len(ANCHORS),
        "rating_question": QUESTION,
        "embedding_model": MODEL,
        "scenarios": results,
        "limitations": [
            "No human outcome prediction accuracy can be inferred",
            "SSR allocation describes similarity of written synthetic responses to anchors",
            "Synthetic alternatives are neither independent samples nor real purchase behavior",
            "Embedding model and anchors differ from published SSR experiment",
            "No reviewer approved the original codebook or links for formal research use",
        ],
    })
    print(json.dumps(results, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    execute(args.checkpoint, args.output_dir)


if __name__ == "__main__":
    main()
