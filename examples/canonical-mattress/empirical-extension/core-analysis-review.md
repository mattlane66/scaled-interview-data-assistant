# Core interview analysis — evidence adjudication required

**Source grain:** one historic participant, one bounded mattress-purchase episode. **Review:** machine-verifiable references and prior model audit only; **independent human adjudication not performed**.

The original [canonical README](../README.md) links the [full reproduced published transcript](../full-transcript.md), [turn registry](../source-turns.json), [28-excerpt bank](../evidence_bank.json), [codebook](../codebook.json), [links](../links.json), and [AI audit](../reference/independent-audit.md). This pass interrogates them together but **does not mutate** their IDs or mark them approved.

| Priority | Original references | What the source warrants | Required adjudication |
| --- | --- | --- | --- |
| Material | `E002 E005`; `A01` | Participant *associated* morning discomfort with the home bed and reported a different experience while traveling. Physical attribution is unproven. | Replace the word “causes” in `A01` **only after** reviewer-authorized recoding; examine whether alternate factors were adequately probed. |
| Material | `E014 E020 E027`; `L002` | The buyer worried about an unfamiliar Groupon failure path and reported some Costco returns. He learned about mattress pickup **after** the historic purchase. | Do not backdate a pickup guarantee into his choice. Separate seller reputation, perceived reversal, actual fulfillment and price. |
| Important | `E008 E009 E017 E019`; `L003` | Competing obligations and a convenient family shopping occasion were both reported; the latter was not shown to *result from* the former. | Reconsider or retire `L003`; classify `B03` as circumstance/enabler, not the ultimate desired outcome. |
| Important | `E018 E019 E021`; `L004` | A foam sample and partner agreement co-occurred, according to the participant; partner not interviewed independently. | Separate sample access from joint financial/social assent. Do not attribute independent causal weight. |
| Material | `E015 E023 E024 E026`; `B01` | He desired restorative sleep and reported purchase, yet retained/used the former bed. Achievement of Point B is unknown. | Track trial use, sleeping outcomes and any eventual return before saying the job was achieved. |
| Important | `E001 E008 E009`; Four Forces | Earlier expense and competing priorities were mentioned. The source does not prove a sunk-cost effect. | Preserve sunk-cost inertia as rival hypothesis rather than accepted diagnosis. |
| Material | `E028`; published workshop Q&A | Hypothetical answers and presenter commentary are not observed buying behavior. | Review all 99 original participant turns, including omitted and contrary material. Do not code facilitator statements as a customer. |

**Working reconstruction (INFERRED):** The person experienced recurring waking discomfort, tried to extend the old bed's life, and postponed replacement while other commitments dominated. He researched alternatives but worried about failure and unattractive buying environments. An unplanned retail encounter with his partner enabled a purchase of a different type of mattress. Desired Point B was better rested functioning, **not** the purchase or an optional return feature. Subsequent improvement is **UNKNOWN**. This is consistent with the source-linked prior audit, but not a fresh independent human validation.

**Special distinction:** `B02`, `B03`, `B04` may describe **conditions for adopting a path**, rather than end-state progress; `B01` better captures desired progress. Recoding requires a reviewer to verify code inclusion/exclusion rules, consider contradictory material and backcode the episode. `A05` reflects the *post-purchase situation* and should not automatically be retrojected into pre-switch Point A.

The later DIY cases in [source-ledger.json](source-ledger.json) do not repair missing original testimony. They may suggest **new research directions**, not demonstrate why the historical participant made his decision.

## Human approval gate (not completed)

1. Review the full participant dialogue, workshop context and 28 candidate excerpts, including excluded material.
2. Correctly separate direct account, facilitator question, retrospective explanation, and spouse account reported secondhand.
3. Approve/revise/reject `A01`, all B-code meanings, `L003`, forces, and contrary evidence; preserve diff and stable IDs.
4. Only after review, rerun the deterministic original pipeline against the same authorized source and publish a new checkpoint with actual approval provenance.

No new checkpoint, human attestation or signed review is claimed by this document.
