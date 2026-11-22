# Extending x with optional Lead User Research

The Scaled Interview Data Assistant reconstructs what is supported about a
**specific, present situation**. When important parts of that situation are missing,
it must not complete the story by statistical extrapolation or a plausible narrative.

Sometimes the right next move is additional ordinary interviews or direct traces.
Sometimes it is [Lead User Research](https://github.com/mattlane66/planning-skills-for-agents-and-humans/tree/main/lead-user-research),
whose canonical source and protocol remain **upstream and separately owned**.

This adapter makes the decision explicit and provides a **source-traceable,
read-only return handoff**. It does not run the Lead User protocol or integrate
Lead User records into the original checkpoint.

## 1. Route the smallest consequential evidence gap

State exactly what is unknown and whether it could change the product/research
decision. Source-link any relevant `D##` and `E###` evidence. If there is no
interview corpus yet, leave those arrays empty rather than inventing source IDs.

Assess observability according to the upstream protocol:
`TRACE_OBSERVABLE | PARTIALLY_OBSERVABLE | NOT_OBSERVABLE | UNKNOWN`.

| Condition | Proposed research move |
|---|---|
| Gap is not consequential | `DEFER` |
| Existing real traces can answer it | `TRACE_RESEARCH` |
| Observability itself is unknown | `CHECK_OBSERVABILITY` |
| Material future-facing gap **with candidates** for an important trend, advanced users, and high expected benefit | `LEAD_USER_RESEARCH` |
| Material gap without those future-facing signals | `TARGETED_CURRENT_RESEARCH` |

These are **routing signals**, not source findings or qualified Lead Users.
A vivid example, expert, referral, user innovation or high online attention does
not establish LU1/LU2 or mainstream prevalence.

### Example input

```json
{
  "domain": "Mattress replacement",
  "decision": "Which uncertainty should shape the next research study?",
  "target_population": "Households replacing unsatisfactory mattresses",
  "uncertainty": "Will different return infrastructure change the operating context?",
  "material_to_decision": true,
  "episode_refs": ["D01"],
  "evidence_refs": ["E010", "E014"],
  "coverage": "PARTIAL",
  "observability": "PARTIALLY_OBSERVABLE",
  "future_facing": {
    "trend_candidate": "Possible growth of home trial return options",
    "advanced_user_signal": "Potentially advanced households using many trials",
    "high_expected_benefit_signal": "Potentially high cost of repeated failed trials"
  }
}
```

**This is an illustrative route hypothesis, not an empirical trend finding.**
The canonical interview does not qualify anyone as a Lead User or show what
mainstream buyers will experience later.

If the optional MCP is connected, call `triage_context_uncertainty` with the
JSON above and the **exact** `checkpoint_json` string from the original study.
The tool validates source membership and returns a `CUR-...` ID bound to the
checkpoint SHA. Without a checkpoint, omit `checkpoint_json` and E/D refs.
A skills-only plugin can *recommend* this path but cannot claim it ran code.

When the route is `LEAD_USER_RESEARCH`, its `lead_user_research_brief`
offers only the minimum domain, target market, learning question, decision and
trend hypothesis. Carry that to the upstream method; apply its real
**LU1 (ahead of a relevant trend)** and
**LU2 (unusually high expected benefit)** tests with separate evidence.

## 2. Return source evidence, not a completed mainstream x

A validated return must contain:

- `route_id` and exact `source_checkpoint_sha256` to prevent cross-study joins
- Upstream `workspace`, `source_handoff_ref`,
  `DESK_RESEARCH | FIELDWORK_ENRICHED | FULL_LEAD_USER_PROJECT`, and study status
- Each upstream `E#` with its bounded `LU#` owner, source locator, and
  `OBSERVED | STATED | INFERRED | UNKNOWN` evidence type
- Each `LU#` with independently located LU1 and LU2 evidence refs,
  advancement indicator, benefit signal, qualification status and caveats
- Each proposed `LX###` with supporting `E#`/`LU#` references,
  classification, `SUPPORTED | PLAUSIBLE | LEAD_USER_BOUND | UNKNOWN`
  transferability, rationale and limits
- Contradictions and consequential unknowns, not a success-only narrative

`simulation/schemas/context-return.schema.json` defines the exact contract.
The adapter confirms referential consistency, source ownership within each LU
episode, LU1/LU2 source pointers, and a real observed or stated basis for
`EMERGING_USER_CONTEXT`. It does **not** independently inspect the external
primary documents or decide whether a source-declared qualification was sound.

If connected, `import_lead_user_context_evidence` validates the return against
the original, unchanged route. Outputs remain explicitly
`PROPOSED_HUMAN_REVIEW_REQUIRED`, with three separate meanings:

| Research output | Meaning | Authority |
|---|---|---|
| `x_observed_in_original_interviews=UNCHANGED` | Previous reported/observed x stays exactly as it was | No automatic revision |
| `emerging_x_from_lead_user_sources` | Source-reported or observed context for qualified-in-source advanced episodes | Source-declared, human inspection required |
| `hypothesized_transfer_x` | Possible future relevance to other users | Untested outside its original source scope |

Namespaced references such as `LUR:study_name:E3`,
`LUR:study_name:LU1`, and `LUR:study_name:LX001` remain
separate from interview `E###` and planning `R##` identities. The importer
returns a fingerprint of the *supplied* handoff, not proof of its authenticity.

### Never infer

- A qualified Lead User from a discovery signal alone.
- Population prevalence, adoption lift, willingness to pay, market size or
  propagation from advanced-user accounts.
- Direct fieldwork from an AI-only or public-web `DESK_RESEARCH` source.
- That even `SUPPORTED` transferability means observed mainstream behavior.
- That a research-local `ACCEPTED` frame or `SELECTED` mechanism authorizes
  a product goal, requirements or a shape.
- That simulated-person ratings become observed evidence.

Human review must compare original sources, trend support, LU1/LU2 qualification,
independence of research discovery branches, advanced analogs, contrary cases,
and transferability to the target market before using a finding for planning.
If the relevant current-behavior uncertainty remains unresolved, record it as
unresolved. Do not merge the return into the original checkpoint.

## 3. What the methods own

**Interview Assistant:** current decision episodes and gaps; triage; source
ownership; a separate proposed x extension. **Lead User Research:** trend and
qualification research; pyramiding; discovery branches; analogs; fieldwork
and evidence freeze; needs and transferability. **Planning Skills:** chooses
accepted y, requirements, candidate f(), Fit Check, and build authority.

A returned x extension is **an input to a human planning decision**, not
automatic product truth. It may justify a narrower study, a new research
question, stopping an unsupported hypothesis, or an explicit revision to
working assumptions.

Implementation: `simulation/context_bridge.py` and
`simulation/schemas/context-*.schema.json`. These are stateless read-only
adapters; they never fetch URLs from transcripts or handoffs.
