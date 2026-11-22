# Canonical mattress study — four methods applied to real evidence

**Evidence reviewed 2026-11-22 · Research mode: source-grounded desk analysis · Human adjudication: NOT DONE · New direct interviews: 0 · Independent simulation holdout: 0 · Qualified Lead Users: 0.**

This is a **worked empirical research case** rather than a demo of software APIs. The original [licensed workshop interview](../full-transcript.md) remains the primary historical case. The seven later [first-person accounts](source-ledger.json) are independent *public source documents*, not independently verified transactions, a random sample, or seven professionally conducted interviews. The machine-readable [casebook](casebook.json) contains episode-by-episode interpretations, contrasting evidence and testable rival hypotheses. [Re-run its structural audit](../../../scripts/audit_canonical_empirical.py) from the repository root with `python scripts/audit_canonical_empirical.py`.

## The decision, and what changed

**Decision:** What should we study next to help households make and sustain progress when a mattress no longer meets their needs?

**INFERRED from these real accounts:** A potentially useful distinction is between **reversibility of the whole purchase** and **adjustability of comfort after purchase**. Some participants report returns as difficult or time-limited; others report straightforward collection. Some DIY experimenters report useful comfort and component repair; another reports repeated loss of support despite years of adjustments. These outcomes do not identify a single winner or an effect size.

**Recommendation:** Investigate the timing and type of uncertainty before shaping a product. Keep recovery, evaluation, ongoing fit, seller trust and actual sleep outcomes separate. Choose no product mechanism yet. The original subject's motives do not become more certain merely because later people tell related stories.

## 1. Core A→B reconstruction from the real switch interview

The source is a published live JTBD workshop transcript with **one historic buyer** and distinct interviewer/audience commentary. The pinned source contains 279 speaker turns, of which 99 are participant turns; the assistant-curated evidence bank selects 28 excerpts. The evidence is real reported testimony, not objectively verified sleep or retailer records. See the [source registry](../source-turns.json), [28 excerpts](../evidence_bank.json), [candidate codebook](../codebook.json), [links](../links.json), and [existing independent AI audit](../reference/independent-audit.md).

| Analytical element | Reconstructed claim | Closest original evidence | Epistemic status |
| --- | --- | --- | --- |
| **Point A** | Recurring waking discomfort and a home bed the buyer believed inadequate | E002, E005 | Participant report; mattress attribution unproven |
| **Path Y** | Kept the older bed, changed sleeping configuration, deferred replacement and researched options | E004, E006, E008, E009, E013, E014 | Reported choices |
| **Pre-switch result** | Continued discomfort and competing family/work commitments | E002, E008, E015 | Reported baseline; no controlled comparison |
| **Tipping context** | Unplanned Costco encounter with spouse and accessible foam sample after prior search | E013, E017–E020 | Reported sequence; independent influence unknown |
| **Path X** | Purchased a different foam mattress rather than the contemplated online Groupon offer | E017, E019, E020, E022 | Reported purchase |
| **Desired Point B** | Wake better rested for work, family and ordinary life | E015 | Participant's stated desired progress |
| **Actual result** | Buyer still retained/used older mattress and described the problem as unresolved | E023, E024, E026 | Reported; improvement from new bed **UNKNOWN** |

**Critical codebook audit.** `A01` currently says the old mattress “causes” impairment, although the interview establishes only the participant's attribution. `B02–B04` often describe **purchase enablers** (reversibility, joint occasion, evaluating a different material) rather than end-state `B01`. `L003` weakly joins competing obligations with a convenient Costco joint purchase without establishing that one produced the other. The spouse was not independently interviewed. A workshop participant first introduced mattress home pickup **after** the historic purchase; it cannot be retroactively coded as a purchase driver. These are material interpretation issues pending independent human acceptance, not changes already made to the source or checkpoint. See [review decisions](core-analysis-review.md).

**What this method adds:** a detailed historical demand and adoption timeline, *including failure to establish realized progress*. It does **not** generalize to other buyers by itself.

