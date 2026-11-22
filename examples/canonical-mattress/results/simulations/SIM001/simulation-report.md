# CANONICAL EDUCATIONAL DEMONSTRATION — NOT HUMAN REVIEWED

These are synthetic GPT-6-authored statements, not simulated independent population samples. SSR used BAAI/bge-small-en-v1.5, not the paper's embedding model. No human holdout exists.

# Evidence-grounded simulation report

**Scenario:** SIM001 | **Run:** R001
**Question:** Would guaranteed home return pickup help overcome switching anxiety?
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
- Changed: return_logistics (uncertain customer-organized return → free home pickup after an unsatisfactory trial)
- Held constant: Poor home sleep, Buyer has a spouse, Mattress price
- Counterfactual distance: NEAR_OOD
- Assumptions: Reconstructed hypothetical behavior is not directly observed; The stated intent question is distinct from actual buying

## Simulated possibilities (not actual customer responses)

### Candidate 1

**Generated statement:**
> I would probably buy if someone reliably picked up the mattress and refunded me if it did not work, but I would still check with my wife.

**Hypothesized mechanism:** Reduced anticipated loss or disposal burden
**Grounding cited:** E014, E019, E020, E027
**Objections:** Seller credibility; Spouse's agreement
**Next human test:** Offer an actual pickup-backed trial and observe paid attempts

### Candidate 2

**Generated statement:**
> I might consider it, but I am still unsure whether I trust an unknown seller to honor the collection promise.

**Hypothesized mechanism:** Trust in the promise may matter as much as logistics
**Grounding cited:** E014, E020, E027
**Objections:** Unfamiliar company; Potential noncompliance
**Next human test:** Hold pickup fixed and compare verified seller familiarity

## Quantitative measurement

Predeclared question: Under the proposed conditions, how likely are you to attempt a mattress purchase?
Construct: hypothetical_stated_purchase_intent; externally supplied embeddings: BAAI/bge-small-en-v1.5; anchors: mattress-intent-anchors-v1.

Generated-response ordinal rating distribution (1–5): 0.1094, 0.1748, 0.3117, 0.2133, 0.1909

**Not** a calibrated population adoption or switching probability.

## Held-out validation

NOT VALIDATED: no real held-out outcomes evaluated.

## Decision boundary

Use these outputs to select a real interview, prototype, or experiment; not as new A/B codes, observed switching facts, population prevalence, causal treatment effects, willingness to pay, or a business decision.

Human evidence establishes what happened; simulation explores what might happen; independent validation is needed to establish predictive performance.
