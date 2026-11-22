# Agent execution contract — research from a user transcript

**Version 1.0 · implemented with plugin v1.9.0.** This contract defines how an agent chooses and executes four existing research methodologies. It is not a fifth research methodology. The upstream protocols own their own steps and authority.

## Start with a decision, not four automatic analyses

Input: the user's question and decision, a permitted transcript or trace, source locations, and any previously accepted research records. The agent reads the actual transcript in its client context, classifies the decision question, and declares only grounded metadata to the advisory router.

Use **research-router** in the portable plugin. With a connected local MCP research server, call **route_research_request** with a [research-request JSON](../../simulation/schemas/research-request.schema.json) and an optional existing exact checkpoint string. The router returns eligibility/gaps, not source interpretation or an executed method.

The evidence summary is **agent-declared** unless a checkpoint is provided. A checkpoint enables schema/reference-count validation, **not** proof of human review, participant independence, model access, or source truth. The tool never fetches source URLs, makes model calls or stores transcripts. Keep raw transcript text out of the routing request.

Example *agent-declared* input for an original single mattress interview (the real transcript is analyzed separately):

~~~json
{
  "research_question": "Why did this household replace its mattress?",
  "decision": "Which uncertainty should the next research study address?",
  "goals": [
    {"type": "CURRENT_DECISION", "question": "Reconstruct the historic switch"},
    {"type": "CONDITIONAL_MECHANISM", "question": "Why might other households differ?"},
    {"type": "COUNTERFACTUAL_RESPONSE", "question": "What if return pickup were included?"},
    {"type": "EMERGING_NEED", "question": "What advanced needs may emerge?"}
  ],
  "evidence": {
    "transcript_coverage": "FULL",
    "decision_episodes": 1,
    "distinct_people": 1,
    "source_locators_available": true,
    "human_review_completed": false,
    "reviewed_links_present": false,
    "human_holdout_available": false
  },
  "counterfactual": {
    "baseline_defined": true,
    "intervention_defined": true,
    "population_defined": true
  },
  "future_facing": {
    "trend_candidate": false,
    "advanced_user_signal": false,
    "high_expected_benefit_signal": false
  },
  "available_skills": []
}
~~~

This yields a provisional A→B path, a call for contrasting episodes, **L0-only counterfactual exploration**, and trend/candidate discovery. None is an empirical finding about future purchases. Even if a client declares an upstream skill available, the tool cannot verify the installation.

## Canonical four-method contract