## 2. Behavioral Mechanism Map — actual cross-case analysis, unreviewed

The [casebook](casebook.json) compares **eight distinct source-account histories**: the original workshop buyer (`CD01`) and seven separately authored public accounts (`CD02–CD08`). One writer describes several bed purchases; those purchases are **not multiple independent respondents**. These cases differ in episode grain and need, so they are **not claimed to be one validated job cluster**, a representative sample, or a formal run of the human-reviewed mechanism-map compiler.

The four candidate mechanisms are assessed case by case as `ALIGNS`, `COUNTEREXAMPLE`, `AMBIGUOUS`, or `UNASSESSED`, with a specific evidence reference, a rival, a potential refuter and a real test. These are researcher interpretations, not votes or causal estimates.

### M1 — Recovery from failure can affect commitment

The original buyer [P01](https://jobstobedone.org/radio/the-mattress-interview-part-one/) described stepping back from an unfamiliar online purchase partly because a failed purchase seemed hard to undo. A later buyer [P08](https://www.reddit.com/r/Mattress/comments/1bzuk1o/costco_mattress_return_super_easy/) describes a completed, comparatively straightforward pickup and refund. By contrast, another writer [P09](https://www.reddit.com/r/Mattress/comments/qgkykh/whats_the_catch_to_these_mattress_trial_periods/) reports failed courier attempts and unwanted mattress disposal after a refund; a different writer [P10](https://www.reddit.com/r/Mattress/comments/1fhes3c/dont_be_an_idiot_like_me_return_your_mattress/) reports missing the trial deadline.

**Interpretation:** *Perceived recoverability* and *actual logistics* are different variables. The easy-return account is not evidence that the guarantee caused the original purchase; the failed-return account is not proof the guarantee never works. Seller reputation, price and product differences remain rivals.

### M2 — Initial feel may poorly predict overnight suitability

A DIY builder [P05](https://www.reddit.com/r/MattressMod/comments/1g0oi73/two_months_later_i_can_see_the_finish_line_for_my/) says showroom testing was unlike overnight use. A separate buyer [P11](https://www.reddit.com/r/Mattress/comments/1f93tts/the_trials_and_tribulations_of_mattress_shopping/) reports being comfortable while lying on a latex mattress but waking stiff, despite different toppers, before completing a return. An expired-trial writer [P10](https://www.reddit.com/r/Mattress/comments/1fhes3c/dont_be_an_idiot_like_me_return_your_mattress/) describes a transient period of improvement followed by renewed discomfort.

**Interpretation:** immediate tactile access, even if it aids purchasing, may not be enough to establish sustained fit. It does not prove that all discomfort was mattress-caused; activities, travel, support and other circumstances differ.

### M3 — Adjustment and selective repair might compete with replacement

One DIY writer [P06](https://www.reddit.com/r/Mattress/comments/1l44ojs/3_year_diy_mattress_build_review_6_foam_base/) reports about three years of satisfaction with a layered build and *plans* to replace a worn base. Another [P07](https://www.reddit.com/r/MattressMod/comments/1nkral8/tired_of_latex_degrading_within_the_year/) reports roughly 15 years of experiments yet repeated perceived loss of support. A third [P05](https://www.reddit.com/r/MattressMod/comments/1g0oi73/two_months_later_i_can_see_the_finish_line_for_my/) reports many iterations but only a few nights on the latest arrangement.

**Interpretation:** component repair could be valuable for some people, but it also introduces expertise, experimentation and time costs. Reported softening does not verify material degradation. This is **a hypothesis surfaced by contrastive real evidence**, not a proven emerging mass-market need.

### M4 — Checkout is not the job's outcome

The original Costco buyer's improved sleep is not established. One DIY writer reports longer-term comfort; other purchasers report returns, persistent discomfort or unknown replacement results. **A purchase event and sustained realized progress must be measured separately.** That is a stronger conclusion about *measurement design* than about mattress choice.

**What this method adds:** specific conditional mechanisms, real negative and differing cases, and tests designed to discriminate explanations. It does not establish frequency, relative effect, causation or a reviewed cross-episode map. A future reviewed map should use consistently recoded interview episodes with independent source review.

## 3. Behavioral Simulation + SSR — model output challenged by real outcomes

The canonical repository already holds **two authored hypothetical response variants per condition**, anchored to the original real interview. Its semantic similarity ratings were computed with `BAAI/bge-small-en-v1.5` across **six anchor sets**, using real vector calculations. The external SSR paper used a different model/setting, and the results are not a replication or validation on mattress shoppers.

| Hypothetical condition | Mean of five-point SSR rating allocation | What it actually measures |
| --- | ---: | --- |
| SIM001 — free home pickup if trial fails | **3.2014** | Similarity of **two authored model-text responses** to ordinal anchors |
| SIM002 — physical material sample | **2.9799** | The same constructed-text metric for a different intervention |

These means and the difference (~0.2214 points) are **not** independent human preferences, conversion likelihoods, an estimate of causal lift, or grounds to rank the interventions. At least one response has substantial variation across anchor sets; the highest per-response anchor-set TVD is about 0.435 in SIM001 and 0.350 in SIM002. The underlying response texts are not independent participant samples.

**Real-case challenges, not a holdout:** The reported easy refund [P08](https://www.reddit.com/r/Mattress/comments/1bzuk1o/costco_mattress_return_super_easy/) confirms that a pickup can be completed; the failed logistics [P09](https://www.reddit.com/r/Mattress/comments/qgkykh/whats_the_catch_to_these_mattress_trial_periods/) and missed deadline [P10](https://www.reddit.com/r/Mattress/comments/1fhes3c/dont_be_an_idiot_like_me_return_your_mattress/) show why a generic guarantee is insufficient to represent all situations. A sample might aid evaluation in the original interview or reduce returned DIY components [P05](https://www.reddit.com/r/MattressMod/comments/1g0oi73/two_months_later_i_can_see_the_finish_line_for_my/), but [P11](https://www.reddit.com/r/Mattress/comments/1f93tts/the_trials_and_tribulations_of_mattress_shopping/) demonstrates that momentary feel can differ from overnight comfort.

**What the actual evidence allows:** identifying conditions the simulation may have omitted and designing narrower scenarios. None of these independent accounts answered the **same predeclared five-point question under the same offers**, so they do not provide an SSR human holdout. A proper next study needs (a) controlled prompts and prespecified anchors, (b) independently recruited human responses to *those exact questions*, and (c) separately observed purchasing/return behavior if prediction of decisions is the claim. A failure to predict must be retained as a negative finding, not optimized away.

**What this method adds:** cheap structured counterfactual challenges and a numerical text-elicitation illustration. The numerical output is real computation; the simulated behavior is **not real human observation**.

## 4. Lead User Research — evidence-backed SCOUT, not manufactured qualification

Following the separate [Lead User Research protocol](https://github.com/mattlane66/planning-skills-for-agents-and-humans/tree/main/lead-user-research), a future-facing need requires **an important trend first**, then specific **LU1** advancement ahead of it and **LU2** unusually high expected benefit, with evidence for each.

**Trend inspection.** A 2023 Better Sleep Council survey, reported with 1,039 respondents, found online mattress buying was an increasingly considered option compared with 2016; the [NBF survey](https://www.bedfed.org.uk/online-overtakes-instore-mattress-purchases/) reports online purchase in an earlier UK buyer sample. A separate [2020 BSC survey](https://bettersleep.org/research/bsc-sub-study-mattress-shopping-behavior-during-covid-19/) surveyed 501 people, including 314 recent buyers, and reports 71% of recent buyers considered easy returns important and 46% considered a free at-home trial important. These are self-reported survey attitudes/behaviors, collected in different populations and times; they are **not causal trial evidence**.

There is genuine trend context for **online evaluation and buying**. There is **not yet independently established evidence** that user-built *modular mattress repair* is an important growing market trend. The presence of many technically skilled DIY posters does not fix that gap.

**Candidate qualification, done honestly.** Four first-person accounts [P05](https://www.reddit.com/r/MattressMod/comments/1g0oi73/two_months_later_i_can_see_the_finish_line_for_my/), [P06](https://www.reddit.com/r/Mattress/comments/1l44ojs/3_year_diy_mattress_build_review_6_foam_base/), [P07](https://www.reddit.com/r/MattressMod/comments/1nkral8/tired_of_latex_degrading_within_the_year/) and [P09](https://www.reddit.com/r/Mattress/comments/qgkykh/whats_the_catch_to_these_mattress_trial_periods/) exhibit reported advanced experimentation or repeated failed trials. They plausibly bear high personal costs/benefits, but **no one has independently passed LU1 and LU2**. The first three are not interchangeable: one latest build is barely tested, one reports long-term benefit, one reports long-term failure. The public-posting discovery channel is biased toward unusually motivated, English-language tinkerers.

**Research result:** `INVESTIGATE`, not `QUALIFIED` or `SHAPE`. A plausible proposed emerging-x question is whether component-level adjustability makes long-run mattress fit less costly or less risky. That is **not** a validated Lead User finding to import automatically into the original x.

**Corrective next move:** verify the importance and direction of the trend from independent evidence, seek referrals outside Reddit to textile/foam repair practitioners and unconventional sleep-system developers, obtain consented first-person interviews plus build logs/receipts/outcome traces, seek deliberate negative cases, qualify each bounded episode against both LU1 and LU2, and only freeze/synthesize when the protocol's sufficiency gate passes.

**What this method adds now:** future-facing candidate discovery, candidate screening and an explicit negative qualification result. It has **not** produced a full fieldwork Lead User study, frozen evidence base, qualified need, or a concept ready for Fit Check.

## 5. One integrated research-to-planning handoff — PROPOSED ONLY

| Planning distinction | What can be handed over | What cannot |
| --- | --- | --- |
| **Current x** | Source-linked original struggle, workaround path, shopping constraints and unknown post-purchase result | Revised historical motives invented from other people's accounts |
| **Participant intent** | Desire for restored sleep and daily functioning, as reported by the original buyer | A product team's selected objective `y` |
| **Conditional M** | Hypotheses about recoverability, initial versus ongoing evaluation, adjustment and adoption versus realized progress | Accepted causal laws, rates, effect sizes or rankings |
| **Possible emerging x** | A separate, unqualified question about adaptation/repair over time | Proven mainstream transfer, formally qualified Lead User need |
| **Candidate intervention** | Specific reversible-trial, sample-access and component-adjustment tests | A selected `f()`, accepted requirements or launch authorization |

**Next empirical test priority:** (1) review and recode the complete original A→B case; (2) recruit real contrasting switch and non-switch cases and follow their outcomes; (3) compare truthful return conditions and available evaluation options in a controlled real offer; (4) study longitudinal comfort and total adjustment cost; (5) only evaluate the synthetic-intent model against a genuinely independent, matching human holdout. Run a separate Lead User STANDARD study only once the future-facing trend and candidate evidence warrant it.

## Reproducibility and boundaries

The [source ledger](source-ledger.json) records original URLs, author-versus-commenter boundaries, source locators and coverage limitations. The [structured casebook](casebook.json) links every public case to those source-level paraphrases and each hypothesis to all case outcomes. The [auditor](../../../scripts/audit_canonical_empirical.py) checks reference ownership, absence of fabricated reviews/holdouts/qualified Lead Users, mechanism classifications and SSR arithmetic; it **cannot** independently authenticate posts or validate causal interpretations.

Source text is treated as untrusted data. Inline AI commentary inside P06 has been excluded as human observation. The original checkpoint, 28 evidence excerpts, model-generated L0 examples and human-review flags remain **untouched**. Source independence and fieldwork claims would require external verification; the present study is transparent about their absence.
