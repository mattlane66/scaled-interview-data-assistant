# Evaluating research agents on unfamiliar transcripts

**Scope:** An evaluation system for whether agents *actually perform* the four methods appropriately. The existing [19 routing scenarios](../../evals/routing-cases.json) exercise software decisions only; they are **not** blind human-judged agent runs or a scientific validation of the research methodologies.

## 1. Assemble a permissioned, genuinely held-out real corpus

Select source-accessible interviews or traces **not used to write the router, the skill instructions or the mattress canonical example**. Require explicit processing permission and minimum necessary personal data; public accessibility does not by itself grant redistribution rights. Preserve original source locators, speaker roles, context and outcome timing.

Cover:
- a real adoption or replacement decision with contrary testimony;
- non-adoption, delayed switching or a failed attempt;
- more than one real respondent with contrasting decisions;
- partial/incomplete transcripts and missing longitudinal outcomes;
- unsuitable inputs such as usability-task transcripts and future-intent-only surveys;
- cases where counterfactual or emerging-need questions require external evidence that the transcript cannot supply.

Randomize source order when appropriate, prevent leakage into model context, and keep references inaccessible to the research agent. No fabricated respondents. Maintain each case's provenance, scope, licensing and access controls.

## 2. Establish independent human adjudication

A research reviewer who did not generate the agent's answer should read the **entire permitted source**, identify valid bounded episodes, material evidence, relevant counterexamples, and unknowns, and write a case-level reference file. A second reviewer or disagreement-resolution pass is preferable for material claims. Human reference judgments are opinions supported by source receipts, **not automated ground truth**.

For each case record a decision question, required/allowed methods, exact allowed source IDs, decisive claims and omissions, competing hypotheses, approved/not-approved review boundaries, and when the answer must be a refusal or request for more data. Mark **HUMAN_REVIEWED** only after actual inspection, with verifiable reviewer provenance.

The included [mattress reference](../../evals/mattress-agent-reference.json) is **AI_AUDITED_NOT_HUMAN_REVIEWED**. It is a demonstration for the scoring interface, not an unseen evaluation.

## 3. Run agents without peeking at references

Use the same permitted source and decision question in real Codex and Claude Code sessions, recording client version, model/version, plugin/skill versions, tool availability, instruction context, exact model outputs and evaluator identity. Require agents to return a structured artifact: case ID, selected methods, material claims with excerpt IDs and epistemic kind, critical unknowns, any human-review/Lead User/predictive-validation claims, and the next evidence move.

When an upstream skill is unavailable, score an accurate explicit **SKILL_REQUIRED** handoff as honest scope handling. Do not give a pass for pretending that external research was run. Compare methods only on questions their prerequisites support.

### Deterministic structural checks

Run:

~~~bash
python scripts/evaluate_research_router.py
python scripts/score_agent_research.py --reference evals/mattress-agent-reference.json --artifact evals/mattress-agent-output-demo.json
~~~

The first checks router behavior on synthetic metadata; the second verifies source *membership*, method scope, unknowns and unsupported approval/validation claims in an **authored demonstration**. **Neither scores substantive transcript interpretation or proves unseen agent generalization.** For actual studies, pass their own permissioned, independent reference and saved agent output files.

### Human interpretation rubric

Independent reviewers score each dimension **0–4** with specific excerpt-level explanations:

| Dimension | What the reviewer examines |
| --- | --- |
| Source accuracy | Does each cited excerpt actually support the claim, with speaker, context and contradictions intact? |
| Chronology | Did the agent correctly distinguish pre-switch baseline, trigger, adoption, later use and outcome? |
| Method fidelity | Was the correct full protocol used, with its eligibility, qualification and review gates? |
| Contradictions | Are negative, competing and missing cases visible rather than edited away? |
| Decision usefulness | Does the output improve the stated decision with an honest next source/test instead of unsupported solution selection? |

A reviewer can provide a JSON rubric with case ID, reviewer and integer score for each dimension to **score_agent_research.py** as --human-review. The scorer labels that submission **REVIEW_SUBMITTED_INDEPENDENCE_NOT_VERIFIED**, not verified blind adjudication. An actual independent evaluation needs separate reviewer and provenance controls.

## 4. Failure classification and source-specific repair

For every material failure, determine the smallest cause:
- **EVIDENCE_NOT_AVAILABLE:** missing transcripts, actual behavior, source rights, longitudinal results, additional people or held-out human outcomes. Obtain evidence rather than changing prompts.
- **METHOD_MISROUTED:** research question or precondition classification failed. Fix router, eligibility test or agent instruction.
- **TOOL_OR_SKILL_MISSING:** external Lead User or Behavioral Simulation skill not available. Implement/install a versioned handoff; do not copy or claim execution.
- **PROTOCOL_UNDERSPECIFIED:** identify a specific absent/ambiguous method operation despite a complete source. Re-read the governing original research, extract the minimal operational procedure with its assumptions and limits, and add a failed-then-passing regression case.
- **AGENT_EXECUTION_ERROR:** source and protocol were sufficient; agent skipped or misapplied them. Improve scaffolding, bounded context or tool checks.
- **RESEARCH_CONTRADICTION:** a paper's assumptions conflict with the target case. Keep the incompatibility visible; do not silently retrofit a method.

When making a paper-derived repair, link *exactly* the source section and relevant primary research, note where the skill's adaptation is your own, and establish whether it changes the evidence requirement or only execution. Never broaden methods merely to eliminate a failure.

## 5. Acceptance and release reporting

The initial release must pass deterministic router scenarios, file/schema and security checks, plus a real local MCP client smoke test in CI. For a **claim of reliable agent research execution**, additionally require actual Codex and Claude sessions against unfamiliar, permissioned transcripts with independently adjudicated source-level interpretations, including at least one negative/inapplicable case per method; document error rates and residual contradictions.

**Current status:** deterministic router and structural artifact scorer implemented. A [source-located two-interview self-pilot](../../evals/real-source-pilot/README.md) has exercised provisional A→B on real public interviews and corrected a formal-mechanism eligibility gap, but it is not blind human adjudication or a native Codex/Claude run; external blind human evaluations, native Codex and Claude CLI invocation and empirical prediction/calibration are **NOT RUN** unless a separate dated result record establishes otherwise.

Never equate passing CI or correct reference IDs with complete, correct interpretation of unfamiliar source material.
