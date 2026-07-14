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
  --interviews data/interviews.json \
  --episodes data/episodes.json \
  --segments data/segments.json \
  --source-root data \
  --evidence data/evidence_bank.json \
  --codebook data/codebook.json \
  --mappings data/evidence_mappings.json \
  --report data/synthesis_report.md \
  --clusters 3 \
  --output-dir outputs
```

The pipeline:

1. verifies excerpts against local sources and validates registries, provenance, mappings, and code
   families;
2. builds decision-episode incidence matrices without dropping zero-code episodes;
3. calculates descriptive A↔B associations and support counts;
4. clusters decision episodes using Jaccard distance;
5. exports a versioned checkpoint;
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

## Input formats

See [data contracts](data-contracts.md). JSON and CSV are recommended. A Markdown input may contain
only one table; multi-table report templates are not machine-readable inputs.