| Method / owning protocol | Trigger | Required source and steps | Bounded result | Stop when |
| --- | --- | --- | --- | --- |
| **A→B / JTBD** — [analyze-interview](../../plugins/scaled-interview-data-assistant/skills/analyze-interview/SKILL.md) and [core prompt](../../prompt/custom-gpt.md) | Why did someone struggle, wait, switch, reject, or attempt change? | Full/partial source coverage; segment real past episodes; evidence and contradictory excerpts; A, Path Y, baseline, tipping, X, desired B, **actual** outcome; Four Forces; source-bound A/B mappings, review gates | Provisional or human-reviewed historical episode analysis, plus specific UNKNOWNs and a decision brief | No bounded past episode; missing outcome; evidence/code reviewer not yet approving |
| **Behavioral Mechanism Map** — [protocol](mechanism-map.md) | Why do comparable real decision episodes diverge? | At least two *actual* episodes; an explicit WITHIN_PERSON scope may compare the same person's decisions without cross-person inference; review of source evidence, A/B links and cluster/scope; conditional M hypothesis; independent cases where available; rival, refuter and discriminating test; ALIGNS/COUNTEREXAMPLE/AMBIGUOUS/UNASSESSED per case | Provisional conditional explanation with source coverage and falsification test; review-gated compiler only after actual review | Only one case, weak comparability, unreviewed source/link or unassessed condition |
| **Behavioral Simulation** — [canonical skill](https://github.com/mattlane66/behavioral-simulation-for-agents-and-humans/blob/main/behavioral-simulation/SKILL.md) and [protocol](https://github.com/mattlane66/behavioral-simulation-for-agents-and-humans/blob/main/behavioral-simulation/PROTOCOL.md) | What might a person/population do if specified conditions change? | Define P/C/T, baseline, actual intervention, closed outcome space and horizon; choose PLAUSIBILITY / INDIVIDUAL / POPULATION / MULTI_AGENT mode; grade L0–L4 by **evidence achieved**; ground sources; preregister runs/metrics, execute external model; held-out validation/calibration only if real independent data exist | SIMULATED_ESTIMATE with exact model/config, uncertainty, held-out error when available; optional SSR for predeclared ordinal text | No defined condition; no upstream skill; no valid person grounding for L1; no population grounding/holdout for predictive claim |
| **Lead User Research** — [canonical skill](https://github.com/mattlane66/planning-skills-for-agents-and-humans/blob/main/lead-user-research/SKILL.md) and [protocol](https://github.com/mattlane66/planning-skills-for-agents-and-humans/blob/main/lead-user-research/PROTOCOL.md) | Which important *future-facing* needs are already experienced by advanced users? | Name decision; identify and independently evidence important trends; discover/pyramid and independent branches; qualify LU1 **and** LU2 per bounded need episode; source-register atomic human evidence and trace pivotal episodes; contradiction, sufficiency/freeze; synthesize needs only after evidence | SCOUT / STANDARD / FULL study with real qualification and status; separate proposed future-x and transfer hypotheses, not rewritten historical x | No important trend, LU1/LU2 unqualified, evidence insufficient, fieldwork not conducted, transfer unsupported |

**One transcript is often enough to start A→B and identify *candidate* mechanisms**, but not to claim a reviewed cross-person mechanism model, a calibrated population simulation, or a qualified Lead User. The correct result may be NEED_MORE_EVIDENCE rather than a filled report.

## Execution and handoffs

1. **Select the smallest applicable move.** If user asks about a product interface task, representative prevalence, randomized effects or economic demand, the four methods may not fit; do not force them.
2. **Preserve reference identity.** Original transcript/episode IDs are authoritative only within that study. Keep Behavioral Simulation outputs and Lead User evidence under their respective namespaces. Never silently insert model-generated text into the real interview.
3. **Invoke the actual method.** Route **does not** call an external method, install an external skill or run a CLI. Call existing tools if connected; if the skill is absent, return a specific handoff and setup requirement.
4. **Apply human gates.** An agent can check source pointers and calculate matrices; it cannot self-sign a human approval or independent fieldwork, and an interview transcript does not become ground truth about external events.
5. **Deliver a decision brief.** Question → evidence-supported findings → conflicting explanation → critical unknown → what can be decided now → targeted next source or test. Do not accept a planning y, R or f().

### Optional upstream handoff semantics

Behavioral Simulation consumes *source-grounded* observations and assumptions; if the data only support L0, return a plausibility exploration. The local [simulation adapter](simulation.md) exports a pinned upstream v0.1.0 file contract; it does not run the full external protocol or automatically calibrate a model. SSR is optional and is not a consumer purchase probability.

Lead User Research can begin with the transcript as a **discovery seed**, not as proof of a trend or a qualified lead user. Apply the [context extension](context-evidence-extension.md), then run the full separate skill if connected. Its return is an evidence sidecar; observed original x stays unchanged, advanced-user x stays source-scoped, mainstream transfer remains a hypothesis.

## Paper-driven repair policy

The four method protocols already contain explicit procedures. To avoid accumulating contradictory instructions, **do not rewrite them from papers by default**. First run the [agent evaluation protocol](agent-evaluations.md) and classify an actual failure:

- **Evidence missing:** acquire a trace, real respondent or observed outcome; more prompting cannot fix this.
- **Tool/skill unavailable:** integrate or install the existing upstream workflow.
- **Instructions ambiguous or incomplete:** identify the specific agent misstep, cite a section of the primary research and add a narrowly-scoped clarification plus a regression case.
- **Model error despite clear instructions:** change execution scaffolding/tooling and test again; do not misattribute it to the source paper.

Original references: [Moesta switch interview](https://jobstobedone.org/radio/the-mattress-interview-part-one/), [von Hippel 1986](https://web.mit.edu/people/evhippel/papers/Lead%20Users%20Paper%20-1986.pdf), [Lead User project handbook](https://web.mit.edu/evhippel/www/Lead%20User%20Project%20Handbook%20%28Full%20Version%29.pdf), [Generative Agents](https://arxiv.org/abs/2304.03442), [self-report-grounded simulations](https://arxiv.org/abs/2411.10109), and [Semantic Similarity Rating](https://arxiv.org/abs/2510.08338). These are method sources, not evidence about the user's current consumers.

## Verification boundary

A green CI run means **schemas, reference validation and software behavior passed**. It does not mean the model followed every instruction in a new chat or that unseen transcript interpretations passed blind human review. Only actual native Codex/Claude sessions and separately scored, unfamiliar, permitted transcripts can establish that. Record such tests as RUN / NOT_RUN with identity, version, source permissions and reviewer provenance.
