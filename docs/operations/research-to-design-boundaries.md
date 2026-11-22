# Research-to-design boundaries

**Foundations:** [Uncovering the Causes of Demand](https://mattlane66.github.io/articles/uncovering-the-causes-of-demand/) explains how to elicit useful accounts of concrete behavior.
[Design as Functions](https://mattlane66.github.io/articles/design-as-functions/) explains why evidence, intent, outcomes, operating assumptions, design criteria, and effects need different justifications.

These are complementary methods, not instructions to run Fit Check inside the interview assistant.

## Responsibilities

The interview assistant should establish what the available sources support about a current
situation **x**, record the progress people report or appear to seek, and make conditional
operating hypotheses **M** inspectable. It does not choose the product team's **y**.

| Research element | What it is | What it cannot establish |
|---|---|---|
| **x** | An evidence-located representation of a current situation, including the incumbent Path Y | External truth beyond the observed/reported source |
| **Human intent** | Participant-reported or inferred progress from B-codes and A→B links, with whose account it represents | The organization has accepted these wants as its priority |
| **Proposed y** | A future outcome that an authorized product/design owner may choose, including whose outcomes count | A B-code automatically dictates the accepted goal |
| **M** | Hypotheses about conditions and relationships in the operating world, with rival mechanisms and contrary cases | A specific proposed solution will succeed |
| **Counterfactual candidate** | A design intervention and its untested effect prediction | Actual adoption lift, use, progress, or attributable effect |

The authority of an interview excerpt and the authority to choose a product goal are different.
A participant can report wanting an easier purchase; the company may still need to choose whether
that outcome is desirable, economically viable, compatible with other parties, or within appetite.

## The v1.1 Planning Skills handoff

The [Behavioral Mechanism Map](mechanism-map.md) exports a JSON
`RESEARCH_TO_PLANNING_PROPOSAL`, now `schema_version=1.1`. Existing
`x_current_struggles_candidates` and `y_desired_progress_candidates` string arrays remain
for compatibility, **but are never accepted requirements or an approved outcome**.

The new typed boundaries are:

- `frame_boundaries.x_current_situation.representations`: codebook-interpreted A conditions,
  with original link, episode and evidence references, and explicit `PROPOSED` authority
- `frame_boundaries.human_intent.progress_candidates`: who supplied the relevant accounts
  and the provenance and `EXPLICIT/INFERRED` status of B-code interpretation
- `frame_boundaries.y_selected_outcome`: `NOT_SELECTED`, no owner or priority choice inferred
  from research; Planning Skills must establish y and handle multi-party priorities
- `M_operating_model.conditions_and_hypotheses`: provisional general operating relationships,
  rival explanations, contradictory cases, and evidence; no candidate's projected success
- `candidate_research_probes`: proposed counterfactual condition changes and human tests
  **outside M**
- `outcome_evidence`: separate participant reports on adoption, use and progress, with
  `attribution=NOT_ESTABLISHED` for interview-only research
- `f_solution_variable=UNSPECIFIED`: no selected product shape

`simulation/schemas/planning-handoff.schema.json` validates the authority boundaries.
A schema can rule out unauthorized fields and unsupported statuses; it cannot decide whether
a particular mechanism hypothesis is conceptually independent of a proposed solution.
Human review remains essential.

### Adoption, use, progress, attribution

The outcome check is **opt-in**, so old studies remain valid. A newly initialized
`mechanism-study.json` has `outcome_assessments=[]` and `outcomes_reviewed=false`.

To record a case where a participant reports taking action but there is no follow-up
on use or successful progress, an analyst may add an episode-scoped assessment:

~~~json
{
  "episode": "D01",
  "adoption": {
    "status": "REPORTED_ADOPTION",
    "evidence_refs": ["E019", "E020"],
    "interpretation": "Participant describes making the purchase."
  },
  "use": {
    "status": "UNKNOWN",
    "evidence_refs": [],
    "interpretation": "No reviewed evidence of using the new product."
  },
  "progress": {
    "status": "UNKNOWN",
    "evidence_refs": [],
    "interpretation": "Improved sleep is not established."
  }
}
~~~

This is an **illustrative input using a real mattress-case evidence identifier**.
It is **not** approved mattress study data: a human must check source ownership,
source type, context and the interpretation before setting
`review.outcomes_reviewed=true`.

Outcomes use the following controlled values:

| Dimension | Allowed descriptions |
|---|---|
| Adoption | `REPORTED_ADOPTION`, `REPORTED_NONADOPTION`, `UNKNOWN` |
| Use | `REPORTED_USE`, `REPORTED_NONUSE`, `MIXED`, `UNKNOWN` |
| Progress | `REPORTED_IMPROVEMENT`, `REPORTED_NO_IMPROVEMENT`, `MIXED`, `UNKNOWN` |
| Attribution | Always `NOT_ESTABLISHED` from interview evidence alone |

The checked assessment must cite source-located `E###` references belonging to the same
episode. Reported actions, use and progress require a concrete-event, observed-behavior or
current-state source type. Hypotheticals, interpretations, generalizations and aspirations
alone cannot justify an assessed result. `UNKNOWN` carries **no positive/negative result
evidence** and is not evidence that an outcome failed.

One testimony can inform multiple dimensions; citing it in several places does not turn
it into independent confirmations. Reports of before/after improvement do not identify
the counterfactual result without the intervention.

The compiler rejects unsupported statuses, cross-episode references, repeated episode
assessments, unapproved assessments and all attempted assertions that intervention
attribution is known. Missing outcome reports default to `UNKNOWN` at all stages.

### Candidate effect evidence

The [counterfactual decision brief](counterfactual-decisions.md) now labels the candidate's
predicted effect as `CANDIDATE_SPECIFIC_EFFECT_HYPOTHESIS` with `UNTESTED` status.
Its `candidate_effect_evidence` makes clear that there are no observed adoption, use
or progress outcomes **for that intervention**, and no attributable effect.
This does not erase a historical baseline observation in `scenario.baseline`.

Importantly, the claim “perceived recovery difficulty may inhibit switching” can be a
candidate operating hypothesis **M**. The claim “guaranteed pickup will increase conversion”
is an untested **candidate f() theory**. It cannot justify itself by being put in M.

## When to move into Planning Skills

- Research reviewers validate sources and episode interpretations.
- An authorized owner chooses `y`, resolves whose interests matter, and decides what
  uncertainty or competing priorities to accept.
- Planning Skills derives `R` from x, y, M and imposed boundaries. No B-code becomes a
  mandatory requirement without that decision.
- Shaping generates and compares candidate `f()`; Fit Check examines conformance.
- A real pilot/launch examines **effect** separately: was the desired outcome changed,
  and what evidence supports attribution?

The existing human approval and checkpoint gates remain intact. Neither interview analysis
nor synthetic SSR establishes a product's causal effect. When reality changes, revise the
relevant evidence, frame, model and criteria rather than treating a previous artifact as truth.
