# Evidence-grounded simulation (optional)

This extension lives **after** the reviewed JTBD/A2B workflow. It never changes the interview evidence bank,
A/B codes, links, job clusters, or original checkpoint.

The governing methodology is
[Behavioral Simulation for Agents and Humans](https://github.com/mattlane66/behavioral-simulation-for-agents-and-humans/blob/main/behavioral-simulation/PROTOCOL.md).
[Semantic Similarity Rating (SSR)](https://arxiv.org/abs/2510.08338) is an **optional**
measurement technique for generated ordinal attitudes, not a substitute for discovery interviews
or observed purchasing and switching behavior.

## What is implemented

- A strict, read-only checkpoint adapter with SHA-256 identity, source evidence ownership checks,
  and an explicit human review attestation bound to exactly that checkpoint.
- Scenario templates for a baseline Path Y, a named intervention, constants, possible outcomes,
  temporal scope, assumptions, and counterfactual distance.
- A minimized prompt packet containing no excerpts by default; exposing verbatim excerpts requires
  explicit approval of model processing in the scenario and the `--include-verbatim` flag.
- An independent `SIMULATED_ESTIMATE` run artifact. A model operates **outside** this repository
  and returns structured text. The deterministic record step rejects invented or foreign evidence IDs.
- Optional vector-based SSR: subtract the minimum cosine similarity to five anchors, normalize,
  optionally apply a temperature, average across anchor sets and generated responses, and retain
  anchor sensitivity. Use six preregistered anchor sets for faithful reproduction of the paper's
  experiment. The paper used `text-embedding-3-small`; this tool **does not** generate embeddings.
- Optional person-grouped ordinal holdout comparison (TVD, KS similarity, and a baseline), with
  leakage checks against **all** interviews in the source checkpoint. Holdout permission,
  predeclaration, and isolation are attested, not independently proven.
- A separate report that keeps observation, assumptions, synthetic estimates, and validation distinct.

## Evidence-first product design counterfactuals

Use [counterfactual decisions](counterfactual-decisions.md) if your first goal is to
decide **which product assumption to test** using real interview findings. It can
produce a human-grounded decision brief and compare different design moves **without**
model generation, embeddings, or SSR. This simulation workflow remains an optional
additional layer for rival mechanisms and ordinal attitude measurements.

## Start from a validated source checkpoint

Produce `outputs/CHECKPOINT.json` via the normal `scripts/run_pipeline.py` or
`scripts/export_checkpoint.py`. Review its evidence bank, A/B links, and (if present) clustering
before authorizing simulation. A technically valid checkpoint is **not** evidence that review occurred.

~~~bash
python scripts/simulation_cli.py init \
  --checkpoint outputs/CHECKPOINT.json \
  --episode D01 --evidence E001 --evidence E002 \
  --output data/scenario.json
~~~

Edit `data/scenario.json`: enter an actual decision, decision owner, known baseline, change,
held-constant conditions, possible outcomes, and explicit assumptions. Set
`review.reviewer`, `review.evidence_reviewed`, `review.codebook_links_reviewed`, and
`review.clusters_reviewed` where applicable **only after actual review**. Keep
`review.approved_checkpoint_sha256` unchanged. To process excerpts using a model, verify the
research permissions and provider controls and set `review.processing_permitted` to true.
Do not assume review has happened because a flag is present.

~~~bash
python scripts/simulation_cli.py prepare \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --include-verbatim --output data/simulation-packet.json
~~~

**No data is sent to a provider by this command.** The packet is stored locally; handle it
as restricted interview data. Without `--include-verbatim`, the packet is deliberately
insufficient for grounding and warns of that limitation. Verify the actual model provider's
retention, training, and access controls before sending any packet to it.

## Generate and record a synthetic run

Give an authorized model the packet's `generation_instructions`, scenario, and evidence.
The returned **model-output JSON** must follow
[`simulation/schemas/model-output.schema.json`](../../simulation/schemas/model-output.schema.json):

~~~json
{
  "model": "your-model",
  "model_version": "exact-model-version",
  "configuration": {"temperature": 0.5, "prompt_version": "sim-1"},
  "responses": [{
    "text": "I might try it, but need to know whether switching is reversible.",
    "mechanism": "Reduced migration effort versus remaining anxiety",
    "evidence_refs": ["E001"],
    "objections": ["Uncertain reversibility"],
    "next_test": "Offer a reversible real-world migration trial."
  }]
}
~~~

This is an **illustrative generated response, not a human interview or empirical finding**.
Never place it in the `evidence_bank.json` or assign `E###`, `D##`, `L###`, or `C##` IDs.

~~~bash
python scripts/simulation_cli.py record \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --model-output data/model-output.json --run-id R001 --output outputs/sim-run.json

python scripts/simulation_cli.py report \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --run outputs/sim-run.json --output outputs/simulation-report.md
~~~

Changing the checkpoint or scenario after recording invalidates the run. The generated-response
text and its evidence citations are **model claims**. The CLI cannot independently prove the
model was given the packet, verify provider identity, or detect whether the model paraphrased
grounding accurately; human review remains essential.

## Optional handoff to the companion Behavioral Simulation skill

The companion repository is a file-backed skill, not a stable Python library. This adapter pins
its `input.json` and `runs.json` v0.1.0 contracts to upstream commit
`c11d29c8d121728306037dd799669bb0ef7cfabf`. It checks both exported documents against
copies of those exact schemas. No upstream code is executed and no upload occurs.

~~~bash
python scripts/simulation_cli.py handoff \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --run outputs/sim-run.json --output-dir outputs/upstream-study
~~~

The files are compatible with the upstream study's **input/run** artifacts, not a complete
upstream study bundle. Downstream validation and calibration remain governed by the full
[Behavioral Simulation Protocol](https://github.com/mattlane66/behavioral-simulation-for-agents-and-humans/blob/c11d29c8d121728306037dd799669bb0ef7cfabf/behavioral-simulation/PROTOCOL.md).
If its schema version changes, review the mapping instead of silently assuming compatibility.

## Optional SSR (not an adoption forecast)

SSR can only be calculated when the approved scenario contains a fixed, predeclared ordinal
measurement. Add this object **before review and model generation**:

~~~json
{
  "measurement": {
    "construct": "stated_switching_intent",
    "question": "How likely would you switch under the proposed conditions?",
    "scale": "FIVE_POINT_LIKERT",
    "anchor_version": "switch-intent-v1"
  }
}
~~~

This is an excerpt to add to `scenario.json`, not a complete scenario. The model must answer
the exact question with a short, standalone first-person statement in `responses[].text`;
put hypothesized mechanisms, objections, and tests in their separate fields. Do **not** use
SSR on general narratives or explanations of behavior. The tool validates the declared
construct and anchor version, but cannot semantically verify that the generated answer
actually addressed the question. Review it before interpreting the distribution.


Supply an external embedding model's vectors in a JSON document meeting
[`simulation/schemas/ssr-input.schema.json`](../../simulation/schemas/ssr-input.schema.json).
Provide one vector per generated response, its SHA-256 text hash, the embedding model/version,
and 2+ unique reference sets of five anchor texts and their vectors (six recommended).
Embeddings must be generated consistently, using the same model and preprocessing;
the CLI cannot verify external embeddings were produced honestly or consistently.
The SSR defaults `epsilon=0` and `temperature=1` follow the primary analysis in
[Maier et al., Appendix A.4.3](https://arxiv.org/abs/2510.08338v3).
Set `"transform": "MAIER_V3_SINGLE_MINIMUM"` in the vectors file for Eq. 8–9.
This adds positive epsilon only to the first minimum in rating order and
expresses epsilon in raw cosine units. To match the authors' library, which
rescales cosine to [0,1], supply twice the library's epsilon. The output records
an explicitly supplied transform. Existing files with no transform retain the
uniform-epsilon calculation and their original output format. At zero epsilon
both transforms give the same PMF for nondegenerate anchors. Compare tuned
parameters on development data before scoring a held-out construct.
The paper-mode quality check refuses equal similarities across all anchors,
including when positive epsilon would make the literal formula one-hot.
Version and freeze the exact anchors, embedding model, transform, epsilon and
temperature before seeing holdout outputs. The scenario binds the construct and
anchor version. The vectors supply the transform and settings, so their prior
selection and the anchor content remain external attestations. The evaluation
binds the measurement artifact after scoring. Keep separate per-set outputs if
needed. The standard output summarizes sensitivity as the maximum per-set TVD
from the mean PMF per response.

~~~bash
python scripts/simulation_cli.py ssr \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --run outputs/sim-run.json --vectors data/ssr-vectors.json \
  --output outputs/sim-ssr.json
~~~

The per-response and aggregate probabilities are **ordinal rating allocations over generated
text**, not probabilities that humans will actually adopt, pay, or switch. Anchor selection matters;
the cited paper manually optimized anchors on its evaluation surveys, so test on unseen studies.

## Optional human holdout comparison

Create a **predeclared** validation input matching
[`simulation/schemas/holdout.schema.json`](../../simulation/schemas/holdout.schema.json).
It requires person-grouped holdout IDs absent from all source interviews, approved collection/use,
a defined target construct and **the exact approved question**, one human Likert response
for each unique holdout person ID, and a naive distributional baseline.
These fields do not, by themselves, prove true independence. Keep human holdout responses
completely outside the grounding checkpoint and model packet.

~~~bash
python scripts/simulation_cli.py evaluate \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --run outputs/sim-run.json --measurement outputs/sim-ssr.json \
  --holdout data/human-holdout.json --output outputs/sim-validation.json

python scripts/simulation_cli.py report \
  --checkpoint outputs/CHECKPOINT.json --scenario data/scenario.json \
  --run outputs/sim-run.json --measurement outputs/sim-ssr.json \
  --validation outputs/sim-validation.json \
  --output outputs/simulation-report.md
~~~

The validation result is bound to the exact scenario, run, and SSR measurement by their hashes.
The report rejects mismatched combinations. These hashes detect accidental substitution but are
not cryptographic signatures of independent human review. The model-output timestamp is the
**time the external output was recorded by the CLI**, not a verified time of model generation;
predeclaration timing remains an analyst attestation.

The automated evaluator checks declared group overlap and timing, but cannot establish
undocumented model exposure, duplicate/aliased identities, or generalization to unobserved
conditions. It **never automatically promotes** the evidence grade to
`L3_HELD_OUT_VALIDATED` or `L4_DECISION_CALIBRATED`. Those require further independent review
and task-specific metrics, subgroup assessment, calibration, and drift controls per the governing
protocol. Holdout statements of intent are not observed purchases.

## Scope and failure behavior

The first executable integration supports `PLAUSIBILITY_SPACE` (`L0_ROLEPLAY`) and narrowly
`INDIVIDUAL_PROXY` (`L1_PERSON_GROUNDED`) only. The latter requires one real interview's
episode(s) and explicit person-grounding review; it is **not** population evidence.
`POPULATION_PREDICTION`, `MULTI_AGENT_DYNAMICS`, automatic L2–L4 promotion, model API calls,
actual intervention-effect claims, and autonomous decision making are intentionally unavailable.

If evidence is incomplete, keep `UNKNOWN`, preserve disagreement, and choose a human test.
Valid outputs expand hypotheses; they do not independently prove jobs, causal forces, prevalence,
willingness to pay, opportunity size, or that a product should ship.

## Test and privacy guard

~~~bash
python -m pytest -q
python -m ruff check .
~~~

Only fictional examples and code belong in Git. `data/`, `outputs/`, original transcripts,
model prompt packets, generated proxies, and holdout responses must remain restricted, local or
stored under an approved research system. Do not use simulations as the sole basis for high-impact
decisions about individuals.
