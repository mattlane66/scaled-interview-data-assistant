# Canonical real interview — the mattress switch

**Source:** [The Mattress Interview, Part One](https://jobstobedone.org/radio/the-mattress-interview-part-one/), from the Jobs-to-be-Done Radio workshop with Bob Moesta and Chris Spiek.

**Authorized source use:** The repository owner has confirmed a license to reproduce the complete published interview here. This example retains the entire published transcript, including the teaching explanations and audience exchanges. It is not a freshly transcribed audio recording.

**Pinned source snapshot:** 279 speaker turns (99 participant, 157 facilitator, 23 audience), plus 21 marked editorial blocks. The website contained 182 duplicate speaker turns due to nested/repeated HTML, which the importer collapsed. [The source manifest](source-manifest.json) records the exact published-page hash and import date.

## Independent analytical reference and product decision

The [independent full-transcript audit](reference/independent-audit.md)
reconstructs the switching chronology, inspects the original A→B relationships,
identifies ten corrections or evidence limitations, and compares five rival
behavioral explanations. Its recommendation is **a live experiment, not a
product launch**: hold mattress, seller and price constant while testing genuine
no-cost return pickup and a shared material sample as separate factors.

The [frozen expected-analysis contract](reference/expected-analysis.json) and
[evaluation rubric](reference/evaluation-rubric.md) provide source-located,
machine-checkable expectations for future analyses. They distinguish actual
participant reports from inferred mechanisms and prohibit turning two
educational SSR values into a product ranking.

**Approval boundary:** This reference is `AI_AUDITED_CANDIDATE_PENDING_HUMAN_ADJUDICATION`.
It is not an independently approved research baseline. The original registries
and checkpoints remain unchanged pending adjudication; disagreements about
A01, L003, and enabling conditions versus desired progress are recorded for
review rather than silently recoded.

## The evidence boundary

The complete source is in [full-transcript.md](full-transcript.md), indexed in [source-turns.json](source-turns.json), with source-page hash and completeness notes in [source-manifest.json](source-manifest.json). The published webpage contained repeated HTML dialogue blocks; the importer removes identifiable duplicates while preserving the final original wording. The HTML is fetched again only when the source importer workflow is explicitly triggered.

The teaching recording switches between interview ("game on"), instructor commentary ("game off"), and audience questions. **Only the participant's actual answers can directly establish the participant's reported experience.** Their answer to a hypothetical question is hypothetical evidence, not an actual choice.

The source is one real person describing one bounded decision. It cannot support a cross-person cluster, an independent SSR human holdout, or a validated behavioral forecast.

## From complete source to working analysis

| Stage | Canonical file | Status |
|---|---|---|
| Full published source and transcript provenance | `full-transcript.md`, `source-turns.json`, `source-manifest.json` | Reproduced from published website, not audio-verified |
| Interview/episode/segment registries | `interviews.json`, `episodes.json`, `segments.json` | One real participant, one decision episode |
| Source-located evidence bank | `evidence_bank.json`, `sources.json` | 28 contiguous excerpts, each checked against actual participant turns |
| A/B coding and decision links | `codebook.json`, `evidence_mappings.json`, `links.json` | AI-curated, interpretive, **not human-reviewed** |
| Single-episode synthesis | `synthesis_report.md` | Explicit `VERIFIED/INFERRED/SPECULATIVE` distinction |
| Deterministic software pipeline | `results/CHECKPOINT.json`, `results/matrices/` | Runnable; no job clustering |
| Hypothetical design conditions | `results/simulations/SIM001/`, `SIM002/` | AI-authored, `L0_ROLEPLAY`, not human responses |
| Behavior Simulation protocol handoff | `behavioral-input.json`, `behavioral-runs.json` in each scenario | Pinned v0.1.0 file contract; not a complete validated study |
| Semantic Similarity Rating | `ssr-vectors.json`, `ssr.json`, `simulation-report.md` in each scenario | Actual semantic embeddings and six sets of five 1–5 anchors; **not calibrated** |
| Human validation | None | **NOT DONE:** no independent holdout, no test of actual buying behavior |
| Cross-episode mechanism map | None | **NOT APPLICABLE:** one interview only |
| Planning Skills acceptance | None | **NOT DONE:** proposed hypotheses cannot automatically become accepted M or R |

## Running the complete canonical study

From the repository root, install development dependencies and the optional public-source/embedding adapters:

```bash
python -m pip install -e ".[dev]"
python -m pip install beautifulsoup4 fastembed
```

To reconstruct the source snapshot from the website (requires the source page to remain accessible):

```bash
python scripts/import_canonical_mattress.py --output-dir examples/canonical-mattress
```

Use the saved `source-turns.json` in the canonical folder instead when reproducing the version committed here. Fetching the live page may change source hashes or speaker-turn numbering.

Generate **provisional** human-analysis registries and run the built-in validators, association matrices, checkpoint, and report audit:

```bash
python scripts/build_canonical_mattress.py --folder examples/canonical-mattress

python scripts/run_pipeline.py \
  --sources examples/canonical-mattress/sources.json \
  --interviews examples/canonical-mattress/interviews.json \
  --episodes examples/canonical-mattress/episodes.json \
  --segments examples/canonical-mattress/segments.json \
  --source-root examples/canonical-mattress \
  --evidence examples/canonical-mattress/evidence_bank.json \
  --codebook examples/canonical-mattress/codebook.json \
  --mappings examples/canonical-mattress/evidence_mappings.json \
  --links examples/canonical-mattress/links.json \
  --report examples/canonical-mattress/synthesis_report.md \
  --clusters none \
  --output-dir examples/canonical-mattress/results
```

Run the canonical hypothetical simulations and calculate the SSR ordinal distributions:

```bash
python scripts/run_canonical_mattress_demo.py \
  --checkpoint examples/canonical-mattress/results/CHECKPOINT.json \
  --output-dir examples/canonical-mattress/results/simulations
```

The demonstration uses two prewritten, context-grounded **GPT-6-authored hypothetical response variants** for each of two alternative conditions:

1. Guaranteed home pickup if the mattress fails to work.
2. A sample the buyer and spouse can handle before purchasing.

Those statements were created for this educational case, **not generated as independent draws by a separate LLM API**, and were not said by the respondent. They deliberately challenge the underlying switching mechanism: ease of recovery versus trusted seller and joint tactile evaluation.

SSR is computed over the actual written synthetic text using the open `BAAI/bge-small-en-v1.5` embedding model and six sets of five original verbal anchors. The [SSR study](https://arxiv.org/abs/2510.08338) used a different embedding configuration and evaluation dataset. Its published results are **not evidence of this case's accuracy**.

The `ssr.json` probability vector is a semantic allocation over five hypothetical stated-intent categories. It is **not** the probability that this respondent or anyone else will buy. Two authored variants are not statistically independent samples. No `L2`–`L4` confidence claim is made.

## Important distinction: fully runnable is not fully human-approved

The original analysis is **AI_CURATED_NOT_HUMAN_APPROVED**. The standard simulation `prepare` and `record` commands deliberately require actual human approval of source excerpts and A/B links. This example **does not turn those review flags on**. The tutorial's L0 simulation artifacts are separate teaching outputs, not formal human-reviewed simulation runs.

A reviewer who wants to make this a research-valid baseline should verify the 28 selections against their original `T####` turns, reconsider omissions, coding, links, and contradictions, and explicitly approve those decisions. Only then should a new reviewed scenario be produced with the ordinary gated workflow. Even then, genuine independent behavioral validation is needed before making predictive or causal claims.

## Why the actual interview matters

The case illustrates why a decision that appeared impulsive at Costco should not be reduced to an impulse-buying persona: the respondent describes long-term discomfort, earlier costly regret, a near Groupon purchase, showroom aversion, his spouse's tactile assessment, and a familiar return path. He also says the old mattress was still in use. The last point demonstrates why purchase and successful Point B progress must be reported separately.

Neither expert facilitator commentary nor a synthetic model's plausible answers may be inserted into the participant's evidence bank. Follow the canonical guide from the original source outward; do not use the teaching synthesis as a source of new customer facts.

## Supporting examples

The repository also preserves [an original synthetic one-interview teaching case](../mattress/README.md) and [a synthetic three-interview study](../synthetic-study/README.md). The multi-interview fixture, not this single real participant, is the appropriate place to test cross-person cluster and mechanism-map software behavior.
