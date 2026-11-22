# Canonical Mattress: Adjudication and Evaluation Rubric

This rubric is for evaluating an analysis against the **complete real interview**, not against the previous assistant's answer. It is a reproducible research-quality checklist, **not** a predictive model benchmark or a human-approved ground truth.

**Source basis:** [279-turn frozen transcript](../source-turns.json), [full source](../full-transcript.md), and [machine-checkable findings](expected-analysis.json). All candidate interpretations remain open to human revision.

## Core evidence checks

| Check | A satisfactory analysis must establish | Original source |
|---|---|---|
| **R1 — Switch chronology** | Original dissatisfaction preceded the unexpected Costco encounter by many months; active research preceded purchase | `T0102 T0106 T0190 T0088 T0094` |
| **R2 — What was sought** | Restored sleep and everyday functioning, not foam as an end in itself | `T0190 / E015` |
| **R3 — How old Path Y persisted** | Tried changing sleep setup, delayed during family/work/move, and considered an alternative sale | `T0108 T0114 T0134 T0136 T0190` |
| **R4 — Failure-recovery concern** | Participant linked Groupon reluctance to previous Macy's disappointment and uncertain reversibility | `T0164 T0166 T0168 T0190 T0200` |
| **R5 — Purchase circumstances** | The spouse's hesitation, touch of a foam sample, reported assent, and physically obtaining the mattress are reconstructed | `T0196 T0200 T0210 T0212` |
| **R6 — Outcome boundary** | Purchase is observed; better sleep is **unknown**. He still kept/used the old bed and said the issue was unresolved | `T0182 T0184 T0241` |
| **R7 — Rival accounts** | At least recoverability/trust, joint evaluation, and opportunity/timing are presented as competing or interacting hypotheses | `T0190 T0196 T0200 T0216` |
| **R8 — Source types** | Facilitators' game-off theory, audience anecdotes, and the interviewee's hypotheticals are separate from what the participant did | `T0220 T0223 T0237 T0270–T0276` |
| **R9 — Original purchase contrast** | Original mattress at Macy's (including spouse's pregnancy and uncle), plus reported hotel contrast, are kept separate from the new purchase | `T0102 T0112 T0160 T0164 T0258` |
| **R10 — Contradictory cases** | Showroom aversion coexists with reported prior lying on a store mattress; a positive effect of the new mattress is not invented | `T0243 T0251 T0258` |

## Material failure conditions

A candidate analysis **fails this reference evaluation** if it:

1. Calls the purchase a spontaneous need for a mattress with no earlier search or dissatisfaction.
2. Asserts home-return pickup caused the historical Costco purchase: pickup was introduced during the workshop afterward.
3. Treats buying or keeping a new mattress as proof of better sleep or a successful Point B.
4. Reports a controlled willingness-to-pay premium from the $699 Costco purchase versus the cheaper Groupon alternative.
5. Treats the two authored SSR scores as observed customer intent, conversion rates, predictive accuracy, or evidence that one intervention beats the other.
6. Presents facilitator/audience conjectures, the Walgreens counterfactual, or partner testimony as independently observed behavior.
7. Infers a population mechanism or prevalence from this single interview.
8. Presents any of the four AI-curated A→B links as independently human-approved.

A reviewer may accept a candidate that flags uncertainty and proposes a discriminating test. A candidate cannot pass solely by containing the correct words or references.

## Structural checks and review procedure

The automated test `tests/test_canonical_reference.py` checks that reference IDs resolve to the pinned actual transcript, evidence locators belong to the participant, rival hypotheses are sourced, and the decision document remains in **TEST_ONLY** status with no human approval. These tests establish **reference integrity**, not interpretive correctness.

For a future change to the assistant, produce a fresh, blind analysis from the full transcript (do not show it this reference), then have an independent human reviewer use R1–R10 and the hard failures. Record disputed interpretations with source turn IDs, arguments for/against, and a revised canonical edition if approved. Do not alter the original transcript to make the expected analysis pass.

## Proposed decision benchmark

A useful outcome is not whether an assistant chooses “returns” as a winning feature. It is whether the assistant:

- Correctly distinguishes purchase triggering conditions from the desired progress.
- Preserves the competing causes and the *negative* or unresolved evidence.
- Proposes a genuine **behavioral** test with identifiable alternatives, a primary observable outcome, and feasible logistics.
- Explicitly declines to make unsupported causal, predictive, and SSR-ranking claims.
- Hands over research-to-shaping inputs as *proposed x/y/M* and leaves `f()` unselected.

**Acceptance state:** `PENDING_INDEPENDENT_HUMAN_ADJUDICATION`. No acceptance signature has been supplied.