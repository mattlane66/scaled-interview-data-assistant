# CANONICAL EDUCATIONAL DEMONSTRATION — NOT HUMAN REVIEWED

These are synthetic GPT-6-authored statements, not simulated independent population samples. SSR used BAAI/bge-small-en-v1.5, not the paper's embedding model. No human holdout exists.

# Evidence-grounded simulation report

**Scenario:** SIM002 | **Run:** R002
**Question:** Would an at-home foam sample enable a joint purchase decision?
**Owner:** Educational case; no product owner has reviewed the study
**Mode:** PLAUSIBILITY_SPACE | **Evidence grade:** L0_ROLEPLAY
**Source type:** SIMULATED_ESTIMATE (never OBSERVED_HUMAN)

## Observed grounding and assumptions

- Read-only checkpoint: `sha256:5a9482de8687dcf4ff9753769cbf9d34008644a52d4541255831e48841c329a6`
- Human episode references: D01
- Source evidence IDs: E002, E006, E008, E014, E015, E018, E019, E020, E021, E023, E024, E025, E027
- Coverage: FULL
- Baseline evidence IDs: E002, E006, E014, E023
- Baseline Path Y: Keep old mattress while experimenting with remedies and searching
- Observed Path X result: Costco purchase occurred; sleep improvement not established
- Changed: tactile_evaluation (no shared tactile assessment of the offered foam → both spouses can handle a take-home foam sample)
- Held constant: Poor home sleep, Buyer has a spouse, Mattress price
- Counterfactual distance: NEAR_OOD
- Assumptions: Reconstructed hypothetical behavior is not directly observed; The stated intent question is distinct from actual buying

## Simulated possibilities (not actual customer responses)

### Candidate 1

**Generated statement:**
> I would be more willing to buy if my wife and I could try a material sample, but I would still want easy returns.

**Hypothesized mechanism:** Shared reassurance about unfamiliar material
**Grounding cited:** E018, E019, E021, E025
**Objections:** Difficult return path
**Next human test:** Offer samples while holding the return policy fixed

### Candidate 2

**Generated statement:**
> I would probably not purchase right away if the return process remained uncertain, even after feeling the sample.

**Hypothesized mechanism:** Tactile familiarity alone leaves reverse-logistics anxiety
**Grounding cited:** E014, E020, E021
**Objections:** Failure recovery uncertainty
**Next human test:** Keep sampling constant and test guaranteed returns

## Quantitative measurement

Predeclared question: Under the proposed conditions, how likely are you to attempt a mattress purchase?
Construct: hypothetical_stated_purchase_intent; externally supplied embeddings: BAAI/bge-small-en-v1.5; anchors: mattress-intent-anchors-v1.

Generated-response ordinal rating distribution (1–5): 0.1087, 0.2599, 0.3119, 0.1816, 0.1378

**Not** a calibrated population adoption or switching probability.

## Held-out validation

NOT VALIDATED: no real held-out outcomes evaluated.

## Decision boundary

Use these outputs to select a real interview, prototype, or experiment; not as new A/B codes, observed switching facts, population prevalence, causal treatment effects, willingness to pay, or a business decision.

Human evidence establishes what happened; simulation explores what might happen; independent validation is needed to establish predictive performance.
