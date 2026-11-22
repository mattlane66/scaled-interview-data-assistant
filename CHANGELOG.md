# Changelog

## 1.4.0 — 2026-11-22

- Added human-reviewed, cross-episode Behavioral Mechanism Maps over source-located
  A→B links and exploratory JTBD clusters.
- Added analyst-coded aligning, counterexample, ambiguous, and unassessed cases,
  with evidence ownership, review gates, and participant-grain distinctions.
- Added rival mechanism hypotheses, disconfirming observations, human test proposals,
  and a read-only, PROPOSED x/y/M handoff to Planning Skills.
- Added stand-alone `mechanism_map_cli.py`, deterministic inventory/compilation,
  documentation, and adversarial regression tests; no LLM or source-registry changes.


## 1.3.0 — 2026-11-22

- Added evidence-first counterfactual product decision briefs using reviewed human A→B
  links, source references, proposed design changes, falsifiers and fallback designs.
- Added optional simulation-augmented briefs with synthetic hypotheses distinctly labeled.
- Added comparisons of alternative product interventions against a common evidence
  baseline, with no causal estimates or automatic ranking.
- Added `init --counterfactual`, `counterfactual`, and `compare` commands, JSON
  schemas, human-research safeguards, tests, and an end-to-end operating guide.
- Preserved original interview synthesis, simulation, SSR and holdout behavior.

## 1.2.1 — 2026-11-22

- Audited and strengthened links between an approved scenario, generated run,
  ordinal measurement, held-out comparison, and rendered report.
- Reject attaching unrelated validation artifacts even if their run IDs match.
- Require the checkpoint and scenario during SSR execution; reject changed measurement definitions.
- Require the exact approved human question in holdout evaluation and add adversarial regression tests.
- Clarify that predeclaration times and external model-generation provenance are not independently verified.


## 1.2.0 — 2026-11-22

- Added optional, read-only, checkpoint-bound behavioral simulation after reviewed JTBD synthesis.
- Added strict scenario and model-response schemas, approval checks, evidence provenance, and CLI.
- Added optional vector-based SSR measurement and guarded person-grouped holdout comparisons.
- Separated simulated reports, evidence grades, and prospective human validation from observations.
- Preserved original checkpoint and deterministic interview analysis without a model API dependency.


## 1.1.0 — 2026-07-15

- Added source-coverage and reviewed A↔B link registries with stable `SRC##` and `L###` IDs.
- Added speaker and evidence-type provenance to every evidence row.
- Made reviewed within-episode links primary and co-occurrence metrics secondary; added full 2×2
  counts and support-aware phi reporting.
- Added automatic, one-cluster, and no-clustering modes and record the actual assignment count.
- Added typed checkpoint schemas, deep referential validation, and additive version 1 migration.
- Validated cluster assignment ownership and completeness.
- Kept the Custom GPT operating prompt below the 8,000-character instruction limit.

## 1.0.0 — 2026-07-14

- Made decision episode the default analysis unit.
- Separated pre-switch baseline, hoped-for Point B, and observed Path X result.
- Added source-located evidence contracts and optional local excerpt verification.
- Hardened registry, mapping, alias, report, and cluster-ID validation.
- Replaced interview-level Ward clustering with episode-level average-linkage clustering on Jaccard
  distance.
- Added support-aware A↔B association output and explicit non-causal reporting rules.
- Added one-command deterministic execution plus checkpoint restore.
- Replaced and expanded examples with original synthetic data.
- Added privacy, prompt-injection, and human-review safeguards.
- Added adversarial tests and Python 3.10/3.12 CI.
