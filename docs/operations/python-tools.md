# Deterministic Python tooling

The Python layer validates and computes over analyst-reviewed artifacts. It does not call an LLM or
decide what interview evidence means.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run the included checks

```bash
python -m ruff check .
python -m pytest -q
```

CI runs both commands on Python 3.10 and 3.12.

## One-command deterministic workflow

After an analyst has reviewed the registries, evidence bank, codebook, and mappings:

```bash
python scripts/run_pipeline.py \
  --sources data/sources.json \
  --interviews data/interviews.json \
  --episodes data/episodes.json \
  --segments data/segments.json \
  --source-root data \
  --evidence data/evidence_bank.json \
  --codebook data/codebook.json \
  --mappings data/evidence_mappings.json \
  --links data/links.json \
  --report data/synthesis_report.md \
  --output-dir outputs
```

The pipeline:

1. verifies excerpts against local sources and validates source coverage, registries, provenance,
   mappings, reviewed A↔B links, and code families;
2. builds decision-episode incidence matrices without dropping zero-code episodes;
3. aggregates reviewed A↔B links and calculates secondary co-occurrence diagnostics;
4. selects an exploratory Jaccard grouping when supported;
5. exports and deeply validates a versioned checkpoint;
6. audits the report when one is supplied.

## Individual commands

```bash
python scripts/validate_registry.py --help
python scripts/build_matrices.py --help
python scripts/analyze_links.py --help
python scripts/cluster_interviews.py --help
python scripts/export_checkpoint.py --help
python scripts/import_checkpoint.py --help
python scripts/audit_report.py --help
```

The historical `cluster_interviews.py` filename remains for compatibility. It clusters `episode` by
default. Use `--unit-column interview` only when every interview contains exactly one bounded
decision episode.

Supply `--previous-assignments` during reclustering to preserve accepted `C##` IDs by membership
overlap. Always review the result; stable IDs do not make a cluster interpretation correct.

Clustering defaults to `--clusters auto`. Use `--clusters none` to skip it, `--clusters 1` to retain
one group, or another positive integer to request a candidate count. The output and checkpoint use
the actual number of distinct assignments, which can be lower than the request.

Checkpoint export and restore apply the JSON Schema plus cross-registry ownership and completeness
checks. Version 1.0 checkpoints are migrated additively; unknown source coverage and evidence types
remain explicitly `UNKNOWN`/`unknown`.

## Input formats

See [data contracts](data-contracts.md). JSON and CSV are recommended. A Markdown input may contain
only one table; multi-table report templates are not machine-readable inputs.
