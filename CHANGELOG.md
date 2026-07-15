# Changelog

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
