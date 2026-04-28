# Python Tooling

This repo is primarily a method and prompt package. The Python scripts are a thin deterministic layer for the parts of qualitative synthesis that should not be done mentally by an LLM.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Smoke test the tooling

The repo includes a tiny fixture dataset under `tests/fixtures/` and an end-to-end pytest that validates the full deterministic workflow without using real research data.

Run:

```bash
pytest -q
```

The smoke test covers:

- registry validation
- incidence matrix generation
- A<->B link analysis
- Ward clustering
- checkpoint export
- synthesis report audit

## Expected working files

Put analyst/model-produced tables in `outputs/` as CSV, Excel, JSON, JSONL, YAML, or Markdown tables.

Recommended files:

```text
outputs/evidence_bank.csv
outputs/codebook.csv
outputs/evidence_mappings.csv
outputs/clusters.csv
outputs/alias_map.csv
outputs/synthesis_report.md
```

## Validate registry integrity

```bash
python scripts/validate_registry.py \
  --evidence outputs/evidence_bank.csv \
  --codebook outputs/codebook.csv \
  --mappings outputs/evidence_mappings.csv \
  --aliases outputs/alias_map.csv
```

## Build incidence matrices

```bash
python scripts/build_matrices.py \
  --mappings outputs/evidence_mappings.csv \
  --output-dir outputs/matrices
```

Writes:

```text
outputs/matrices/interview_x_a_code.csv
outputs/matrices/interview_x_b_code.csv
outputs/matrices/interview_x_combined_code.csv
```

## Compute A<->B link strengths

```bash
python scripts/analyze_links.py \
  --mappings outputs/evidence_mappings.csv \
  --codebook outputs/codebook.csv \
  --output outputs/matrices/a_to_b_link_strengths.csv
```

This computes Jaccard co-occurrence across interviews, phi when `N >= 5`, and optional TF-IDF cosine similarity between code definitions.

## Cluster interviews

```bash
python scripts/cluster_interviews.py \
  --matrix outputs/matrices/interview_x_combined_code.csv \
  --clusters 3
```

Uses Ward hierarchical clustering on combined A+B incidence.

## Export a checkpoint

```bash
python scripts/export_checkpoint.py \
  --evidence outputs/evidence_bank.csv \
  --codebook outputs/codebook.csv \
  --mappings outputs/evidence_mappings.csv \
  --clusters outputs/clusters.csv \
  --aliases outputs/alias_map.csv \
  --output CHECKPOINT.json
```

## Audit a synthesis report

```bash
python scripts/audit_report.py \
  --report outputs/synthesis_report.md \
  --evidence outputs/evidence_bank.csv \
  --codebook outputs/codebook.csv \
  --clusters outputs/clusters.csv \
  --n-interviews 5
```

The audit checks that referenced evidence IDs exist, `VERIFIED` claims cite evidence IDs, code/cluster references are known when supplied, and reports declare computation status.
