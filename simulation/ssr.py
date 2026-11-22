"""Provider-neutral semantic similarity rating over externally supplied embeddings.

Based on Maier et al., arXiv:2510.08338v3. Semantic resemblance is not
evidence of human purchasing or switching behavior.
"""
from __future__ import annotations

import json
import math
from typing import Any

from simulation.core import SimulationError, schema_check, sha256_text


def _vector(value: object) -> list[float]:
    if not isinstance(value, list) or not value:
        raise SimulationError("Embedding vectors must be nonempty arrays")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in value):
        raise SimulationError("Embedding contains a nonnumeric element")
    vector = [float(x) for x in value]
    if not all(math.isfinite(x) for x in vector) or not any(x != 0 for x in vector):
        raise SimulationError("Embedding is zero or nonfinite")
    return vector


def cosine(a: object, b: object) -> float:
    va, vb = _vector(a), _vector(b)
    if len(va) != len(vb):
        raise SimulationError("Mismatched embedding dimensions")
    numerator = math.fsum(x * y for x, y in zip(va, vb, strict=True))
    den = math.sqrt(math.fsum(x * x for x in va) * math.fsum(y * y for y in vb))
    if den <= 0 or not math.isfinite(den):
        raise SimulationError("Invalid embedding norm")
    return max(-1.0, min(1.0, numerator / den))


def distribution(vector: list[float], anchor_vectors: list[list[float]],
                 epsilon: float = 0.0, temperature: float = 1.0) -> list[float]:
    if len(anchor_vectors) != 5 or epsilon < 0 or temperature <= 0:
        raise SimulationError("SSR needs five anchors, epsilon >= 0, and temperature > 0")
    if not math.isfinite(epsilon) or not math.isfinite(temperature):
        raise SimulationError("SSR parameters must be finite")
    similarities = [cosine(vector, anchor) for anchor in anchor_vectors]
    minimum = min(similarities)
    weights = [max(0.0, s - minimum + epsilon) ** (1.0 / temperature)
               for s in similarities]
    total = math.fsum(weights)
    if total <= 0 or not math.isfinite(total):
        raise SimulationError("Anchor set is degenerate; cannot create an SSR distribution")
    return [value / total for value in weights]


def _mean(distributions: list[list[float]]) -> list[float]:
    size = len(distributions)
    if size == 0:
        raise SimulationError("No distributions")
    output = [math.fsum(row[i] for row in distributions) / size for i in range(5)]
    total = math.fsum(output)
    return [x / total for x in output]


def measure(run: dict[str, Any], vectors: dict[str, Any]) -> dict[str, Any]:
    schema_check(vectors, "ssr-input.schema.json")
    if vectors["run_id"] != run.get("run_id"):
        raise SimulationError("SSR vectors do not reference this simulation run")
    declared = run.get("measurement")
    if not isinstance(declared, dict) or not declared.get("question"):
        raise SimulationError("SSR requires a predeclared fixed ordinal question")
    if (declared["construct"] != vectors["construct"]
            or declared["anchor_version"] != vectors["anchor_version"]
            or declared["scale"] != "FIVE_POINT_LIKERT"):
        raise SimulationError("SSR construct, anchors or scale differ from approved scenario")
    responses = run.get("responses", [])
    supplied = vectors["response_embeddings"]
    if len(supplied) != len(responses):
        raise SimulationError("Must provide one embedding per generated response")
    if len({e["index"] for e in supplied}) != len(responses):
        raise SimulationError("Duplicate response embedding indices")
    anchors = vectors["anchor_sets"]
    if len({row["id"] for row in anchors}) != len(anchors):
        raise SimulationError("Anchor-set IDs must be unique")
    epsilon, temperature = vectors["epsilon"], vectors["temperature"]
    by_index = {entry["index"]: entry for entry in supplied}
    individual = []
    for index, response in enumerate(responses):
        entry = by_index.get(index)
        if entry is None or entry["text_sha256"] != sha256_text(response["text"]):
            raise SimulationError("Response embedding does not match generated response text")
        per_set = []
        for statement_set in anchors:
            ordered = sorted(statement_set["anchors"], key=lambda x: x["rating"])
            if [item["rating"] for item in ordered] != [1, 2, 3, 4, 5]:
                raise SimulationError("Each anchor set must cover ratings 1 through 5 once")
            pmf = distribution(entry["vector"], [a["vector"] for a in ordered],
                               epsilon=epsilon, temperature=temperature)
            per_set.append(pmf)
        mean = _mean(per_set)
        sensitivity = max(
            0.5 * math.fsum(abs(x - y) for x, y in zip(row, mean, strict=True))
            for row in per_set
        )
        individual.append({"response_index": index, "rating_probabilities": mean,
                           "max_anchor_set_tvd": sensitivity})
    return {
        "schema_version": "1.0", "run_id": run["run_id"],
        "run_sha256": sha256_text(json.dumps(run, sort_keys=True)),
        "evidence_type": "SIMULATED_ESTIMATE",
        "construct": vectors["construct"], "embedding_model": vectors["embedding_model"],
        "anchor_version": vectors["anchor_version"],
        "anchor_set_count": len(anchors), "epsilon": epsilon, "temperature": temperature,
        "per_response": individual,
        "aggregate": _mean([row["rating_probabilities"] for row in individual]),
        "note": ("SSR measures generated textual attitudes, not actual switching "
                 "probabilities; external embedding provenance is self-reported."),
    }
