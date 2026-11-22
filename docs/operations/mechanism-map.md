# Behavioral Mechanism Map

Use reviewed JTBD interview evidence to compare **which conditions may explain different
decisions within a job cluster**. This is an evidence-first interpretation tool, not a
causal discovery algorithm, synthetic interview generator, or product-shaping method.

**Observe the episodes → inspect the A→B relationships → state competing conditional
explanations → check aligning and contrasting cases → propose a falsifying human test.**

The map sits between [interview synthesis](../../README.md) and
[counterfactual product decisions](counterfactual-decisions.md). It can also provide
a *proposed* operating-model input to
[Planning Skills](https://github.com/mattlane66/planning-skills-for-agents-and-humans).

## What the tool does

- Resolves an existing **reviewed cluster** (`C##`) at episode or interview grain,
  or an explicitly selected **set of episodes** when clustering was not used.
- Indexes original `D##` episodes, `I##` interview owners, evidence `E###`,
  source type/coverage/locator, and primary reviewed `L###` A→B relationships.
- Preserves code definitions and the `EXPLICIT/INFERRED` status of those links.
- Requires an analyst to specify the condition, proposed relationship, **rival
  explanation**, counterfactual condition change, disconfirming observation,
  and smallest discriminating **human** test.
- Requires episode-level annotations with `ALIGNS`, `COUNTEREXAMPLE`,
  `AMBIGUOUS`, or `UNASSESSED`. Assessed cases must cite existing evidence from
  that episode. Missing observations remain `UNASSESSED`, never negative cases.
- Describes which distinct **interviews** supplied evidence for each stance, and
  flags contradictions within the same participant. These are descriptive case
  indexes, **not prevalence percentages or causal-effect estimates**.
- Keeps full interview excerpts out of its inventory and reports by default.
  Research identifiers/descriptors and interpretations may still be sensitive.
- Emits a separate **PROPOSED** planning handoff. It cannot accept requirements,
  select solution shapes, or authorize implementation.

No model call, vector embedding, survey measurement, or SSR is required.

## 1. Start with a validated source checkpoint

After the existing evidence, codebook/links, and cluster interpretation reviews,
produce `outputs/CHECKPOINT.json` using the standard pipeline.

For an existing cluster:

~~~bash
python scripts/mechanism_map_cli.py init \
  --checkpoint outputs/CHECKPOINT.json \
  --cluster C02 \
  --output data/mechanism-study.json
~~~

For research without meaningful clustering, explicitly name at least two episodes:

~~~bash
python scripts/mechanism_map_cli.py init \
  --checkpoint outputs/CHECKPOINT.json \
  --episode D01 --episode D02 \
  --output data/mechanism-study.json
~~~

The draft has **no hypotheses**, an empty reviewer, a null review date, and all
review approvals set to false. This is deliberate; a validated checkpoint is not
itself proof that any interpretation was reviewed.

Before coding conditional mechanisms, generate an inventory:

~~~bash
python scripts/mechanism_map_cli.py inventory \
  --checkpoint outputs/CHECKPOINT.json \
  --study data/mechanism-study.json \
  --output outputs/mechanism-inventory.json
~~~

Inspect the supporting `E###` citations at their original transcript locations.
Study the strongest cases and **seek contrasting and missing cases**, not only
evidence favorable to the proposed explanation.

## 2. Code provisional mechanisms, not solution shapes

Enter a real `research_question` and add one or more mechanism hypotheses to
`mechanisms`. One illustrative mechanism object (not a real research finding):

~~~json
{
  "mechanism_id": "BM01",
  "condition": "Whether switching requires substantial manual migration",
  "hypothesized_relationship": "High migration effort may lead people to defer action",
  "rival_explanation": "The barrier may be trust or fear of losing existing work",
  "counterfactual_condition_change": "Reduce migration effort, holding other conditions constant",
  "disconfirming_observation": "People still defer after assisted migration is available",
  "discriminating_human_test": "Offer a real migration trial and observe attempted switches",
  "revisit_when": "Pricing, migration technology, or customer environment changes",
  "observations": [
    {
      "episode": "D01",
      "stance": "ALIGNS",
      "evidence_refs": ["E001"],
      "link_refs": ["L001"],
      "interpretation": "REPLACE: cite what in this real episode bears on the hypothesis"
    }
  ]
}
~~~

**These example values are fictional placeholders.** Never use the example IDs or
claims as findings without checking the actual source checkpoint.

For each episode, an analyst may mark `ALIGNS`, `COUNTEREXAMPLE`, or
`AMBIGUOUS` only with at least one source-located `E###` that actually belongs
to that episode. `link_refs` must also belong to the same episode. Every
annotation needs an explanation; passing a referential-integrity test does not
prove that explanation is correct.

`UNASSESSED` must have **no** evidence or link references, and omitted episodes
are automatically classified `UNASSESSED`. A participant who did not mention a
condition has **not** necessarily demonstrated that the condition was absent.

The tool shows whether an annotation's evidence includes a
`concrete_event_or_behavior`, `current_state`, or `observation` source
type. Generalizations, aspirations, and interpretations can matter, but should
not silently be called directly observed behavior.

## 3. Approve the research interpretation

Only after actually reviewing the data and contradictory cases, fill the
`review` object with the human reviewer's name, actual `reviewed_at` date/time,
and applicable approval flags:

- `evidence_reviewed`
- `a_to_b_links_reviewed`
- `cluster_interpretation_reviewed` (required for cluster scope)
- `contrasting_cases_reviewed`

Keep `approved_checkpoint_sha256` unchanged. If source or coding changes,
create/review a new study against the updated checkpoint, rather than reusing an
approval bound to old source bytes.

Review flags are **human attestations**. The software can validate their presence
and the cited IDs, not independently certify that thoughtful review occurred.

## 4. Compile a map and propose a Planning Skills handoff

~~~bash
python scripts/mechanism_map_cli.py compile \
  --checkpoint outputs/CHECKPOINT.json \
  --study data/mechanism-study.json \
  --output outputs/behavioral-mechanism-map.json \
  --report outputs/behavioral-mechanism-map.md \
  --planning-handoff outputs/proposed-planning-M.json
~~~

The JSON map and Markdown report keep human-source relationships separate from
analyst hypotheses, expose divergent cases and evidence limitations, and remain
`PROVISIONAL`. Compilation fails for invalid/misaligned IDs, unreadable sources,
missing human reviews, duplicate mechanism IDs, or absent hypotheses.

The [research-to-design boundary](research-to-design-boundaries.md) distinguishes
interview-derived current conditions `x`, participant progress claims, organizational
outcome `y` (not selected by research), conditional operating model `M`,
proposed research probes, and source-checked evidence of adoption/use/progress.

The versioned v1.1 planning handoff is always `status=PROPOSED` with
`HUMAN_ACCEPTANCE_REQUIRED`. It supplies:

- **x representations:** interpreted struggling conditions from A-code definitions,
  source-located by evidence, link and episode; external truth is not independently verified
- **Human intent:** hoped-for progress from B-code definitions, including whose interview
  accounts and whether an A→B relation was EXPLICIT or INFERRED
- **y:** `NOT_SELECTED` — research cannot choose whose outcomes count or authorize goals
- **f():** `UNSPECIFIED` — no solution shape is selected
- **M candidates:** general conditional relationships with rival hypotheses, review
  limitations and case-by-case ALIGNS/COUNTEREXAMPLE/AMBIGUOUS/UNASSESSED evidence
- **Research probes:** candidate intervention tests are `UNTESTED` and remain outside M
- **Outcome evidence:** separately cited reports of adoption, use and realized progress,
  with `UNKNOWN` for missing information and causal attribution `NOT_ESTABLISHED`

Evidence IDs are namespaced `SID:BMST001:E###` in the handoff to avoid colliding
with requirements and other research workspaces.

**Planning Skills owns promotion.** After explicit human acceptance, its
`framing-doc` or collaborative `shaping` skill may import these as Working
x/y/M inputs. The handoff cannot turn a mechanism into an accepted requirement,
a candidate-specific success claim, an approved Fit Check, or a selected design.
When `M` changes materially, re-evaluate affected Fit Checks under the new frame.

## Boundaries

Clusters are exploratory; similarity of A/B codes does not prove that different
episodes share a cause. Multiple episodes belonging to the same interview are not
independent respondents. Counts are descriptive only for this convenience sample.

The mapping process does not discover a genuine causal effect, know the prevalence
of any mechanism, infer switching outcomes that a transcript did not report, or
automatically recommend a product. To validate a proposed mechanism, collect
discriminating behavioral evidence or run a properly designed intervention.

Use [the counterfactual decision workflow](counterfactual-decisions.md) when a
particular behavioral assumption should now be translated into one or more
product-design alternatives. Use [Behavioral Simulation](simulation.md) only as
an optional **synthetic** hypothesis-expansion or risk exploration step. Neither
path may backfill simulated answers into the human evidence bank.

Keep research artifacts in ignored local `data/` and `outputs/` directories,
or an approved access-controlled research workspace. Do not publish real
participant descriptors, source IDs, or evidence selections without authorization.
