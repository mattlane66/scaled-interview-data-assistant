---
name: extend-context
description: Route consequential gaps in current x to traces, targeted fieldwork, or optional Lead User Research; preserve separate emerging-x and hypothesized-transfer evidence on return.
---

# Extend the evidence for x

Use this only when a **consequential** part of the current situation is missing, partial, or contradictory. More research is not always needed. Do not generalize from a few interviews or fill missing behavioral history with invented explanations.

First determine the exact **uncertainty**, its effect on the intended human decision, the relevant interview `D##` and `E###` references (or explicitly no interview corpus), and whether the missing fact is **TRACE_OBSERVABLE**, **PARTIALLY_OBSERVABLE**, **NOT_OBSERVABLE**, or **UNKNOWN**.

## Choose the smallest valid research move

- If the gap does not matter to a decision: **DEFER**.
- If reliable traces can answer it: **TRACE_RESEARCH**, using existing actual behavior/records before defaulting to interviews.
- If observability is not known: **CHECK_OBSERVABILITY**.
- If it is a consequential future-facing gap with **candidate** important trend, advanced-user conditions and high expected benefit: optionally route to [Lead User Research](https://github.com/mattlane66/planning-skills-for-agents-and-humans/tree/main/lead-user-research).
- Otherwise: **TARGETED_CURRENT_RESEARCH** (interview or observe ordinary users).

Lead User Research belongs to its own repo and protocol. Do not duplicate its methodology here or claim that the route ran its research. Its true qualification test requires both **LU1** (ahead of a relevant trend) and **LU2** (unusually high expected benefit); a prominent person, vivid workaround or discovery signal is not enough.

If connected, call `triage_context_uncertainty` with a complete `context_question` and optional `checkpoint_json`. The tool checks original E/D ownership; an unconnected skills-only plugin must describe the recommendation as a reasoned proposal, **not** as executed validation.

## Return handoff: three separate meanings

When the upstream research is completed, ask for the original research handoff, source-location manifest, bounded `LU##` episodes, LU1/LU2 qualification references and transferability judgments. If an MCP tool is connected, `import_lead_user_context_evidence` checks consistency with the original route.

Distinguish:
- **Observed current x:** unchanged original interview and trace evidence
- **Emerging x:** cited advanced-user conditions, *only within the observed/source-reported Lead User context*
- **Hypothesized mainstream x:** explicitly inferred future transfer, `SUPPORTED | PLAUSIBLE | LEAD_USER_BOUND | UNKNOWN` with rationale and limitations

Preserve each original ref as `LUR:<workspace>:E#`, `LUR:<workspace>:LU#`, and `LUR:<workspace>:LX###`. The upstream research may be `DESK_RESEARCH` even if carefully executed; AI-only evidence does not become human fieldwork. Avoid treating a research-local frame or SELECTED mechanism as an accepted product requirement or chosen shape.

**Neither source-located citations nor the MCP validator independently verify human qualification, causality, mainstream prevalence, propagation, or a product decision.** Return `PROPOSED_HUMAN_REVIEW_REQUIRED`; do not silently merge into x, M, accepted y, requirements, or `f()`.

See the [context bridge guide](https://github.com/mattlane66/scaled-interview-data-assistant/blob/main/docs/operations/context-evidence-extension.md).
