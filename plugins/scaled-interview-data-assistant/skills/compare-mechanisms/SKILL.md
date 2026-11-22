---
name: compare-mechanisms
description: Compare rival reasons for different customer decisions across reviewed JTBD episodes and produce a provisional behavioral mechanism map, never a causal effect estimate.
---

# Compare behavioral mechanisms

Use reviewed, source-bound decision episodes and their A→B links. Do not treat clustering or code co-occurrence as an explanation. Distinguish **ALIGNS**, **COUNTEREXAMPLE**, **AMBIGUOUS**, and **UNASSESSED**. An unassessed case is not a negative case; multiple episodes from one interview are not independent respondents.

For each proposed mechanism record:
- relevant operating condition and hypothesized relationship, separate from candidate solution claims
- source-located observations, contrary evidence, distinct respondent coverage and limitations
- at least one rival explanation, a counterfactual condition change, a disconfirming observation and the smallest credible human test

When tools are connected, call `check_checkpoint` to verify the exact input, `draft_mechanism_map` to create an **unapproved** study, and `preview_mechanism_evidence` to inspect coverage. Call `compile_reviewed_mechanism_map` only after actual human evidence/link/contrasting-case review. Never manufacture reviewer names, approval flags or review dates. The compiled map remains PROVISIONAL even if the review attestation is present.

Do not generate invented interviewees, claim mechanism prevalence, estimate behavior from isolated synthetic text, or treat the educational mattress SSR scores as purchasing probabilities. A counterfactual is a **testable hypothesis**, not observed behavior.

Follow [the methodology](https://github.com/mattlane66/scaled-interview-data-assistant/blob/main/docs/operations/mechanism-map.md) and clearly identify which steps were computed versus reasoned.
